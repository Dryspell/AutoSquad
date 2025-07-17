"""
Real-time progress display for AutoSquad - show agent conversations and actions live
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from collections import deque


class AgentProgressTracker:
    """Tracks progress and activity for individual agents."""
    
    def __init__(self, agent_name: str, agent_type: str):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.current_action = "Waiting..."
        self.actions_completed = 0
        self.last_message = ""
        self.last_activity = datetime.now()
        self.is_active = False
        self.files_created = 0
        self.files_modified = 0
        
    def update_action(self, action: str):
        """Update the current action for this agent."""
        self.current_action = action
        self.last_activity = datetime.now()
        self.is_active = True
        
    def complete_action(self):
        """Mark the current action as completed."""
        self.actions_completed += 1
        self.is_active = False
        
    def update_message(self, message: str):
        """Update the last message from this agent."""
        self.last_message = message[:200] + "..." if len(message) > 200 else message
        self.last_activity = datetime.now()
        
    def file_operation(self, operation_type: str):
        """Record a file operation."""
        if operation_type == "create":
            self.files_created += 1
        elif operation_type == "modify":
            self.files_modified += 1


class LiveProgressDisplay:
    """Live terminal display for AutoSquad progress."""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.agents: Dict[str, AgentProgressTracker] = {}
        self.conversation_log = deque(maxlen=50)  # Keep last 50 messages
        self.round_info = {"current": 1, "total": 3}
        self.project_info = {"name": "", "files_created": 0}
        self.token_info = {"used": 0, "estimated_cost": 0.0}
        self.start_time = datetime.now()
        self.live_display = None
        self.is_running = False
        
    def register_agent(self, agent_name: str, agent_type: str):
        """Register an agent for tracking."""
        self.agents[agent_name] = AgentProgressTracker(agent_name, agent_type)
        
    def agent_started_action(self, agent_name: str, action: str):
        """Mark that an agent started an action."""
        if agent_name in self.agents:
            self.agents[agent_name].update_action(action)
            self._log_activity(f"🤖 {agent_name} started: {action}")
            
    def agent_completed_action(self, agent_name: str, result: str = ""):
        """Mark that an agent completed their current action."""
        if agent_name in self.agents:
            self.agents[agent_name].complete_action()
            if result:
                self._log_activity(f"✅ {agent_name} completed: {result}")
                
    def agent_sent_message(self, agent_name: str, message: str):
        """Record a message from an agent."""
        if agent_name in self.agents:
            self.agents[agent_name].update_message(message)
            # Log a truncated version
            short_message = message[:100] + "..." if len(message) > 100 else message
            self._log_activity(f"💬 {agent_name}: {short_message}")
            
    def agent_file_operation(self, agent_name: str, operation: str, file_path: str):
        """Record a file operation by an agent."""
        if agent_name in self.agents:
            self.agents[agent_name].file_operation(operation)
            self.project_info["files_created"] += 1
            self._log_activity(f"📄 {agent_name} {operation}: {file_path}")
            
    def update_round_info(self, current_round: int, total_rounds: int):
        """Update round information."""
        self.round_info = {"current": current_round, "total": total_rounds}
        
    def update_token_usage(self, tokens_used: int, estimated_cost: float):
        """Update token usage information."""
        self.token_info = {"used": tokens_used, "estimated_cost": estimated_cost}
        
    def update_project_info(self, project_name: str, files_created: int = None):
        """Update project information."""
        self.project_info["name"] = project_name
        if files_created is not None:
            self.project_info["files_created"] = files_created
            
    def _log_activity(self, message: str):
        """Add an activity message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation_log.append(f"[dim]{timestamp}[/dim] {message}")
        
    def _create_main_layout(self) -> Layout:
        """Create the main layout for the live display."""
        layout = Layout()
        
        # Split into header, main content, and footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=8)
        )
        
        # Split main into agents and conversation
        layout["main"].split_row(
            Layout(name="agents", ratio=1),
            Layout(name="conversation", ratio=2)
        )
        
        return layout
        
    def _render_header(self) -> Panel:
        """Render the header with project and round info."""
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"{int(elapsed.total_seconds() // 60)}m {int(elapsed.total_seconds() % 60)}s"
        
        title = f"🧠 AutoSquad - {self.project_info['name']}"
        content = f"Round {self.round_info['current']}/{self.round_info['total']} | "
        content += f"Elapsed: {elapsed_str} | "
        content += f"Files: {self.project_info['files_created']} | "
        content += f"Tokens: {self.token_info['used']:,} (~${self.token_info['estimated_cost']:.3f})"
        
        return Panel(
            content,
            title=title,
            border_style="blue",
            padding=(0, 1)
        )
        
    def _render_agents_panel(self) -> Panel:
        """Render the agents status panel."""
        if not self.agents:
            return Panel("No agents registered", title="🤖 Agents", border_style="yellow")
            
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Agent", style="cyan", width=12)
        table.add_column("Status", width=15)
        table.add_column("Current Action", style="green")
        table.add_column("Progress", justify="right", width=8)
        
        for agent in self.agents.values():
            # Agent status
            if agent.is_active:
                status = "[green]🟢 Active[/green]"
            else:
                idle_time = (datetime.now() - agent.last_activity).total_seconds()
                if idle_time < 30:
                    status = "[yellow]🟡 Recent[/yellow]"
                else:
                    status = "[dim]⚪ Waiting[/dim]"
            
            # Progress info
            progress = f"{agent.actions_completed} tasks"
            if agent.files_created + agent.files_modified > 0:
                progress += f", {agent.files_created + agent.files_modified} files"
                
            table.add_row(
                f"{agent.agent_name}",
                status,
                agent.current_action,
                progress
            )
            
        return Panel(table, title="🤖 Agent Status", border_style="green")
        
    def _render_conversation_panel(self) -> Panel:
        """Render the conversation/activity log panel."""
        if not self.conversation_log:
            content = "[dim]No activity yet...[/dim]"
        else:
            # Show recent messages, newest at bottom
            content = "\n".join(list(self.conversation_log)[-20:])  # Last 20 lines
            
        return Panel(
            content,
            title="💬 Agent Activity",
            border_style="cyan",
            height=None
        )
        
    def _render_footer(self) -> Panel:
        """Render the footer with token usage and performance info."""
        # Token usage info
        token_line = f"Token Usage: {self.token_info['used']:,} tokens | Est. Cost: ${self.token_info['estimated_cost']:.4f}"
        
        # Performance info
        active_agents = sum(1 for agent in self.agents.values() if agent.is_active)
        total_actions = sum(agent.actions_completed for agent in self.agents.values())
        performance_line = f"Active Agents: {active_agents}/{len(self.agents)} | Total Actions: {total_actions}"
        
        # Instructions
        instructions = "[dim]Press Ctrl+C to stop | Logs saved to project/logs/[/dim]"
        
        content = f"{token_line}\n{performance_line}\n{instructions}"
        
        return Panel(
            content,
            title="📊 Status",
            border_style="magenta",
            padding=(1, 1)
        )
        
    async def start_live_display(self):
        """Start the live display."""
        if self.is_running:
            return
            
        self.is_running = True
        layout = self._create_main_layout()
        
        with Live(layout, console=self.console, refresh_per_second=2, screen=True) as live:
            self.live_display = live
            
            while self.is_running:
                # Update layout components
                layout["header"].update(self._render_header())
                layout["agents"].update(self._render_agents_panel())
                layout["conversation"].update(self._render_conversation_panel())
                layout["footer"].update(self._render_footer())
                
                await asyncio.sleep(0.5)  # Update every 500ms
                
    def stop_live_display(self):
        """Stop the live display."""
        self.is_running = False
        
    def display_summary(self) -> Panel:
        """Display a final summary when complete."""
        total_actions = sum(agent.actions_completed for agent in self.agents.values())
        total_files = sum(agent.files_created + agent.files_modified for agent in self.agents.values())
        elapsed = datetime.now() - self.start_time
        
        summary_table = Table(show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Runtime", f"{int(elapsed.total_seconds() // 60)}m {int(elapsed.total_seconds() % 60)}s")
        summary_table.add_row("Rounds Completed", str(self.round_info["current"]))
        summary_table.add_row("Actions Taken", str(total_actions))
        summary_table.add_row("Files Created/Modified", str(total_files))
        summary_table.add_row("Tokens Used", f"{self.token_info['used']:,}")
        summary_table.add_row("Estimated Cost", f"${self.token_info['estimated_cost']:.4f}")
        
        return Panel(
            summary_table,
            title="🎉 AutoSquad Session Complete",
            border_style="green"
        )


def create_progress_callback(display: LiveProgressDisplay) -> Dict[str, Callable]:
    """Create callback functions for progress tracking."""
    return {
        "agent_action_started": display.agent_started_action,
        "agent_action_completed": display.agent_completed_action,
        "agent_message": display.agent_sent_message,
        "file_operation": display.agent_file_operation,
        "round_update": display.update_round_info,
        "token_update": display.update_token_usage
    } 