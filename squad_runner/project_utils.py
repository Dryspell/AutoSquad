"""
Project management utilities for AutoSquad CLI.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

console = Console()


class ProjectInfo:
    """Information about an AutoSquad project."""
    
    def __init__(self, project_path: Path):
        self.path = project_path
        self.name = project_path.name
        self.prompt_file = project_path / "prompt.txt"
        self.workspace_dir = project_path / "workspace"
        self.logs_dir = project_path / "logs"
        self.metadata_file = project_path / ".autosquad_metadata.json"
    
    @property
    def exists(self) -> bool:
        """Check if this appears to be a valid AutoSquad project."""
        return self.path.exists() and self.path.is_dir() and self.prompt_file.exists()
    
    @property
    def prompt(self) -> str:
        """Get the project prompt."""
        if self.prompt_file.exists():
            return self.prompt_file.read_text(encoding='utf-8').strip()
        return ""
    
    @property
    def has_workspace(self) -> bool:
        """Check if workspace directory exists and has files."""
        return self.workspace_dir.exists() and any(self.workspace_dir.iterdir())
    
    @property
    def has_logs(self) -> bool:
        """Check if logs directory exists and has files."""
        return self.logs_dir.exists() and any(self.logs_dir.iterdir())
    
    @property
    def workspace_file_count(self) -> int:
        """Count files in workspace."""
        if not self.workspace_dir.exists():
            return 0
        return len([f for f in self.workspace_dir.rglob("*") if f.is_file()])
    
    @property
    def log_file_count(self) -> int:
        """Count files in logs."""
        if not self.logs_dir.exists():
            return 0
        return len([f for f in self.logs_dir.rglob("*") if f.is_file()])
    
    @property
    def last_modified(self) -> Optional[datetime]:
        """Get last modification time of the project."""
        if not self.path.exists():
            return None
        
        latest_time = None
        for file_path in [self.prompt_file, self.workspace_dir, self.logs_dir]:
            if file_path.exists():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if latest_time is None or file_time > latest_time:
                    latest_time = file_time
        
        return latest_time
    
    @property
    def total_size(self) -> int:
        """Get total size of project in bytes."""
        total = 0
        if self.path.exists():
            for file_path in self.path.rglob("*"):
                if file_path.is_file():
                    try:
                        total += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        pass  # Skip files that can't be accessed
        return total
    
    def get_metadata(self) -> Dict:
        """Get project metadata from .autosquad_metadata.json if it exists."""
        if self.metadata_file.exists():
            try:
                return json.loads(self.metadata_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {}
        return {}
    
    def save_metadata(self, metadata: Dict) -> None:
        """Save project metadata to .autosquad_metadata.json."""
        try:
            self.metadata_file.write_text(
                json.dumps(metadata, indent=2, default=str),
                encoding='utf-8'
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save metadata: {e}[/yellow]")


def find_projects(base_dir: Path = None) -> List[ProjectInfo]:
    """Find all AutoSquad projects in the given directory (or projects/ by default)."""
    if base_dir is None:
        base_dir = Path("projects")
    
    if not base_dir.exists():
        return []
    
    projects = []
    for item in base_dir.iterdir():
        if item.is_dir():
            project = ProjectInfo(item)
            if project.exists:
                projects.append(project)
    
    return sorted(projects, key=lambda p: p.last_modified or datetime.min, reverse=True)


def display_project_status(project: ProjectInfo) -> None:
    """Display detailed status of a single project."""
    if not project.exists:
        console.print(Panel.fit(
            f"❌ [bold red]Project not found or invalid[/bold red]\n"
            f"Path: {project.path}\n"
            "Make sure the directory exists and contains a prompt.txt file.",
            title="Project Status",
            border_style="red"
        ))
        return
    
    # Get metadata
    metadata = project.get_metadata()
    
    # Create status content
    status_lines = [
        f"📁 [bold]Project:[/bold] {project.name}",
        f"📍 [bold]Location:[/bold] {project.path}",
        f"📝 [bold]Prompt:[/bold] {project.prompt[:100]}{'...' if len(project.prompt) > 100 else ''}",
        ""
    ]
    
    # Workspace info
    if project.has_workspace:
        status_lines.extend([
            f"💼 [bold]Workspace:[/bold] ✅ {project.workspace_file_count} files",
        ])
    else:
        status_lines.append("💼 [bold]Workspace:[/bold] ❌ No files generated")
    
    # Logs info
    if project.has_logs:
        status_lines.append(f"📋 [bold]Logs:[/bold] ✅ {project.log_file_count} files")
    else:
        status_lines.append("📋 [bold]Logs:[/bold] ❌ No logs")
    
    # Size and dates
    size_mb = project.total_size / (1024 * 1024)
    status_lines.extend([
        f"💾 [bold]Total Size:[/bold] {size_mb:.1f} MB",
        f"🕒 [bold]Last Modified:[/bold] {project.last_modified.strftime('%Y-%m-%d %H:%M:%S') if project.last_modified else 'Unknown'}"
    ])
    
    # Metadata info
    if metadata:
        status_lines.append("")
        status_lines.append("⚙️ [bold]Metadata:[/bold]")
        for key, value in metadata.items():
            status_lines.append(f"   {key}: {value}")
    
    console.print(Panel(
        "\n".join(status_lines),
        title=f"📊 Project Status: {project.name}",
        border_style="blue",
        expand=True
    ))


def display_project_list(projects: List[ProjectInfo]) -> None:
    """Display a table of all projects."""
    if not projects:
        console.print(Panel.fit(
            "📂 [bold yellow]No AutoSquad projects found[/bold yellow]\n"
            "Create a new project with: [bold]autosquad project create[/bold]",
            title="Project List",
            border_style="yellow"
        ))
        return
    
    table = Table(title="🚀 AutoSquad Projects")
    table.add_column("Name", style="bold blue")
    table.add_column("Status", justify="center")
    table.add_column("Files", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Last Modified", style="dim")
    
    for project in projects:
        # Status indicators
        status_parts = []
        if project.has_workspace:
            status_parts.append("💼")
        if project.has_logs:
            status_parts.append("📋")
        status = " ".join(status_parts) if status_parts else "📝"
        
        # File count
        total_files = project.workspace_file_count + project.log_file_count
        files_text = str(total_files) if total_files > 0 else "-"
        
        # Size
        size_mb = project.total_size / (1024 * 1024)
        size_text = f"{size_mb:.1f}MB" if size_mb > 0.1 else f"{project.total_size}B"
        
        # Last modified
        last_mod = project.last_modified.strftime('%Y-%m-%d %H:%M') if project.last_modified else "-"
        
        table.add_row(
            project.name,
            status,
            files_text,
            size_text,
            last_mod
        )
    
    console.print(table)
    console.print(f"\n[dim]Found {len(projects)} projects. Legend: 💼=Workspace 📋=Logs 📝=Prompt only[/dim]")


def display_project_tree(project: ProjectInfo) -> None:
    """Display a tree view of project contents."""
    if not project.exists:
        console.print("[red]Project not found or invalid[/red]")
        return
    
    tree = Tree(f"📁 [bold blue]{project.name}[/bold blue]")
    
    # Add prompt info
    prompt_text = project.prompt[:50] + "..." if len(project.prompt) > 50 else project.prompt
    tree.add(f"📝 prompt.txt - [dim]{prompt_text}[/dim]")
    
    # Add workspace
    if project.workspace_dir.exists():
        workspace_branch = tree.add("💼 workspace/")
        workspace_files = list(project.workspace_dir.rglob("*"))
        if workspace_files:
            for file_path in sorted(workspace_files):
                if file_path.is_file():
                    rel_path = file_path.relative_to(project.workspace_dir)
                    workspace_branch.add(f"📄 {rel_path}")
        else:
            workspace_branch.add("[dim]empty[/dim]")
    else:
        tree.add("💼 workspace/ [dim](not created)[/dim]")
    
    # Add logs
    if project.logs_dir.exists():
        logs_branch = tree.add("📋 logs/")
        log_files = list(project.logs_dir.rglob("*"))
        if log_files:
            for file_path in sorted(log_files):
                if file_path.is_file():
                    rel_path = file_path.relative_to(project.logs_dir)
                    logs_branch.add(f"📄 {rel_path}")
        else:
            logs_branch.add("[dim]empty[/dim]")
    else:
        tree.add("📋 logs/ [dim](not created)[/dim]")
    
    console.print(tree)


def clean_project(project: ProjectInfo, confirm: bool = True) -> bool:
    """Clean project artifacts (workspace and logs)."""
    if not project.exists:
        console.print("[red]Project not found or invalid[/red]")
        return False
    
    # Calculate what would be cleaned
    items_to_clean = []
    if project.workspace_dir.exists():
        items_to_clean.append(f"💼 Workspace ({project.workspace_file_count} files)")
    if project.logs_dir.exists():
        items_to_clean.append(f"📋 Logs ({project.log_file_count} files)")
    
    if not items_to_clean:
        console.print(Panel.fit(
            "✨ [bold green]Project is already clean![/bold green]\n"
            "No workspace or log files to remove.",
            title="Clean Project",
            border_style="green"
        ))
        return True
    
    # Show what will be cleaned
    console.print(Panel(
        f"🧹 [bold]Cleaning project:[/bold] {project.name}\n\n"
        f"The following will be removed:\n" +
        "\n".join(f"  • {item}" for item in items_to_clean) +
        f"\n\n[dim]The prompt.txt file will be preserved.[/dim]",
        title="Clean Project",
        border_style="yellow"
    ))
    
    if confirm:
        import click
        if not click.confirm("Are you sure you want to continue?"):
            console.print("[yellow]Cleanup cancelled[/yellow]")
            return False
    
    # Perform cleanup
    try:
        cleaned_items = []
        
        if project.workspace_dir.exists():
            shutil.rmtree(project.workspace_dir)
            cleaned_items.append("workspace")
        
        if project.logs_dir.exists():
            shutil.rmtree(project.logs_dir)
            cleaned_items.append("logs")
        
        console.print(Panel.fit(
            f"✅ [bold green]Project cleaned successfully![/bold green]\n"
            f"Removed: {', '.join(cleaned_items)}\n"
            f"Prompt file preserved: {project.prompt_file}",
            title="Cleanup Complete",
            border_style="green"
        ))
        return True
        
    except Exception as e:
        console.print(Panel.fit(
            f"❌ [bold red]Cleanup failed:[/bold red] {e}\n"
            "Some files may not have been removed.",
            title="Cleanup Error",
            border_style="red"
        ))
        return False


def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB" 