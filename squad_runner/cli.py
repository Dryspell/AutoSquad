"""
AutoSquad CLI - Command-line interface for running autonomous development squads
"""

import asyncio
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from .execution import run_squad
from .exceptions import AutoSquadError
from .validation import validate_all_inputs, validate_configuration, validate_api_key
from .project_utils import (
    ProjectInfo, find_projects, display_project_status, 
    display_project_list, display_project_tree, clean_project
)

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """AutoSquad - Autonomous Multi-Agent Development Framework
    
    Spin up AI development teams to build software from simple prompts.
    """
    pass


# Legacy command for backward compatibility  
@cli.command()
@click.option(
    "--project", 
    "-p", 
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to project directory containing prompt.txt"
)
@click.option(
    "--squad-profile",
    "-s",
    default="mvp-team",
    help="Squad profile to use (use 'autosquad list-profiles' to see available options)"
)
@click.option(
    "--rounds",
    "-r",
    default=3,
    type=click.IntRange(min=1, max=10),
    help="Number of development rounds to run (1-10)"
)
@click.option(
    "--model",
    "-m",
    default="gpt-4",
    help="LLM model to use for agents"
)
@click.option(
    "--reflect/--no-reflect",
    default=True,
    help="Enable reflection and planning between rounds"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option(
    "--no-live-display",
    is_flag=True,
    help="Disable live progress display (use basic logging instead)"
)
@click.option(
    "--debug-mode",
    is_flag=True,
    help="Enable debug mode with limited API calls and detailed logging"
)
@click.option(
    "--max-messages",
    type=int,
    default=None,
    help="Maximum number of messages per round (debug mode)"
)
def run(
    project: Path,
    squad_profile: str,
    rounds: int,
    model: str,
    reflect: bool,
    verbose: bool,
    no_live_display: bool,
    debug_mode: bool,
    max_messages: int
):
    """Run an autonomous development squad on a project (legacy command - use 'run start' instead)."""
    console.print("[yellow]ℹ️  Note: This command is deprecated. Use 'autosquad run start' for new features.[/yellow]\n")
    
    # Show initial project info
    console.print(Panel.fit(
        f"🧠 [bold blue]AutoSquad[/bold blue] - Starting Development Squad\n"
        f"📁 Project: {project}\n"
        f"👥 Squad: {squad_profile}\n"
        f"🔄 Rounds: {rounds}\n"
        f"🤖 Model: {model}",
        title="AutoSquad",
        border_style="blue"
    ))
    
    try:
        # Run the squad using the new execution engine
        asyncio.run(run_squad(
            project_path=project,
            squad_profile=squad_profile,
            rounds=rounds,
            model=model,
            reflect=reflect,
            verbose=verbose,
            show_live_progress=not no_live_display,
            debug_mode=debug_mode,
            max_messages=max_messages
        ))
        
        console.print(Panel.fit(
            "✅ [bold green]Squad completed successfully![/bold green]\n"
            f"📂 Check {project}/workspace/ for generated code\n"
            f"📝 Check {project}/logs/ for conversation logs",
            title="Success",
            border_style="green"
        ))
        
    except AutoSquadError:
        # AutoSquadError exceptions are already well-formatted and displayed
        raise click.ClickException("")  # Exit with error code but no additional message
    except Exception as e:
        error_msg = str(e)
        
        # Check if this is one of our friendly formatted error messages
        if error_msg.startswith("🚫") or "OpenAI API" in error_msg:
            console.print(Panel(
                error_msg,
                title="❌ API Error",
                border_style="red",
                expand=True
            ))
        else:
            console.print(Panel.fit(
                f"❌ [bold red]Squad failed:[/bold red] {error_msg}",
                title="Error",
                border_style="red"
            ))
        
        if verbose:
            console.print_exception()
        raise click.ClickException(str(e))


@cli.group()
def run():
    """Advanced squad execution with session management."""
    pass


@run.command()
@click.option(
    "--project", 
    "-p", 
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to project directory containing prompt.txt"
)
@click.option(
    "--squad-profile",
    "-s",
    help="Squad profile to use (will auto-detect available profiles)"
)
@click.option(
    "--rounds",
    "-r",
    default=3,
    type=click.IntRange(min=1, max=10),
    help="Number of development rounds to run (1-10)"
)
@click.option(
    "--model",
    "-m",
    default="gpt-4",
    help="LLM model to use for agents"
)
@click.option(
    "--reflect/--no-reflect",
    default=True,
    help="Enable reflection and planning between rounds"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option(
    "--no-live-display",
    is_flag=True,
    help="Disable live progress display (use basic logging instead)"
)
@click.option(
    "--debug-mode",
    is_flag=True,
    help="Enable debug mode with limited API calls and detailed logging"
)
@click.option(
    "--max-messages",
    type=int,
    default=None,
    help="Maximum number of messages per round (debug mode)"
)
@click.option(
    "--session-name",
    help="Custom session name for tracking and resuming"
)
@click.option(
    "--save-session/--no-save-session",
    default=True,
    help="Save session state for resuming later"
)
def start(
    project: Path,
    squad_profile: Optional[str],
    rounds: int,
    model: str,
    reflect: bool,
    verbose: bool,
    no_live_display: bool,
    debug_mode: bool,
    max_messages: int,
    session_name: Optional[str],
    save_session: bool
):
    """Start a new development squad session."""
    
    # Auto-detect squad profile if not provided
    if not squad_profile:
        try:
            from .config import get_default_squad_profiles
            available_profiles = list(get_default_squad_profiles().keys())
            squad_profile = click.prompt(
                f"Select squad profile {available_profiles}",
                type=click.Choice(available_profiles),
                default="mvp-team"
            )
        except Exception:
            squad_profile = "mvp-team"
    
    # Generate session name if not provided
    if not session_name and save_session:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"session_{timestamp}"
    
    # Show initial project info
    console.print(Panel.fit(
        f"🧠 [bold blue]AutoSquad[/bold blue] - Starting Development Squad\n"
        f"📁 Project: {project}\n"
        f"👥 Squad: {squad_profile}\n"
        f"🔄 Rounds: {rounds}\n"
        f"🤖 Model: {model}"
        + (f"\n💾 Session: {session_name}" if session_name else ""),
        title="AutoSquad",
        border_style="blue"
    ))
    
    try:
        # Create session state directory if needed
        if save_session and session_name:
            session_dir = project / ".autosquad" / "sessions" / session_name
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Save session metadata
            session_metadata = {
                "session_name": session_name,
                "created_at": datetime.now().isoformat(),
                "project_path": str(project),
                "squad_profile": squad_profile,
                "rounds": rounds,
                "model": model,
                "reflect": reflect,
                "status": "running"
            }
            
            import json
            (session_dir / "metadata.json").write_text(json.dumps(session_metadata, indent=2))
            console.print(f"💾 Session saved as: {session_name}")
        
        # Run the squad using the new execution engine
        asyncio.run(run_squad(
            project_path=project,
            squad_profile=squad_profile,
            rounds=rounds,
            model=model,
            reflect=reflect,
            verbose=verbose,
            show_live_progress=not no_live_display,
            debug_mode=debug_mode,
            max_messages=max_messages
        ))
        
        # Update session status if saved
        if save_session and session_name:
            session_metadata["status"] = "completed"
            session_metadata["completed_at"] = datetime.now().isoformat()
            (session_dir / "metadata.json").write_text(json.dumps(session_metadata, indent=2))
        
        console.print(Panel.fit(
            "✅ [bold green]Squad completed successfully![/bold green]\n"
            f"📂 Check {project}/workspace/ for generated code\n"
            f"📝 Check {project}/logs/ for conversation logs"
            + (f"\n💾 Session: {session_name}" if session_name else ""),
            title="Success",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        # Handle graceful shutdown
        if save_session and session_name:
            session_metadata["status"] = "interrupted"
            session_metadata["interrupted_at"] = datetime.now().isoformat()
            (session_dir / "metadata.json").write_text(json.dumps(session_metadata, indent=2))
            console.print(f"\n💾 Session state saved. Resume with: autosquad run resume {session_name}")
        
        console.print("\n🛑 Squad execution interrupted by user")
        raise click.ClickException("")
        
    except AutoSquadError:
        # Update session status on error
        if save_session and session_name:
            session_metadata["status"] = "failed"
            session_metadata["failed_at"] = datetime.now().isoformat()
            (session_dir / "metadata.json").write_text(json.dumps(session_metadata, indent=2))
        
        raise click.ClickException("")
    except Exception as e:
        # Update session status on error
        if save_session and session_name:
            session_metadata["status"] = "failed"
            session_metadata["failed_at"] = datetime.now().isoformat() 
            session_metadata["error"] = str(e)
            (session_dir / "metadata.json").write_text(json.dumps(session_metadata, indent=2))
        
        error_msg = str(e)
        
        if error_msg.startswith("🚫") or "OpenAI API" in error_msg:
            console.print(Panel(
                error_msg,
                title="❌ API Error",
                border_style="red",
                expand=True
            ))
        else:
            console.print(Panel.fit(
                f"❌ [bold red]Squad failed:[/bold red] {error_msg}",
                title="Error",
                border_style="red"
            ))
        
        if verbose:
            console.print_exception()
        raise click.ClickException(str(e))


@run.command()
@click.argument("session_name")
@click.option(
    "--continue-rounds",
    "-r",
    type=int,
    help="Additional rounds to run (default: continue with original settings)"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging"
)
def resume(session_name: str, continue_rounds: Optional[int], verbose: bool):
    """Resume a previously interrupted squad session."""
    
    console.print(f"🔄 [bold blue]Resuming session: {session_name}[/bold blue]")
    
    try:
        # Find the session
        projects_dir = Path("projects")
        session_found = False
        session_metadata = None
        project_path = None
        
        # Search for session in all projects
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                session_dir = project_dir / ".autosquad" / "sessions" / session_name
                metadata_file = session_dir / "metadata.json"
                
                if metadata_file.exists():
                    import json
                    session_metadata = json.loads(metadata_file.read_text())
                    project_path = Path(session_metadata["project_path"])
                    session_found = True
                    break
        
        if not session_found:
            console.print(f"[red]❌ Session '{session_name}' not found[/red]")
            console.print("Use 'autosquad run list-sessions' to see available sessions")
            raise click.ClickException("Session not found")
        
        # Check session status
        status = session_metadata.get("status", "unknown")
        if status == "completed":
            console.print("[yellow]⚠️  This session was already completed[/yellow]")
            if not click.confirm("Continue anyway?"):
                raise click.ClickException("Resume cancelled")
        elif status == "running":
            console.print("[yellow]⚠️  This session appears to be running[/yellow]")
            if not click.confirm("Resume anyway (may cause conflicts)?"):
                raise click.ClickException("Resume cancelled")
        
        # Show session info
        console.print(Panel.fit(
            f"📁 Project: {session_metadata['project_path']}\n"
            f"👥 Squad: {session_metadata['squad_profile']}\n"
            f"🔄 Original Rounds: {session_metadata['rounds']}\n"
            f"🤖 Model: {session_metadata['model']}\n"
            f"📅 Created: {session_metadata['created_at']}\n"
            f"🔄 Status: {status}"
            + (f"\n🔄 Additional Rounds: {continue_rounds}" if continue_rounds else ""),
            title="Session Info",
            border_style="blue"
        ))
        
        # Update session metadata
        session_metadata["status"] = "running"
        session_metadata["resumed_at"] = datetime.now().isoformat()
        if continue_rounds:
            session_metadata["additional_rounds"] = continue_rounds
        
        session_dir = project_path / ".autosquad" / "sessions" / session_name
        import json
        (session_dir / "metadata.json").write_text(json.dumps(session_metadata, indent=2))
        
        # Resume the squad
        rounds = continue_rounds or session_metadata["rounds"]
        asyncio.run(run_squad(
            project_path=project_path,
            squad_profile=session_metadata["squad_profile"],
            rounds=rounds,
            model=session_metadata["model"],
            reflect=session_metadata.get("reflect", True),
            verbose=verbose,
            show_live_progress=True,
            debug_mode=False,
            max_messages=None
        ))
        
        # Update completion status
        session_metadata["status"] = "completed"
        session_metadata["completed_at"] = datetime.now().isoformat()
        (session_dir / "metadata.json").write_text(json.dumps(session_metadata, indent=2))
        
        console.print(Panel.fit(
            "✅ [bold green]Session resumed and completed successfully![/bold green]\n"
            f"📂 Check {project_path}/workspace/ for generated code\n"
            f"📝 Check {project_path}/logs/ for conversation logs\n"
            f"💾 Session: {session_name}",
            title="Success",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        # Update session status on interruption
        if session_metadata:
            session_metadata["status"] = "interrupted"
            session_metadata["interrupted_at"] = datetime.now().isoformat()
            (session_dir / "metadata.json").write_text(json.dumps(session_metadata, indent=2))
        
        console.print(f"\n💾 Session state saved. Resume again with: autosquad run resume {session_name}")
        console.print("\n🛑 Squad execution interrupted by user")
        raise click.ClickException("")
        
    except Exception as e:
        console.print(f"[red]❌ Error resuming session: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.ClickException(str(e))


@run.command()
@click.argument("session_name", required=False)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Stop all running sessions"
)
def stop(session_name: Optional[str], all: bool):
    """Stop a running squad session."""
    
    if all:
        console.print("🛑 [bold red]Stopping all running sessions...[/bold red]")
        # This would require process management - placeholder for now
        console.print("[yellow]⚠️  Process stopping not yet implemented[/yellow]")
        console.print("Use Ctrl+C to interrupt running sessions")
        return
    
    if not session_name:
        console.print("[red]❌ Please specify a session name or use --all[/red]")
        raise click.ClickException("Session name required")
    
    console.print(f"🛑 [bold red]Stopping session: {session_name}[/bold red]")
    console.print("[yellow]⚠️  Process stopping not yet implemented[/yellow]")
    console.print("Use Ctrl+C to interrupt the running session")


@run.command(name="list-sessions")
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Show sessions for specific project only"
)
@click.option(
    "--status",
    "-s",
    type=click.Choice(["running", "completed", "interrupted", "failed", "all"]),
    default="all",
    help="Filter by session status"
)
def list_sessions(project: Optional[Path], status: str):
    """List squad execution sessions."""
    
    console.print("[bold blue]📋 Squad Sessions[/bold blue]\n")
    
    sessions_found = []
    
    # Determine search scope
    if project:
        search_dirs = [project]
    else:
        projects_dir = Path("projects")
        if projects_dir.exists():
            search_dirs = [d for d in projects_dir.iterdir() if d.is_dir()]
        else:
            search_dirs = []
    
    # Search for sessions
    for project_dir in search_dirs:
        sessions_dir = project_dir / ".autosquad" / "sessions"
        if sessions_dir.exists():
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir():
                    metadata_file = session_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            import json
                            metadata = json.loads(metadata_file.read_text())
                            if status == "all" or metadata.get("status") == status:
                                sessions_found.append((project_dir, session_dir, metadata))
                        except Exception:
                            continue
    
    if not sessions_found:
        if project:
            console.print(f"[dim]No sessions found for project {project}[/dim]")
        else:
            console.print("[dim]No sessions found in any projects[/dim]")
        return
    
    # Display sessions grouped by project
    current_project = None
    for project_dir, session_dir, metadata in sorted(sessions_found, key=lambda x: x[0].name):
        if current_project != project_dir:
            current_project = project_dir
            console.print(f"\n[bold]📁 {project_dir.name}[/bold]")
        
        session_name = metadata["session_name"]
        session_status = metadata.get("status", "unknown")
        created_at = metadata.get("created_at", "unknown")
        squad_profile = metadata.get("squad_profile", "unknown")
        
        # Status emoji
        status_emoji = {
            "running": "🟡",
            "completed": "✅", 
            "interrupted": "🟠",
            "failed": "❌"
        }.get(session_status, "❓")
        
        # Format creation time
        try:
            from datetime import datetime
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            time_str = created_time.strftime("%m/%d %H:%M")
        except:
            time_str = created_at[:16] if len(created_at) > 16 else created_at
        
        console.print(f"  {status_emoji} [bold]{session_name}[/bold] ({squad_profile})")
        console.print(f"     [dim]Created: {time_str} | Status: {session_status}[/dim]")
        
        # Show resume command for interrupted sessions
        if session_status == "interrupted":
            console.print(f"     [dim]Resume: autosquad run resume {session_name}[/dim]")
    
    console.print()  # Empty line at end


@run.command()
@click.argument("session_name", required=False)
@click.option(
    "--detailed",
    "-d",
    is_flag=True,
    help="Show detailed progress including agent interactions"
)
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Project path (if session name is ambiguous)"
)
def progress(session_name: Optional[str], detailed: bool, project: Optional[Path]):
    """Show progress for a specific session or list all active sessions."""
    
    try:
        from .progress_tracking import get_session_progress, list_active_sessions
        
        if session_name:
            # Show progress for specific session
            tracker = get_session_progress(session_name, project)
            if not tracker:
                console.print(f"[red]❌ Session '{session_name}' not found[/red]")
                console.print("Use 'autosquad run list-sessions' to see available sessions")
                raise click.ClickException("Session not found")
            
            if detailed:
                tracker.display_detailed_progress()
            else:
                tracker.display_progress_summary()
        else:
            # Show all active sessions
            sessions = list_active_sessions()
            
            if not sessions:
                console.print("[dim]No active sessions found[/dim]")
                return
            
            console.print("[bold blue]🔄 Active Squad Sessions[/bold blue]\n")
            
            for session in sorted(sessions, key=lambda x: x["start_time"] or datetime.min, reverse=True):
                progress_pct = session["progress"]
                current_round = session["current_round"]
                total_rounds = session["total_rounds"]
                
                # Progress bar
                bar_length = 20
                filled = int(progress_pct / 100 * bar_length)
                bar = "█" * filled + "░" * (bar_length - filled)
                
                console.print(f"[bold]{session['session_name']}[/bold] ({session['project']})")
                console.print(f"  {bar} {progress_pct:.1f}% ({current_round}/{total_rounds} rounds)")
                console.print(f"  [dim]Task: {session['current_task']}[/dim]")
                
                if session['start_time']:
                    elapsed = datetime.now() - session['start_time']
                    console.print(f"  [dim]Running for: {str(elapsed).split('.')[0]}[/dim]")
                
                console.print()
                
    except ImportError:
        console.print("[red]❌ Progress tracking module not available[/red]")
        raise click.ClickException("Feature not available")
    except Exception as e:
        console.print(f"[red]❌ Error showing progress: {e}[/red]")
        raise click.ClickException(str(e))


@cli.group()
def project():
    """Manage AutoSquad projects."""
    pass


@project.command()
@click.option(
    "--name",
    "-n",
    required=True,
    help="Name of the new project"
)
@click.option(
    "--prompt",
    "-p",
    help="Initial project prompt (or will prompt interactively)"
)
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(path_type=Path),
    default=Path("projects"),
    help="Base directory for projects (default: projects/)"
)
def create(name: str, prompt: Optional[str], base_dir: Path):
    """Create a new AutoSquad project."""
    
    project_path = base_dir / name
    
    if project_path.exists():
        raise click.ClickException(f"Project {name} already exists at {project_path}")
    
    # Create project structure
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "workspace").mkdir(exist_ok=True)
    (project_path / "logs").mkdir(exist_ok=True)
    
    # Get prompt if not provided
    if not prompt:
        prompt = click.prompt("Enter your project prompt", type=str)
    
    # Write prompt file
    (project_path / "prompt.txt").write_text(prompt)
    
    # Create initial metadata
    project_info = ProjectInfo(project_path)
    metadata = {
        "created_at": datetime.now().isoformat(),
        "created_with": "autosquad-cli",
        "version": "0.1.0"
    }
    project_info.save_metadata(metadata)
    
    console.print(Panel.fit(
        f"✅ [bold green]Project created![/bold green]\n"
        f"📁 Location: {project_path}\n"
        f"📝 Prompt: {prompt}\n\n"
        f"Run with: [bold]autosquad run --project {project_path}[/bold]",
        title="Project Created",
        border_style="green"
    ))


@project.command(name="list")
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(path_type=Path),
    default=Path("projects"),
    help="Base directory to search for projects (default: projects/)"
)
def list_projects(base_dir: Path):
    """List all AutoSquad projects."""
    console.print(f"[dim]Searching for projects in {base_dir}...[/dim]\n")
    
    projects = find_projects(base_dir)
    display_project_list(projects)


@project.command()
@click.argument("name")
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(path_type=Path),
    default=Path("projects"),
    help="Base directory for projects (default: projects/)"
)
@click.option(
    "--tree",
    "-t",
    is_flag=True,
    help="Show project contents as a tree"
)
def status(name: str, base_dir: Path, tree: bool):
    """Show detailed status of a project."""
    project_path = base_dir / name
    project_info = ProjectInfo(project_path)
    
    if tree:
        display_project_tree(project_info)
    else:
        display_project_status(project_info)


@project.command()
@click.argument("name")
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(path_type=Path),
    default=Path("projects"),
    help="Base directory for projects (default: projects/)"
)
def info(name: str, base_dir: Path):
    """Show project information and tree structure."""
    project_path = base_dir / name
    project_info = ProjectInfo(project_path)
    
    # Show both status and tree
    display_project_status(project_info)
    console.print("\n")
    display_project_tree(project_info)


@project.command()
@click.argument("name")
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(path_type=Path),
    default=Path("projects"),
    help="Base directory for projects (default: projects/)"
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompt"
)
def clean(name: str, base_dir: Path, force: bool):
    """Clean project artifacts (workspace and logs)."""
    project_path = base_dir / name
    project_info = ProjectInfo(project_path)
    
    success = clean_project(project_info, confirm=not force)
    if not success:
        raise click.ClickException("Project cleanup failed")


# Legacy command for backward compatibility
@cli.command()
@click.option(
    "--name",
    "-n",
    required=True,
    help="Name of the new project"
)
@click.option(
    "--prompt",
    "-p",
    help="Initial project prompt (or will prompt interactively)"
)
def create(name: str, prompt: Optional[str]):
    """Create a new AutoSquad project (legacy command - use 'project create' instead)."""
    console.print("[yellow]ℹ️  Note: This command is deprecated. Use 'autosquad project create' instead.[/yellow]\n")
    
    from datetime import datetime
    
    project_path = Path("projects") / name
    
    if project_path.exists():
        raise click.ClickException(f"Project {name} already exists at {project_path}")
    
    # Create project structure
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "workspace").mkdir(exist_ok=True)
    (project_path / "logs").mkdir(exist_ok=True)
    
    # Get prompt if not provided
    if not prompt:
        prompt = click.prompt("Enter your project prompt", type=str)
    
    # Write prompt file
    (project_path / "prompt.txt").write_text(prompt)
    
    console.print(Panel.fit(
        f"✅ [bold green]Project created![/bold green]\n"
        f"📁 Location: {project_path}\n"
        f"📝 Prompt: {prompt}\n\n"
        f"Run with: [bold]autosquad run --project {project_path}[/bold]",
        title="Project Created",
        border_style="green"
    ))


@cli.group()
def config():
    """Manage AutoSquad configuration."""
    pass


@config.command()
def validate():
    """Validate current AutoSquad configuration."""
    console.print("[dim]🔍 Validating AutoSquad configuration...[/dim]")
    
    try:
        validate_configuration()
        console.print(Panel.fit(
            "✅ [bold green]Configuration is valid![/bold green]\n"
            "All configuration files and settings are properly configured.",
            title="Configuration Valid",
            border_style="green"
        ))
    except AutoSquadError as e:
        console.print(Panel(
            str(e),
            title="❌ Configuration Error",
            border_style="red",
            expand=True
        ))
        raise click.ClickException("")


@config.command()
def check_api():
    """Test OpenAI API connectivity."""
    console.print("[dim]🔍 Testing OpenAI API connectivity...[/dim]")
    
    try:
        api_key = validate_api_key()
        console.print(Panel.fit(
            "✅ [bold green]API connection successful![/bold green]\n"
            f"API key: {api_key[:8]}...{api_key[-4:]}\n"
            "OpenAI API is accessible and working properly.",
            title="API Connection Test",
            border_style="green"
        ))
    except AutoSquadError as e:
        console.print(Panel(
            str(e),
            title="❌ API Connection Failed",
            border_style="red",
            expand=True
        ))
        raise click.ClickException("")


@config.command()
@click.option(
    "--api-key",
    prompt="Enter your OpenAI API key",
    hide_input=True,
    help="OpenAI API key for authentication"
)
def setup(api_key: str):
    """Interactive configuration setup."""
    console.print(Panel.fit(
        "🔧 [bold blue]AutoSquad Configuration Setup[/bold blue]\n"
        "Setting up your AutoSquad configuration...",
        title="Setup",
        border_style="blue"
    ))
    
    # Validate the provided API key
    try:
        validate_api_key(api_key)
        console.print("[green]✅ API key validated successfully[/green]")
    except AutoSquadError as e:
        console.print(Panel(
            str(e),
            title="❌ Invalid API Key",
            border_style="red",
            expand=True
        ))
        raise click.ClickException("")
    
    # Set environment variable
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Create or update .env file
    env_path = Path(".env")
    if env_path.exists():
        # Read existing .env and update
        lines = []
        found_key = False
        for line in env_path.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                lines.append(f"OPENAI_API_KEY={api_key}")
                found_key = True
            else:
                lines.append(line)
        
        if not found_key:
            lines.append(f"OPENAI_API_KEY={api_key}")
        
        env_path.write_text("\n".join(lines))
    else:
        env_path.write_text(f"OPENAI_API_KEY={api_key}\n")
    
    console.print(Panel.fit(
        "✅ [bold green]Configuration setup complete![/bold green]\n"
        f"API key saved to {env_path}\n"
        "You can now run AutoSquad commands.",
        title="Setup Complete",
        border_style="green"
    ))


@config.command()
def show():
    """Show current configuration."""
    from .config import load_config, get_config_dir
    
    console.print("[bold blue]AutoSquad Configuration:[/bold blue]\n")
    
    try:
        config = load_config()
        config_dir = get_config_dir()
        
        # Show configuration source
        console.print(f"📁 [bold]Config Directory:[/bold] {config_dir}")
        
        # Show LLM configuration (hiding sensitive info)
        llm_config = config.llm_config
        console.print(f"\n🤖 [bold]LLM Configuration:[/bold]")
        console.print(f"   Model: {llm_config.get('model', 'Not set')}")
        console.print(f"   Temperature: {llm_config.get('temperature', 'Not set')}")
        console.print(f"   Max Tokens: {llm_config.get('max_tokens', 'Not set')}")
        
        api_key = llm_config.get('api_key', 'Not set')
        if api_key and api_key != 'Not set':
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                actual_key = os.getenv(env_var)
                if actual_key:
                    console.print(f"   API Key: {actual_key[:8]}...{actual_key[-4:]} (from {env_var})")
                else:
                    console.print(f"   API Key: [red]Environment variable {env_var} not set[/red]")
            else:
                console.print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
        else:
            console.print("   API Key: [red]Not configured[/red]")
        
        # Show runtime configuration
        runtime_config = config.runtime_config
        console.print(f"\n⚙️  [bold]Runtime Configuration:[/bold]")
        console.print(f"   Code Execution: {runtime_config.get('code_execution', 'Not set')}")
        console.print(f"   Execution Timeout: {runtime_config.get('execution_timeout', 'Not set')}s")
        console.print(f"   Max Auto Reply: {runtime_config.get('max_consecutive_auto_reply', 'Not set')}")
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")


@cli.command()
def init():
    """Interactive setup wizard for new users."""
    console.print(Panel.fit(
        "🚀 [bold blue]Welcome to AutoSquad![/bold blue]\n"
        "This wizard will help you set up AutoSquad and create your first project.",
        title="AutoSquad Setup Wizard",
        border_style="blue"
    ))
    
    try:
        # Step 1: Check/setup API key
        console.print("\n[bold]Step 1: API Configuration[/bold]")
        
        try:
            validate_api_key()
            console.print("✅ OpenAI API key is already configured and working!")
        except Exception:
            console.print("🔧 OpenAI API key needs to be configured.")
            api_key = click.prompt(
                "Enter your OpenAI API key", 
                hide_input=True,
                type=str
            )
            
            try:
                validate_api_key(api_key)
                # Save to .env file
                env_path = Path(".env")
                if env_path.exists():
                    lines = []
                    found_key = False
                    for line in env_path.read_text().splitlines():
                        if line.startswith("OPENAI_API_KEY="):
                            lines.append(f"OPENAI_API_KEY={api_key}")
                            found_key = True
                        else:
                            lines.append(line)
                    if not found_key:
                        lines.append(f"OPENAI_API_KEY={api_key}")
                    env_path.write_text("\n".join(lines))
                else:
                    env_path.write_text(f"OPENAI_API_KEY={api_key}\n")
                
                os.environ["OPENAI_API_KEY"] = api_key
                console.print("✅ API key configured and saved to .env file!")
            except Exception as e:
                console.print(f"❌ API key validation failed: {e}")
                raise click.ClickException("Setup aborted due to invalid API key")
        
        # Step 2: Choose squad profile
        console.print("\n[bold]Step 2: Choose Your Squad Profile[/bold]")
        
        profiles = {
            "mvp-team": {
                "description": "Minimal team for building MVPs",
                "agents": "PM + Engineer + Architect",
                "best_for": "Quick prototypes, simple applications"
            },
            "full-stack": {
                "description": "Complete development team",
                "agents": "PM + Engineer + Architect + QA",
                "best_for": "Production apps, comprehensive solutions"
            },
            "research-team": {
                "description": "Experimental team for prototyping",
                "agents": "PM + Engineer + QA",
                "best_for": "Research projects, proof of concepts"
            }
        }
        
        console.print("\nAvailable squad profiles:")
        for i, (name, info) in enumerate(profiles.items(), 1):
            console.print(f"{i}. [bold]{name}[/bold]")
            console.print(f"   📝 {info['description']}")
            console.print(f"   👥 Agents: {info['agents']}")
            console.print(f"   🎯 Best for: {info['best_for']}\n")
        
        profile_choice = click.prompt(
            "Select a squad profile (1-3)",
            type=click.IntRange(1, 3)
        )
        
        selected_profile = list(profiles.keys())[profile_choice - 1]
        console.print(f"✅ Selected: [bold]{selected_profile}[/bold]")
        
        # Step 3: Create first project
        console.print("\n[bold]Step 3: Create Your First Project[/bold]")
        
        project_name = click.prompt(
            "Enter project name",
            type=str,
            default="my-first-project"
        )
        
        console.print("\nExample prompts:")
        console.print("• 'Create a simple todo list web app with Flask and SQLite'")
        console.print("• 'Build a CLI tool that processes CSV files'")
        console.print("• 'Make a REST API for managing a library catalog'")
        
        project_prompt = click.prompt(
            "\nEnter your project description",
            type=str
        )
        
        # Create the project
        project_path = Path("projects") / project_name
        
        if project_path.exists():
            if not click.confirm(f"Project '{project_name}' already exists. Overwrite?"):
                raise click.ClickException("Setup cancelled")
            shutil.rmtree(project_path)
        
        # Create project structure
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "workspace").mkdir(exist_ok=True)
        (project_path / "logs").mkdir(exist_ok=True)
        
        # Write prompt file
        (project_path / "prompt.txt").write_text(project_prompt)
        
        # Create metadata
        project_info = ProjectInfo(project_path)
        metadata = {
            "created_at": datetime.now().isoformat(),
            "created_with": "autosquad-init-wizard",
            "version": "0.1.0",
            "recommended_profile": selected_profile
        }
        project_info.save_metadata(metadata)
        
        # Final summary
        console.print(Panel.fit(
            f"🎉 [bold green]Setup Complete![/bold green]\n\n"
            f"✅ API key configured\n"
            f"✅ Squad profile selected: {selected_profile}\n"
            f"✅ Project created: {project_name}\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"1. Run your first squad: [bold]autosquad run --project {project_path} --squad-profile {selected_profile}[/bold]\n"
            f"2. Check project status: [bold]autosquad project status {project_name}[/bold]\n"
            f"3. List all projects: [bold]autosquad project list[/bold]\n\n"
            f"📚 Get help anytime with: [bold]autosquad --help[/bold]",
            title="🚀 Ready to Go!",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        console.print("\n\n🛑 Setup cancelled by user")
        raise click.ClickException("")


@cli.command()
def list_profiles():
    """List available squad profiles with detailed descriptions."""
    
    console.print("[bold blue]📋 Available Squad Profiles[/bold blue]\n")
    
    try:
        from .config import load_squad_profile, get_default_squad_profiles
        
        # Get all available profiles
        try:
            # Try to load from config file first
            profiles_data = get_default_squad_profiles()
        except Exception:
            # Fallback to hardcoded profiles
            profiles_data = {
                "mvp-team": {},
                "full-stack": {},
                "research-team": {}
            }
        
        for profile_name in profiles_data.keys():
            try:
                profile = load_squad_profile(profile_name)
                console.print(f"[bold green]• {profile_name}[/bold green]")
                
                # Show agents
                agent_types = [agent.get("type", "unknown") for agent in profile.agents]
                agent_display = " + ".join(agent_types).title()
                console.print(f"  👥 [bold]Agents:[/bold] {agent_display}")
                
                # Show workflow info  
                workflow = profile.workflow
                console.print(f"  🔄 [bold]Rounds:[/bold] {workflow.get('rounds', 3)}")
                console.print(f"  🤔 [bold]Reflection:[/bold] Every {workflow.get('reflection_frequency', 2)} rounds")
                
                # Show quality gates if available
                quality_gates = workflow.get('quality_gates', [])
                if quality_gates:
                    gates_display = ", ".join(quality_gates)
                    console.print(f"  ✅ [bold]Quality Gates:[/bold] {gates_display}")
                
                # Show agent details
                console.print(f"  📝 [bold]Agent Details:[/bold]")
                for agent in profile.agents:
                    agent_type = agent.get("type", "unknown").title()
                    agent_config = agent.get("config", {})
                    focus = agent_config.get("focus", "General development")
                    if isinstance(focus, list):
                        focus = ", ".join(focus)
                    console.print(f"     • [dim]{agent_type}:[/dim] {focus}")
                
                console.print()  # Empty line between profiles
                
            except Exception as e:
                console.print(f"[bold red]• {profile_name}[/bold red]")
                console.print(f"  [red]❌ Error loading profile: {e}[/red]\n")
    
    except Exception as e:
        console.print(f"[red]❌ Error loading profiles: {e}[/red]")
        console.print("\n[yellow]Falling back to basic profile list...[/yellow]\n")
        
        # Fallback to simple hardcoded display
        profiles = {
            "mvp-team": "Minimal team for building MVPs (PM, Engineer, Architect)",
            "full-stack": "Complete development team (PM, Engineer, Architect, QA)",
            "research-team": "Experimental team for prototyping (PM, Engineer, QA)",
        }
        
        for name, description in profiles.items():
            console.print(f"• [bold]{name}[/bold]: {description}")


@cli.command()
@click.option(
    "--project", 
    "-p", 
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to project directory containing prompt.txt"
)
@click.option(
    "--squad-profile",
    "-s",
    default="mvp-team",
    type=click.Choice(['mvp-team', 'full-stack', 'research-team']),
    help="Squad profile to use"
)
def test_progress(project: Path, squad_profile: str):
    """Test the progress display system without making API calls."""
    
    console.print(Panel.fit(
        f"🧪 [bold blue]Testing Progress System[/bold blue]\n"
        f"📁 Project: {project}\n"
        f"👥 Squad: {squad_profile}",
        title="AutoSquad Debug",
        border_style="yellow"
    ))
    
    try:
        # Use the execution engine in test mode
        asyncio.run(run_squad(
            project_path=project,
            squad_profile=squad_profile,
            rounds=1,  # Just one round for testing
            model="gpt-4o-mini",
            reflect=False,
            verbose=True,
            show_live_progress=True,
            debug_mode=True,
            max_messages=0  # No API calls
        ))
        
        console.print("✅ Progress system test completed!")
        
    except KeyboardInterrupt:
        console.print("\n🛑 Test interrupted by user")
    except Exception as e:
        console.print(f"❌ Test failed: {e}")
        if console.is_terminal:
            console.print_exception()


@cli.command()
def create_profile():
    """Create a custom squad profile interactively."""
    
    console.print(Panel.fit(
        "🧩 [bold blue]Create Custom Squad Profile[/bold blue]\n"
        "Design your own agent team for specialized projects.",
        title="Profile Creator",
        border_style="blue"
    ))
    
    try:
        from .config import get_config_dir, create_default_configs
        import yaml
        
        # Ensure config directory exists
        create_default_configs()
        
        # Step 1: Basic profile info
        console.print("\n[bold]Step 1: Profile Information[/bold]")
        profile_name = click.prompt("Profile name (lowercase, no spaces)", type=str)
        profile_name = profile_name.lower().replace(" ", "-")
        
        description = click.prompt("Brief description", type=str)
        
        # Step 2: Agent configuration
        console.print("\n[bold]Step 2: Agent Configuration[/bold]")
        console.print("Available agent types: pm, engineer, architect, qa")
        
        agents = []
        while True:
            console.print(f"\n[dim]Currently configured agents: {len(agents)}[/dim]")
            
            agent_type = click.prompt(
                "Add agent type (pm/engineer/architect/qa) or 'done' to finish",
                type=str
            ).lower()
            
            if agent_type == "done":
                break
                
            if agent_type not in ["pm", "engineer", "architect", "qa"]:
                console.print("[red]❌ Invalid agent type. Use: pm, engineer, architect, qa[/red]")
                continue
            
            console.print(f"\n[bold]Configuring {agent_type.title()} Agent[/bold]")
            
            # Agent-specific configuration
            agent_config = {"type": agent_type, "config": {}}
            
            if agent_type == "pm":
                focus = click.prompt("Focus area", default="product management", type=str)
                risk_tolerance = click.prompt("Risk tolerance (low/medium/high)", default="medium", type=str)
                agent_config["config"] = {"focus": focus, "risk_tolerance": risk_tolerance}
                
            elif agent_type == "engineer":
                languages = click.prompt("Programming languages (comma-separated)", default="python", type=str)
                frameworks = click.prompt("Frameworks (comma-separated)", default="flask", type=str)
                focus = click.prompt("Engineering focus", default="rapid prototyping", type=str)
                agent_config["config"] = {
                    "languages": [lang.strip() for lang in languages.split(",")],
                    "frameworks": [fw.strip() for fw in frameworks.split(",")],
                    "focus": focus
                }
                
            elif agent_type == "architect":
                focus_areas = click.prompt("Architecture focus areas (comma-separated)", default="maintainability,scalability", type=str)
                review_style = click.prompt("Review style (pragmatic/thorough)", default="pragmatic", type=str)
                agent_config["config"] = {
                    "focus": [area.strip() for area in focus_areas.split(",")],
                    "review_style": review_style
                }
                
            elif agent_type == "qa":
                focus_areas = click.prompt("QA focus areas (comma-separated)", default="testing,quality", type=str)
                testing_types = click.prompt("Testing types (comma-separated)", default="unit,integration", type=str)
                agent_config["config"] = {
                    "focus": [area.strip() for area in focus_areas.split(",")],
                    "testing_types": [test.strip() for test in testing_types.split(",")]
                }
            
            agents.append(agent_config)
            console.print(f"✅ Added {agent_type.title()} agent")
        
        if not agents:
            console.print("[red]❌ Profile must have at least one agent[/red]")
            raise click.ClickException("Profile creation cancelled")
        
        # Step 3: Workflow configuration
        console.print("\n[bold]Step 3: Workflow Configuration[/bold]")
        
        rounds = click.prompt("Number of development rounds", default=3, type=int)
        reflection_freq = click.prompt("Reflection frequency (every N rounds)", default=2, type=int)
        
        # Quality gates based on agents
        available_gates = []
        if any(a["type"] == "architect" for a in agents):
            available_gates.append("code_review")
        if any(a["type"] == "qa" for a in agents):
            available_gates.extend(["basic_testing", "comprehensive_testing"])
        
        quality_gates = []
        if available_gates:
            console.print(f"Available quality gates: {', '.join(available_gates)}")
            gates_input = click.prompt(
                "Quality gates (comma-separated, or 'all' for all available)", 
                default="all", 
                type=str
            )
            if gates_input.lower() == "all":
                quality_gates = available_gates
            else:
                quality_gates = [gate.strip() for gate in gates_input.split(",") if gate.strip() in available_gates]
        
        # Step 4: Create the profile
        profile_config = {
            "description": description,
            "agents": agents,
            "workflow": {
                "rounds": rounds,
                "reflection_frequency": reflection_freq,
                "quality_gates": quality_gates
            }
        }
        
        # Load existing profiles and add new one
        config_dir = get_config_dir()
        profiles_path = config_dir / "squad_profiles.yaml"
        
        if profiles_path.exists():
            with open(profiles_path, 'r') as f:
                profiles_data = yaml.safe_load(f) or {"profiles": {}}
        else:
            from .config import get_default_squad_profiles
            profiles_data = {"profiles": get_default_squad_profiles()}
        
        profiles_data["profiles"][profile_name] = profile_config
        
        # Save updated profiles
        with open(profiles_path, 'w') as f:
            yaml.dump(profiles_data, f, default_flow_style=False, indent=2)
        
        # Show summary
        agent_types_display = " + ".join([a["type"].title() for a in agents])
        console.print(Panel.fit(
            f"✅ [bold green]Profile '{profile_name}' created successfully![/bold green]\n\n"
            f"📝 Description: {description}\n"
            f"👥 Agents: {agent_types_display}\n"
            f"🔄 Rounds: {rounds}\n"
            f"🤔 Reflection: Every {reflection_freq} rounds\n"
            f"✅ Quality Gates: {', '.join(quality_gates) if quality_gates else 'None'}\n\n"
            f"[bold]Usage:[/bold] autosquad run --project <path> --squad-profile {profile_name}",
            title="Profile Created",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        console.print("\n\n🛑 Profile creation cancelled")
        raise click.ClickException("")
    except Exception as e:
        console.print(f"[red]❌ Error creating profile: {e}[/red]")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()


def main():
    """Entry point for the console script."""
    cli() 