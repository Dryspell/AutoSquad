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
from rich.progress import Progress, SpinnerColumn, TextColumn

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
def run(
    project: Path,
    squad_profile: str,
    rounds: int,
    model: str,
    reflect: bool,
    verbose: bool
):
    """Run an autonomous development squad on a project."""
    
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
        asyncio.run(_run_squad(project, squad_profile, rounds, model, reflect, verbose))
        
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
    verbose: bool
):
    """Internal async function to run the squad."""
    
    # Initialize project manager
    project_manager = ProjectManager(project_path)
    
    # Load project prompt
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
            verbose=verbose
        )
        progress.update(task3, completed=True)
        
        # Run development cycles
        task4 = progress.add_task(f"Running {rounds} development rounds...", total=rounds)
        for round_num in range(rounds):
            console.print(f"\n🔄 [bold yellow]Round {round_num + 1}/{rounds}[/bold yellow]")
            await orchestrator.run_round(round_num + 1, reflect=reflect)
            progress.update(task4, advance=1)


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


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main() 