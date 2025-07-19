"""
Tool definitions for AutoSquad agents - enables function calling for file operations
"""

from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import json


class WorkspaceTools:
    """Function calling tools for workspace file operations."""
    
    def __init__(self, project_manager, progress_callback=None):
        self.project_manager = project_manager
        self.progress_callback = progress_callback
        
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI function definitions for workspace tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Create or update a file in the project workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file relative to workspace root (e.g., 'main.py', 'src/utils.py')"
                            },
                            "content": {
                                "type": "string", 
                                "description": "Complete file content to write"
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional description of what this file does"
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file from the workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file relative to workspace root"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List all files currently in the workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_directory",
                    "description": "Create a directory in the workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {
                                "type": "string",
                                "description": "Path to the directory relative to workspace root"
                            }
                        },
                        "required": ["dir_path"]
                    }
                }
            }
        ]
    
    def get_function_map(self) -> Dict[str, Callable]:
        """Get mapping of function names to actual implementation functions."""
        return {
            "write_file": self._write_file,
            "read_file": self._read_file,
            "list_files": self._list_files,
            "create_directory": self._create_directory
        }
    
    def _write_file(self, file_path: str, content: str, description: str = "") -> str:
        """Implementation for write_file function."""
        try:
            # Notify progress callback if available
            if self.progress_callback:
                self.progress_callback("agent_action_started", f"Writing file {file_path}")
                self.progress_callback("file_operation", "create", file_path)
            
            # Write the file
            self.project_manager.workspace.write_file(file_path, content)
            
            # Log the action
            self.project_manager.logs.log_agent_action(
                agent_name="WorkspaceTools",
                action="wrote_file",
                details={
                    "file_path": file_path,
                    "file_size": len(content),
                    "description": description
                }
            )
            
            # Notify completion
            if self.progress_callback:
                self.progress_callback("agent_action_completed", f"Created {file_path}")
            
            return f"✅ Successfully created/updated file: {file_path}"
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback("agent_action_completed", f"Failed to write {file_path}: {str(e)}")
            error_msg = f"❌ Error writing file {file_path}: {str(e)}"
            return error_msg
    
    def _read_file(self, file_path: str) -> str:
        """Implementation for read_file function."""
        try:
            content = self.project_manager.workspace.read_file(file_path)
            return f"📄 Contents of {file_path}:\n\n{content}"
        except FileNotFoundError:
            return f"❌ File not found: {file_path}"
        except Exception as e:
            return f"❌ Error reading file {file_path}: {str(e)}"
    
    def _list_files(self) -> str:
        """Implementation for list_files function."""
        try:
            files = self.project_manager.workspace.list_files()
            if not files:
                return "📁 Workspace is currently empty"
            
            file_list = "\n".join(f"  - {file}" for file in files)
            return f"📁 Current workspace files:\n{file_list}"
        except Exception as e:
            return f"❌ Error listing files: {str(e)}"
    
    def _create_directory(self, dir_path: str) -> str:
        """Implementation for create_directory function."""
        try:
            # Notify progress callback if available
            if self.progress_callback:
                self.progress_callback("agent_action_started", f"Creating directory {dir_path}")
                self.progress_callback("file_operation", "mkdir", dir_path)
            
            self.project_manager.workspace.create_directory(dir_path)
            
            # Log the action
            self.project_manager.logs.log_agent_action(
                agent_name="WorkspaceTools",
                action="created_directory", 
                details={"dir_path": dir_path}
            )
            
            # Notify completion
            if self.progress_callback:
                self.progress_callback("agent_action_completed", f"Created directory {dir_path}")
            
            return f"✅ Successfully created directory: {dir_path}"
        except Exception as e:
            if self.progress_callback:
                self.progress_callback("agent_action_completed", f"Failed to create {dir_path}: {str(e)}")
            return f"❌ Error creating directory {dir_path}: {str(e)}"


def create_workspace_tools(project_manager, progress_callback=None) -> WorkspaceTools:
    """Factory function to create workspace tools."""
    return WorkspaceTools(project_manager, progress_callback) 