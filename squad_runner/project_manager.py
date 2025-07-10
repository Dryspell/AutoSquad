"""
Project management for AutoSquad - handles project lifecycle and workspace management
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProjectWorkspace:
    """Manages the project workspace directory and file operations."""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.workspace_path.mkdir(exist_ok=True)
    
    def list_files(self) -> List[str]:
        """List all files in the workspace."""
        files = []
        for file_path in self.workspace_path.rglob("*"):
            if file_path.is_file():
                files.append(str(file_path.relative_to(self.workspace_path)))
        return sorted(files)
    
    def read_file(self, file_path: str) -> str:
        """Read a file from the workspace."""
        full_path = self.workspace_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File {file_path} not found in workspace")
        
        try:
            return full_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Handle binary files
            return f"<Binary file: {file_path}>"
    
    def write_file(self, file_path: str, content: str) -> None:
        """Write a file to the workspace."""
        full_path = self.workspace_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
    
    def delete_file(self, file_path: str) -> None:
        """Delete a file from the workspace."""
        full_path = self.workspace_path / file_path
        if full_path.exists():
            full_path.unlink()
    
    def create_directory(self, dir_path: str) -> None:
        """Create a directory in the workspace."""
        full_path = self.workspace_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file."""
        full_path = self.workspace_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
        stat = full_path.stat()
        return {
            "path": file_path,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_directory": full_path.is_dir()
        }
    
    def backup_workspace(self, backup_dir: Path) -> None:
        """Create a backup of the workspace."""
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"workspace_backup_{timestamp}"
        shutil.copytree(self.workspace_path, backup_path)


class LogManager:
    """Manages conversation logs and project history."""
    
    def __init__(self, logs_path: Path):
        self.logs_path = logs_path
        self.logs_path.mkdir(exist_ok=True)
        self.current_session = None
    
    def start_session(self, session_id: str) -> None:
        """Start a new logging session."""
        self.current_session = session_id
        session_dir = self.logs_path / session_id
        session_dir.mkdir(exist_ok=True)
    
    def log_conversation(self, round_num: int, messages: List[Dict[str, Any]]) -> None:
        """Log conversation messages for a round."""
        if not self.current_session:
            raise RuntimeError("No active logging session")
        
        log_file = self.logs_path / self.current_session / f"round_{round_num:02d}_conversation.json"
        
        log_data = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "messages": messages
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def log_workspace_state(self, round_num: int, workspace_files: List[str]) -> None:
        """Log the workspace state after a round."""
        if not self.current_session:
            raise RuntimeError("No active logging session")
        
        log_file = self.logs_path / self.current_session / f"round_{round_num:02d}_workspace.json"
        
        log_data = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "files": workspace_files
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def log_agent_action(self, agent_name: str, action: str, details: Dict[str, Any]) -> None:
        """Log an individual agent action."""
        if not self.current_session:
            return  # Silently skip if no session
        
        log_file = self.logs_path / self.current_session / "agent_actions.jsonl"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "details": details
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of a logging session."""
        session_dir = self.logs_path / session_id
        if not session_dir.exists():
            raise FileNotFoundError(f"Session {session_id} not found")
        
        # Count files and get basic stats
        conversation_files = list(session_dir.glob("*_conversation.json"))
        workspace_files = list(session_dir.glob("*_workspace.json"))
        
        return {
            "session_id": session_id,
            "rounds": len(conversation_files),
            "created": datetime.fromtimestamp(session_dir.stat().st_ctime).isoformat(),
            "conversation_logs": len(conversation_files),
            "workspace_snapshots": len(workspace_files)
        }


class ProjectManager:
    """Main project manager that coordinates workspace and logging."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.workspace = ProjectWorkspace(project_path / "workspace")
        self.logs = LogManager(project_path / "logs")
        self.prompt_file = project_path / "prompt.txt"
        self.project_prompt = None
    
    async def initialize(self) -> None:
        """Initialize the project and load the prompt."""
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project directory {self.project_path} does not exist")
        
        if not self.prompt_file.exists():
            raise FileNotFoundError(f"Project prompt file {self.prompt_file} does not exist")
        
        # Load the project prompt
        self.project_prompt = self.prompt_file.read_text().strip()
        
        # Start a new logging session
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs.start_session(session_id)
        
        # Log project initialization
        self.logs.log_agent_action(
            "ProjectManager",
            "project_initialized",
            {
                "project_path": str(self.project_path),
                "prompt": self.project_prompt,
                "workspace_files": self.workspace.list_files()
            }
        )
    
    def get_project_context(self) -> Dict[str, Any]:
        """Get the current project context for agents."""
        return {
            "prompt": self.project_prompt,
            "workspace_path": str(self.workspace.workspace_path),
            "current_files": self.workspace.list_files(),
            "project_path": str(self.project_path)
        }
    
    def get_workspace_summary(self) -> str:
        """Get a human-readable summary of the workspace."""
        files = self.workspace.list_files()
        if not files:
            return "Workspace is empty."
        
        summary = f"Workspace contains {len(files)} files:\n"
        for file_path in files:
            try:
                info = self.workspace.get_file_info(file_path)
                summary += f"  - {file_path} ({info['size']} bytes)\n"
            except Exception:
                summary += f"  - {file_path}\n"
        
        return summary
    
    async def save_round_state(self, round_num: int, conversation_messages: List[Dict[str, Any]]) -> None:
        """Save the state after a development round."""
        # Log conversation
        self.logs.log_conversation(round_num, conversation_messages)
        
        # Log workspace state
        self.logs.log_workspace_state(round_num, self.workspace.list_files())
        
        # Create workspace backup
        backup_dir = self.project_path / "backups"
        self.workspace.backup_workspace(backup_dir)
    
    def create_project_summary(self) -> Dict[str, Any]:
        """Create a final project summary."""
        return {
            "project_path": str(self.project_path),
            "prompt": self.project_prompt,
            "workspace_summary": self.get_workspace_summary(),
            "files_created": self.workspace.list_files(),
            "session_summary": self.logs.get_session_summary(self.logs.current_session) if self.logs.current_session else None
        }
    
    def export_project(self, export_path: Path) -> None:
        """Export the project to a new location."""
        export_path.mkdir(parents=True, exist_ok=True)
        
        # Copy workspace
        shutil.copytree(
            self.workspace.workspace_path,
            export_path / "workspace",
            dirs_exist_ok=True
        )
        
        # Copy prompt
        shutil.copy2(self.prompt_file, export_path / "prompt.txt")
        
        # Copy logs
        shutil.copytree(
            self.logs.logs_path,
            export_path / "logs",
            dirs_exist_ok=True
        )
        
        # Create summary
        summary = self.create_project_summary()
        with open(export_path / "project_summary.json", 'w') as f:
            json.dump(summary, f, indent=2) 