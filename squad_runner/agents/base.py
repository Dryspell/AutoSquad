"""
Base Squad Agent - Common functionality for all AutoSquad agents
Enhanced with patterns from well-funded AI companies
"""

from typing import Any, Dict, List, Optional, Sequence, Callable

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import TextMessage, ToolCallSummaryMessage
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool

from ..tools import create_workspace_tools
from .enhanced_prompts import get_enhanced_agent_prompt


class BaseSquadAgent(AssistantAgent):
    """Base class for all AutoSquad agents with project awareness."""
    
    def __init__(
        self,
        name: str,
        model_client: OpenAIChatCompletionClient,
        project_context: Dict[str, Any],
        agent_settings: Dict[str, Any],
        project_manager,
        system_message: Optional[str] = None,
        tools: Optional[List] = None,
        use_enhanced_prompts: bool = True
    ):
        self.project_context = project_context
        self.agent_settings = agent_settings
        self.project_manager = project_manager
        self.role_type = self.__class__.__name__.replace("Agent", "").lower()
        
        # Initialize workspace tools (will be updated with progress callback later)
        self.workspace_tools = create_workspace_tools(project_manager)
        
        # Create function tools for AutoGen
        function_tools = self._create_function_tools()
        
        # Progress tracking callback (will be set by orchestrator)
        self.progress_callback = None
        
        # Generate enhanced system message if enabled and no custom message provided
        if use_enhanced_prompts and system_message is None:
            enhanced_context = {
                'project_prompt': project_context.get('prompt', ''),
                'workspace_path': project_context.get('workspace_path', ''),
                'current_files': project_context.get('current_files', [])
            }
            system_message = get_enhanced_agent_prompt(self.role_type, enhanced_context)
        elif system_message is None:
            # Fallback to basic system message
            system_message = f"You are a {self.role_type} agent in the AutoSquad development framework."
        
        # Initialize the AssistantAgent with enhanced system message and tools
        # Using AutoGen 0.6.4 parameter names
        super().__init__(
            name=name,
            model_client=model_client,
            system_message=system_message,
            tools=function_tools or []
        )
    
    def set_progress_callback(self, callback: Optional[Callable]):
        """Set the progress callback for tracking actions."""
        self.progress_callback = callback
        # Update workspace tools with the callback
        if hasattr(self.workspace_tools, 'progress_callback'):
            self.workspace_tools.progress_callback = callback
            if callback and hasattr(self, 'verbose') and getattr(self, 'verbose', False):
                print(f"[DEBUG] Progress callback set for workspace tools of {getattr(self, 'name', 'agent')}")
    
    def _notify_action_started(self, action: str):
        """Notify that an action has started."""
        if self.progress_callback:
            self.progress_callback("agent_action_started", action)
    
    def _notify_action_completed(self, result: str = ""):
        """Notify that an action has completed."""
        if self.progress_callback:
            self.progress_callback("agent_action_completed", result)
    
    def _notify_file_operation(self, operation: str, file_path: str):
        """Notify about a file operation."""
        if self.progress_callback:
            self.progress_callback("file_operation", operation, file_path)
    
    def _create_function_tools(self) -> List[FunctionTool]:
        """Create AutoGen function tools from workspace tools."""
        function_tools = []
        
        # Get function definitions from workspace tools
        function_definitions = self.workspace_tools.get_function_definitions()
        function_map = self.workspace_tools.get_function_map()
        
        for func_def in function_definitions:
            func_name = func_def["function"]["name"]
            
            if func_name in function_map:
                # Use the original function directly to avoid signature issues
                original_func = function_map[func_name]
                
                # Create AutoGen function tool with original function
                function_tool = FunctionTool(
                    func=original_func,
                    description=func_def["function"]["description"]
                )
                
                function_tools.append(function_tool)
        
        return function_tools
    
    def get_enhanced_system_message(self, project_context: Dict[str, Any] = None) -> str:
        """Get enhanced system message using AI company patterns."""
        # Use provided project_context or fall back to instance attribute
        context = project_context or self.project_context
        
        enhanced_context = {
            'project_prompt': context.get('prompt', ''),
            'workspace_path': context.get('workspace_path', ''),
            'current_files': context.get('current_files', [])
        }
        
        return get_enhanced_agent_prompt(self.role_type, enhanced_context)
    
    def update_project_context(self, new_context: Dict[str, Any]):
        """Update project context and regenerate enhanced system message if needed."""
        self.project_context.update(new_context)
        
        # Update current files list from workspace if available
        if hasattr(self, 'project_manager') and self.project_manager:
            try:
                current_files = self.get_workspace_files()
                self.project_context['current_files'] = current_files
            except Exception:
                pass  # Ignore errors if workspace is not available
    
    # Note: Message handling will be managed by AutoGen 0.6.4's AssistantAgent
    # We'll focus on utility methods for project management
    
    def get_workspace_files(self) -> List[str]:
        """Get list of files in the workspace."""
        return self.project_manager.workspace.list_files()
    
    def read_workspace_file(self, file_path: str) -> str:
        """Read a file from the workspace."""
        self._notify_action_started(f"Reading {file_path}")
        try:
            content = self.project_manager.workspace.read_file(file_path)
            self._notify_action_completed(f"Read {file_path}")
            return content
        except Exception as e:
            self._notify_action_completed(f"Failed to read {file_path}: {str(e)}")
            raise
    
    def write_workspace_file(self, file_path: str, content: str) -> None:
        """Write a file to the workspace."""
        self._notify_action_started(f"Writing {file_path}")
        try:
            self.project_manager.workspace.write_file(file_path, content)
            
            # Log the file operation
            if hasattr(self.project_manager, 'logs'):
                self.project_manager.logs.log_agent_action(
                    agent_name=self.name,
                    action="wrote_file",
                    details={
                        "file_path": file_path,
                        "file_size": len(content)
                    }
                )
            
            self._notify_file_operation("create", file_path)
            self._notify_action_completed(f"Created {file_path}")
            
        except Exception as e:
            self._notify_action_completed(f"Failed to write {file_path}: {str(e)}")
            raise
        
    def delete_workspace_file(self, file_path: str) -> None:
        """Delete a file from the workspace."""
        self._notify_action_started(f"Deleting {file_path}")
        try:
            self.project_manager.workspace.delete_file(file_path)
            
            # Log the file operation
            if hasattr(self.project_manager, 'logs'):
                self.project_manager.logs.log_agent_action(
                    agent_name=self.name,
                    action="deleted_file",
                    details={"file_path": file_path}
                )
            
            self._notify_action_completed(f"Deleted {file_path}")
            
        except Exception as e:
            self._notify_action_completed(f"Failed to delete {file_path}: {str(e)}")
            raise
    
    def create_workspace_directory(self, dir_path: str) -> None:
        """Create a directory in the workspace."""
        self._notify_action_started(f"Creating directory {dir_path}")
        try:
            self.project_manager.workspace.create_directory(dir_path)
            
            # Log the directory creation
            if hasattr(self.project_manager, 'logs'):
                self.project_manager.logs.log_agent_action(
                    agent_name=self.name,
                    action="created_directory",
                    details={"dir_path": dir_path}
                )
            
            self._notify_file_operation("mkdir", dir_path)
            self._notify_action_completed(f"Created directory {dir_path}")
            
        except Exception as e:
            self._notify_action_completed(f"Failed to create directory {dir_path}: {str(e)}")
            raise
    
    def get_project_prompt(self) -> str:
        """Get the original project prompt."""
        return self.project_context.get("prompt", "")
    
    def get_workspace_summary(self) -> str:
        """Get a summary of the current workspace."""
        return self.project_manager.get_workspace_summary()
    
    def announce_action(self, action: str, details: str = "") -> str:
        """Create a standardized announcement for agent actions."""
        self._notify_action_started(action)
        prefix = f"🤖 **{self.name}** ({self.role_type.upper()})"
        if details:
            return f"{prefix}: {action}\n\n{details}"
        else:
            return f"{prefix}: {action}"
    
    def format_code_block(self, code: str, language: str = "") -> str:
        """Format code in a markdown code block."""
        return f"```{language}\n{code}\n```"
    
    def format_file_operation(self, operation: str, file_path: str, content: str = "") -> str:
        """Format a file operation announcement."""
        if operation == "created" and content:
            return self.announce_action(
                f"Created file `{file_path}`",
                self.format_code_block(content, self._get_file_language(file_path))
            )
        elif operation == "updated" and content:
            return self.announce_action(
                f"Updated file `{file_path}`",
                self.format_code_block(content, self._get_file_language(file_path))
            )
        elif operation == "deleted":
            return self.announce_action(f"Deleted file `{file_path}`")
        else:
            return self.announce_action(f"{operation.capitalize()} file `{file_path}`")
    
    def _get_file_language(self, file_path: str) -> str:
        """Get the language identifier for syntax highlighting."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".html": "html",
            ".css": "css",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".sh": "bash",
            ".sql": "sql"
        }
        
        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang
        
        return ""
    
    def get_agent_capabilities(self) -> List[str]:
        """Get a list of this agent's capabilities - to be overridden by subclasses."""
        return [
            "Project context awareness",
            "Workspace file operations",
            "Action logging and tracking",
            "Function calling for file management"
        ] 