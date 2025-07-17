"""
Base Squad Agent - Common functionality for all AutoSquad agents
"""

from typing import Any, Dict, List, Optional, Sequence, Callable

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import TextMessage, ToolCallSummaryMessage
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool

from ..tools import create_workspace_tools


class BaseSquadAgent(AssistantAgent):
    """Base class for all AutoSquad agents with project awareness."""
    
    def __init__(
        self,
        name: str,
        model_client: OpenAIChatCompletionClient,
        project_context: Dict[str, Any],
        agent_settings: Dict[str, Any],
        project_manager,
        system_message: str,
        tools: Optional[List] = None
    ):
        self.project_context = project_context
        self.agent_settings = agent_settings
        self.project_manager = project_manager
        self.role_type = self.__class__.__name__.replace("Agent", "").lower()
        
        # Initialize workspace tools
        self.workspace_tools = create_workspace_tools(project_manager)
        
        # Create function tools for AutoGen
        function_tools = self._create_function_tools()
        
        # Progress tracking callback (will be set by orchestrator)
        self.progress_callback = None
        
        # Initialize the AssistantAgent with tools
        super().__init__(
            name=name,
            model_client=model_client,
            system_message=system_message,
            tools=function_tools
        )
    
    def set_progress_callback(self, callback: Optional[Callable]):
        """Set the progress callback for tracking actions."""
        self.progress_callback = callback
    
    def _notify_action_started(self, action: str):
        """Notify that an action has started."""
        if self.progress_callback:
            self.progress_callback("agent_action_started", self.name, action)
    
    def _notify_action_completed(self, result: str = ""):
        """Notify that an action has completed."""
        if self.progress_callback:
            self.progress_callback("agent_action_completed", self.name, result)
    
    def _notify_file_operation(self, operation: str, file_path: str):
        """Notify about a file operation."""
        if self.progress_callback:
            self.progress_callback("file_operation", self.name, operation, file_path)
    
    def _create_function_tools(self) -> List[FunctionTool]:
        """Create AutoGen function tools from workspace tools."""
        function_tools = []
        
        # Get function definitions from workspace tools
        function_definitions = self.workspace_tools.get_function_definitions()
        function_map = self.workspace_tools.get_function_map()
        
        for func_def in function_definitions:
            func_name = func_def["function"]["name"]
            
            if func_name in function_map:
                # Create enhanced function that includes progress tracking
                original_func = function_map[func_name]
                
                def create_tracked_function(original, name):
                    def tracked_function(*args, **kwargs):
                        # Notify action started
                        self._notify_action_started(f"Executing {name}")
                        
                        try:
                            result = original(*args, **kwargs)
                            
                            # Track file operations
                            if name == "write_file" and len(args) >= 1:
                                self._notify_file_operation("create", args[0])
                            elif name == "create_directory" and len(args) >= 1:
                                self._notify_file_operation("mkdir", args[0])
                            
                            # Notify completion
                            self._notify_action_completed(f"Completed {name}")
                            return result
                            
                        except Exception as e:
                            self._notify_action_completed(f"Failed {name}: {str(e)}")
                            raise
                    
                    return tracked_function
                
                tracked_func = create_tracked_function(original_func, func_name)
                
                # Create AutoGen FunctionTool
                function_tool = FunctionTool(
                    name=func_name,
                    description=func_def["function"]["description"],
                    parameters=func_def["function"]["parameters"],
                    func=tracked_func
                )
                
                function_tools.append(function_tool)
        
        return function_tools
    
    def get_enhanced_system_message(self, base_template: str, project_context: Dict[str, Any] = None) -> str:
        """Enhance the system message with project context."""
        # Use provided project_context or fall back to instance attribute
        context = project_context or self.project_context
        workspace_path = context.get("workspace_path", "")
        current_files = context.get("current_files", [])
        project_prompt = context.get("prompt", "")
        
        return base_template.format(
            project_prompt=project_prompt,
            workspace_path=workspace_path,
            current_files=", ".join(current_files) if current_files else "No files yet"
        )
    
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