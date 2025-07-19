"""
AutoSquad CLI - Command-line interface for running autonomous development squads
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from .orchestrator import SquadOrchestrator
from .project_manager import ProjectManager
from .config import load_config, load_squad_profile

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """AutoSquad - Autonomous Multi-Agent Development Framework
    
    Spin up AI development teams to build software from simple prompts.
    """
    pass


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
    help="Squad profile to use (mvp-team, full-stack, research-team)"
)
@click.option(
    "--rounds",
    "-r",
    default=3,
    type=int,
    help="Number of development rounds to run"
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
    """Run an autonomous development squad on a project."""
    
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
        # Run the async squad orchestration
        asyncio.run(_run_squad(
            project, squad_profile, rounds, model, reflect, verbose, not no_live_display, debug_mode, max_messages
        ))
        
        console.print(Panel.fit(
            "✅ [bold green]Squad completed successfully![/bold green]\n"
            f"📂 Check {project}/workspace/ for generated code\n"
            f"📝 Check {project}/logs/ for conversation logs",
            title="Success",
            border_style="green"
        ))
        
    except Exception as e:
        error_msg = str(e)
        
        # Check if this is one of our friendly formatted error messages
        if error_msg.startswith("🚫") or "OpenAI API" in error_msg:
            # Display friendly error messages with better formatting
            console.print(Panel(
                error_msg,
                title="❌ API Error",
                border_style="red",
                expand=True
            ))
        else:
            # Display standard error message
            console.print(Panel.fit(
                f"❌ [bold red]Squad failed:[/bold red] {error_msg}",
                title="Error",
                border_style="red"
            ))
        
        if verbose:
            console.print_exception()
        raise click.ClickException(str(e))


async def _run_squad(
    project_path: Path,
    squad_profile: str,
    rounds: int,
    model: str,
    reflect: bool,
    verbose: bool,
    show_live_progress: bool,
    debug_mode: bool,
    max_messages: int
):
    """Internal async function to run the squad."""
    
    # Enable debug logging if in debug mode
    if debug_mode:
        console.print("[yellow]🐛 DEBUG MODE ENABLED[/yellow]")
        console.print(f"[dim]- Limited to {max_messages or 10} messages per round[/dim]")
        console.print(f"[dim]- Verbose logging enabled[/dim]")
        console.print(f"[dim]- Live progress: {show_live_progress}[/dim]")
        verbose = True  # Force verbose in debug mode
    
    # Initialize project manager
    project_manager = ProjectManager(project_path)
    
    if debug_mode:
        console.print("🔍 [DEBUG] Initializing project manager...")
    
    # Load project prompt
    if not show_live_progress:
        # Use simple progress display for no-live-display mode
        from rich.progress import Progress, SpinnerColumn, TextColumn
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task1 = progress.add_task("Loading project...", total=None)
            await project_manager.initialize()
            progress.update(task1, completed=True)
            
            # Load configuration
            task2 = progress.add_task("Loading configuration...", total=None)
            config = load_config()
            profile = load_squad_profile(squad_profile)
            progress.update(task2, completed=True)
            
            # Initialize orchestrator
            task3 = progress.add_task("Creating squad...", total=None)
            orchestrator = SquadOrchestrator(
                project_manager=project_manager,
                config=config,
                squad_profile=profile,
                model=model,
                verbose=verbose,
                show_live_progress=False,
                debug_mode=debug_mode,
                max_messages=max_messages
            )
            progress.update(task3, completed=True)
            
            # Run development cycles
            task4 = progress.add_task(f"Running {rounds} development rounds...", total=rounds)
            for round_num in range(rounds):
                console.print(f"\n🔄 [bold yellow]Round {round_num + 1}/{rounds}[/bold yellow]")
                await orchestrator.run_round(round_num + 1, reflect=reflect)
                progress.update(task4, advance=1)
    else:
        # Use live progress display
        console.print(f"\n[dim]Initializing AutoSquad...{' (DEBUG MODE)' if debug_mode else ''}[/dim]")
        
        # Initialize components
        await project_manager.initialize()
        
        if debug_mode:
            console.print("🔍 [DEBUG] Project manager initialized")
            
        config = load_config()
        profile = load_squad_profile(squad_profile)
        
        if debug_mode:
            console.print(f"🔍 [DEBUG] Loaded config and profile: {squad_profile}")
        
        # Initialize orchestrator with live progress
        orchestrator = SquadOrchestrator(
            project_manager=project_manager,
            config=config,
            squad_profile=profile,
            model=model,
            verbose=verbose,
            show_live_progress=True,
            debug_mode=debug_mode,
            max_messages=max_messages
        )
        
        if debug_mode:
            console.print("🔍 [DEBUG] Squad orchestrator created")
        
        # Set up project info in progress display
        progress_display = orchestrator.get_progress_display()
        if progress_display:
            progress_display.update_project_info(project_path.name)
            progress_display.update_round_info(1, rounds)
            
            if debug_mode:
                console.print("🔍 [DEBUG] Progress display configured")
        
        # Start live display in background
        live_display_task = None
        if progress_display:
            try:
                if debug_mode:
                    console.print("🔍 [DEBUG] Starting live display task...")
                    
                live_display_task = asyncio.create_task(progress_display.start_live_display())
                # Give the display a moment to initialize
                await asyncio.sleep(1)
                
                if debug_mode:
                    console.print("🔍 [DEBUG] Live display task started")
                    
            except Exception as e:
                console.print(f"[yellow]Warning: Could not start live display: {e}[/yellow]")
                if debug_mode:
                    console.print(f"🔍 [DEBUG] Live display error details: {type(e).__name__}: {e}")
                console.print("[yellow]Continuing with basic progress logging...[/yellow]")
                progress_display = None
                live_display_task = None
        
        try:
            # Run development cycles with live progress
            for round_num in range(rounds):
                if progress_display:
                    await orchestrator.run_round(round_num + 1, reflect=reflect)
                else:
                    # Basic progress logging when live display is not available
                    console.print(f"\n🔄 [bold yellow]Starting Round {round_num + 1}/{rounds}[/bold yellow]")
                    await orchestrator.run_round(round_num + 1, reflect=reflect)
                    console.print(f"✅ [bold green]Round {round_num + 1} completed[/bold green]")
                
                # Small delay between rounds to let progress display update
                if round_num < rounds - 1:
                    await asyncio.sleep(1)
            
        finally:
            # Stop live display
            if progress_display:
                progress_display.stop_live_display()
                
            # Wait for display task to complete
            if live_display_task:
                try:
                    await asyncio.wait_for(live_display_task, timeout=2.0)
                except asyncio.TimeoutError:
                    live_display_task.cancel()
                    try:
                        await live_display_task
                    except asyncio.CancelledError:
                        pass  # Expected when cancelling
            
            # Show final summary
            if progress_display:
                console.print("\n")
                console.print(progress_display.display_summary())
                
                # Show token usage summary
                final_summary = await orchestrator.get_final_summary()
                if "token_usage" in final_summary:
                    token_info = final_summary["token_usage"]
                    console.print(Panel.fit(
                        f"💰 [bold]Token Usage Summary[/bold]\n"
                        f"Total Tokens: {token_info['total_tokens_used']:,}\n"
                        f"API Calls: {token_info['api_calls_made']}\n"
                        f"Estimated Cost: ${token_info['estimated_cost_usd']:.4f}\n"
                        f"Avg Tokens/Call: {token_info['average_tokens_per_call']:,}",
                        title="💰 Cost Summary",
                        border_style="yellow"
                    ))
    
    # Cleanup
    await orchestrator.cleanup()


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
    """Create a new AutoSquad project."""
    
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


@cli.command()
def list_profiles():
    """List available squad profiles."""
    
    console.print("[bold blue]Available Squad Profiles:[/bold blue]\n")
    
    # This will read from configs/squad_profiles.yaml when implemented
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
    help="Squad profile to use (mvp-team, full-stack, research-team)"
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
    
    async def _test_progress():
        # Initialize components
        project_manager = ProjectManager(project)
        await project_manager.initialize()
        
        config = load_config()
        profile = load_squad_profile(squad_profile)
        
        # Create orchestrator with live progress
        orchestrator = SquadOrchestrator(
            project_manager=project_manager,
            config=config,
            squad_profile=profile,
            model="gpt-4o-mini",
            verbose=True,
            show_live_progress=True,
            debug_mode=True,
            max_messages=0  # No API calls
        )
        
        console.print("🔍 Starting progress system test...")
        
        # Set up project info in progress display
        progress_display = orchestrator.get_progress_display()
        
        if progress_display:
            progress_display.update_project_info(project.name)
            
            # Start live display in background
            live_display_task = asyncio.create_task(progress_display.start_live_display())
            await asyncio.sleep(1)  # Let display initialize
            
            try:
                # Run the test
                await orchestrator.test_progress_system()
                
                console.print("✅ Progress system test completed!")
                console.print("Press Ctrl+C to exit...")
                
                # Keep display running for a bit
                await asyncio.sleep(15)
                
            finally:
                # Stop live display
                progress_display.stop_live_display()
                
                # Wait for display task to complete
                try:
                    await asyncio.wait_for(live_display_task, timeout=2.0)
                except asyncio.TimeoutError:
                    live_display_task.cancel()
                    try:
                        await live_display_task
                    except asyncio.CancelledError:
                        pass
        else:
            console.print("❌ No progress display available!")
            
        await orchestrator.cleanup()
    
    try:
        asyncio.run(_test_progress())
    except KeyboardInterrupt:
        console.print("\n🛑 Test interrupted by user")
    except Exception as e:
        console.print(f"❌ Test failed: {e}")
        if console.is_terminal:
            console.print_exception()


if __name__ == "__main__":
    cli()


def main():
    """Entry point for the console script."""
    cli() 