"""
Progress Tracking Module - Tracks and persists squad execution progress
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn
from rich.table import Table

console = Console()


class ProgressTracker:
    """Tracks and persists progress for squad execution sessions."""
    
    def __init__(self, session_name: str, project_path: Path):
        self.session_name = session_name
        self.project_path = project_path
        self.session_dir = project_path / ".autosquad" / "sessions" / session_name
        self.progress_file = self.session_dir / "progress.json"
        
        # Progress state
        self.rounds_completed = 0
        self.total_rounds = 0
        self.current_round = 0
        self.current_agent = ""
        self.current_task = ""
        self.start_time = None
        self.round_times = []
        self.agent_interactions = []
        self.errors = []
        self.milestones = []
        
        # Load existing progress if available
        self.load_progress()
    
    def initialize_tracking(self, total_rounds: int) -> None:
        """Initialize progress tracking for a new session."""
        self.total_rounds = total_rounds
        self.start_time = datetime.now()
        self.save_progress()
    
    def start_round(self, round_number: int) -> None:
        """Mark the start of a new round."""
        self.current_round = round_number
        self.round_start_time = time.time()
        self.current_task = f"Starting round {round_number}"
        self.save_progress()
    
    def end_round(self, round_number: int) -> None:
        """Mark the end of a round."""
        if hasattr(self, 'round_start_time'):
            round_duration = time.time() - self.round_start_time
            self.round_times.append({
                "round": round_number,
                "duration": round_duration,
                "completed_at": datetime.now().isoformat()
            })
        
        self.rounds_completed = round_number
        self.current_task = f"Round {round_number} completed"
        self.save_progress()
    
    def set_current_agent(self, agent_name: str, task: str = "") -> None:
        """Update current agent and task."""
        self.current_agent = agent_name
        self.current_task = task or f"Agent {agent_name} working"
        self.save_progress()
    
    def add_agent_interaction(self, agent: str, message_type: str, message_count: int) -> None:
        """Record an agent interaction."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "type": message_type,
            "count": message_count,
            "round": self.current_round
        }
        self.agent_interactions.append(interaction)
        self.save_progress()
    
    def add_milestone(self, title: str, description: str) -> None:
        """Add a milestone to track significant progress points."""
        milestone = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "description": description,
            "round": self.current_round
        }
        self.milestones.append(milestone)
        self.save_progress()
    
    def add_error(self, error_type: str, error_message: str) -> None:
        """Record an error for troubleshooting."""
        error = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": error_message,
            "round": self.current_round,
            "agent": self.current_agent
        }
        self.errors.append(error)
        self.save_progress()
    
    def get_estimated_completion(self) -> Optional[datetime]:
        """Estimate completion time based on round durations."""
        if not self.round_times or self.rounds_completed == 0:
            return None
        
        # Calculate average round time
        total_time = sum(rt["duration"] for rt in self.round_times)
        avg_round_time = total_time / len(self.round_times)
        
        # Estimate remaining time
        remaining_rounds = self.total_rounds - self.rounds_completed
        estimated_remaining_seconds = remaining_rounds * avg_round_time
        
        return datetime.now() + timedelta(seconds=estimated_remaining_seconds)
    
    def get_progress_percentage(self) -> float:
        """Get completion percentage."""
        if self.total_rounds == 0:
            return 0.0
        return (self.rounds_completed / self.total_rounds) * 100
    
    def save_progress(self) -> None:
        """Save progress state to file."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        progress_data = {
            "session_name": self.session_name,
            "project_path": str(self.project_path),
            "rounds_completed": self.rounds_completed,
            "total_rounds": self.total_rounds,
            "current_round": self.current_round,
            "current_agent": self.current_agent,
            "current_task": self.current_task,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "round_times": self.round_times,
            "agent_interactions": self.agent_interactions,
            "errors": self.errors,
            "milestones": self.milestones,
            "last_updated": datetime.now().isoformat()
        }
        
        self.progress_file.write_text(json.dumps(progress_data, indent=2))
    
    def load_progress(self) -> None:
        """Load progress state from file."""
        if not self.progress_file.exists():
            return
        
        try:
            progress_data = json.loads(self.progress_file.read_text())
            
            self.rounds_completed = progress_data.get("rounds_completed", 0)
            self.total_rounds = progress_data.get("total_rounds", 0)
            self.current_round = progress_data.get("current_round", 0)
            self.current_agent = progress_data.get("current_agent", "")
            self.current_task = progress_data.get("current_task", "")
            self.round_times = progress_data.get("round_times", [])
            self.agent_interactions = progress_data.get("agent_interactions", [])
            self.errors = progress_data.get("errors", [])
            self.milestones = progress_data.get("milestones", [])
            
            start_time_str = progress_data.get("start_time")
            if start_time_str:
                self.start_time = datetime.fromisoformat(start_time_str)
                
        except Exception as e:
            console.print(f"[yellow]⚠️  Warning: Could not load progress data: {e}[/yellow]")
    
    def display_progress_summary(self) -> None:
        """Display a comprehensive progress summary."""
        console.print(Panel.fit(
            f"🧠 [bold blue]Squad Progress Summary[/bold blue]\n"
            f"📁 Project: {self.project_path.name}\n"
            f"💾 Session: {self.session_name}\n"
            f"🔄 Progress: {self.rounds_completed}/{self.total_rounds} rounds ({self.get_progress_percentage():.1f}%)\n"
            f"👤 Current Agent: {self.current_agent or 'None'}\n"
            f"📝 Current Task: {self.current_task or 'Idle'}",
            title="Progress Summary",
            border_style="blue"
        ))
        
        # Show timing information
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            console.print(f"\n⏱️  [bold]Timing:[/bold]")
            console.print(f"   Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            console.print(f"   Elapsed: {str(elapsed).split('.')[0]}")
            
            estimated_completion = self.get_estimated_completion()
            if estimated_completion:
                console.print(f"   Estimated completion: {estimated_completion.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show round timing
        if self.round_times:
            console.print(f"\n🔄 [bold]Round Performance:[/bold]")
            for rt in self.round_times[-3:]:  # Show last 3 rounds
                duration_str = f"{rt['duration']:.1f}s"
                console.print(f"   Round {rt['round']}: {duration_str}")
        
        # Show recent milestones
        if self.milestones:
            console.print(f"\n🎯 [bold]Recent Milestones:[/bold]")
            for milestone in self.milestones[-3:]:  # Show last 3 milestones
                console.print(f"   • {milestone['title']}")
        
        # Show errors if any
        if self.errors:
            console.print(f"\n⚠️  [bold yellow]Issues:[/bold yellow] {len(self.errors)} error(s) encountered")
    
    def display_detailed_progress(self) -> None:
        """Display detailed progress information."""
        self.display_progress_summary()
        
        # Agent interactions table
        if self.agent_interactions:
            console.print(f"\n[bold]Agent Interactions:[/bold]")
            table = Table()
            table.add_column("Time", style="dim")
            table.add_column("Agent", style="bold")
            table.add_column("Type", style="cyan")
            table.add_column("Messages", justify="right")
            table.add_column("Round", justify="center")
            
            for interaction in self.agent_interactions[-10:]:  # Last 10 interactions
                timestamp = datetime.fromisoformat(interaction['timestamp'])
                time_str = timestamp.strftime("%H:%M:%S")
                
                table.add_row(
                    time_str,
                    interaction['agent'],
                    interaction['type'],
                    str(interaction['count']),
                    str(interaction['round'])
                )
            
            console.print(table)
        
        # Error details if any
        if self.errors:
            console.print(f"\n[bold red]Errors:[/bold red]")
            for error in self.errors[-5:]:  # Last 5 errors
                timestamp = datetime.fromisoformat(error['timestamp'])
                time_str = timestamp.strftime("%H:%M:%S")
                console.print(f"   {time_str} [red]{error['type']}[/red]: {error['message']}")


def get_session_progress(session_name: str, project_path: Optional[Path] = None) -> Optional[ProgressTracker]:
    """Get progress tracker for a specific session."""
    if not project_path:
        # Search for session in all projects
        projects_dir = Path("projects")
        if projects_dir.exists():
            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir():
                    session_dir = project_dir / ".autosquad" / "sessions" / session_name
                    if session_dir.exists():
                        return ProgressTracker(session_name, project_dir)
    else:
        return ProgressTracker(session_name, project_path)
    
    return None


def list_active_sessions() -> List[Dict[str, Any]]:
    """List all active/recent sessions with their progress."""
    active_sessions = []
    
    projects_dir = Path("projects")
    if not projects_dir.exists():
        return active_sessions
    
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            sessions_dir = project_dir / ".autosquad" / "sessions"
            if sessions_dir.exists():
                for session_dir in sessions_dir.iterdir():
                    if session_dir.is_dir():
                        progress_file = session_dir / "progress.json"
                        if progress_file.exists():
                            try:
                                tracker = ProgressTracker(session_dir.name, project_dir)
                                active_sessions.append({
                                    "session_name": tracker.session_name,
                                    "project": project_dir.name,
                                    "progress": tracker.get_progress_percentage(),
                                    "current_round": tracker.current_round,
                                    "total_rounds": tracker.total_rounds,
                                    "current_task": tracker.current_task,
                                    "start_time": tracker.start_time
                                })
                            except Exception:
                                continue
    
    return active_sessions 