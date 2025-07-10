"""
Base Squad Agent - Common functionality for all AutoSquad agents
"""

from typing import Any, Dict, List, Optional, Sequence

from autogen_agentchat.agents import ConversableAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import ChatMessage
from autogen_core import CancellationToken
from autogen_ext.models import ChatCompletionClient


class BaseSquadAgent(ConversableAgent):
    """Base class for all AutoSquad agents with project awareness."""
    
    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
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
        
        # Initialize the ConversableAgent
        super().__init__(
            name=name,
            model_client=model_client,
            system_message=system_message,
            tools=tools or []
        )
    
    def get_enhanced_system_message(self, base_template: str) -> str:
        """Enhance the system message with project context."""
        workspace_path = self.project_context.get("workspace_path", "")
        current_files = self.project_context.get("current_files", [])
        project_prompt = self.project_context.get("prompt", "")
        
        return base_template.format(
            project_prompt=project_prompt,
            workspace_path=workspace_path,
            current_files=", ".join(current_files) if current_files else "No files yet"
        )
    
    async def on_messages(
        self,
        messages: Sequence[ChatMessage],
        cancellation_token: CancellationToken
    ) -> Response:
        """Handle incoming messages with project context awareness."""
        
        # Log the agent action
        if hasattr(self.project_manager, 'logs'):
            self.project_manager.logs.log_agent_action(
                agent_name=self.name,
                action="received_message",
                details={
                    "message_count": len(messages),
                    "last_sender": messages[-1].source if messages else None
                }
            )
        
        # Call the parent implementation
        response = await super().on_messages(messages, cancellation_token)
        
        # Log the response
        if hasattr(self.project_manager, 'logs'):
            self.project_manager.logs.log_agent_action(
                agent_name=self.name,
                action="sent_response",
                details={
                    "response_type": type(response).__name__,
                    "chat_message": response.chat_message.content if response.chat_message else None
                }
            )
        
        return response
    
    def get_workspace_files(self) -> List[str]:
        """Get list of files in the workspace."""
        return self.project_manager.workspace.list_files()
    
    def read_workspace_file(self, file_path: str) -> str:
        """Read a file from the workspace."""
        return self.project_manager.workspace.read_file(file_path)
    
    def write_workspace_file(self, file_path: str, content: str) -> None:
        """Write a file to the workspace."""
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
    
    def delete_workspace_file(self, file_path: str) -> None:
        """Delete a file from the workspace."""
        self.project_manager.workspace.delete_file(file_path)
        
        # Log the file operation
        if hasattr(self.project_manager, 'logs'):
            self.project_manager.logs.log_agent_action(
                agent_name=self.name,
                action="deleted_file",
                details={"file_path": file_path}
            )
    
    def create_workspace_directory(self, dir_path: str) -> None:
        """Create a directory in the workspace."""
        self.project_manager.workspace.create_directory(dir_path)
        
        # Log the directory creation
        if hasattr(self.project_manager, 'logs'):
            self.project_manager.logs.log_agent_action(
                agent_name=self.name,
                action="created_directory",
                details={"dir_path": dir_path}
            )
    
    def get_project_prompt(self) -> str:
        """Get the original project prompt."""
        return self.project_context.get("prompt", "")
    
    def get_workspace_summary(self) -> str:
        """Get a summary of the current workspace."""
        return self.project_manager.get_workspace_summary()
    
    def announce_action(self, action: str, details: str = "") -> str:
        """Create a standardized announcement for agent actions."""
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
            "Action logging and tracking"
        ] 