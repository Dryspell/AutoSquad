"""
Execution engine for AutoSquad operations.
Handles the refactored squad running logic with better organization.
"""

import asyncio
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import load_config, load_squad_profile
from .exceptions import AutoSquadError
from .orchestrator import SquadOrchestrator
from .project_manager import ProjectManager
from .validation import validate_all_inputs

console = Console()


class SquadExecutionEngine:
    """Handles the execution of AutoSquad operations with proper separation of concerns."""
    
    def __init__(
        self,
        project_path: Path,
        squad_profile: str,
        rounds: int,
        model: str,
        reflect: bool = True,
        verbose: bool = False,
        show_live_progress: bool = True,
        debug_mode: bool = False,
        max_messages: Optional[int] = None
    ):
        self.project_path = project_path
        self.squad_profile = squad_profile
        self.rounds = rounds
        self.model = model
        self.reflect = reflect
        self.verbose = verbose
        self.show_live_progress = show_live_progress
        self.debug_mode = debug_mode
        self.max_messages = max_messages or (10 if debug_mode else None)
        
        # Will be initialized during setup
        self.project_manager = None
        self.orchestrator = None
        self.live_display_task = None
    
    async def run(self) -> None:
        """Main execution method."""
        try:
            # Step 1: Validate inputs
            await self._validate_inputs()
            
            # Step 2: Initialize components
            await self._initialize_components()
            
            # Step 3: Setup progress display
            await self._setup_progress_display()
            
            # Step 4: Run development cycles
            await self._run_development_cycles()
            
            # Step 5: Display final summary
            await self._display_final_summary()
            
        except Exception as e:
            await self._handle_error(e)
            raise
        finally:
            await self._cleanup()
    
    async def _validate_inputs(self) -> None:
        """Validate all inputs before starting."""
        if self.debug_mode:
            console.print("[yellow]🐛 DEBUG MODE ENABLED[/yellow]")
            console.print(f"[dim]- Limited to {self.max_messages} messages per round[/dim]")
            console.print(f"[dim]- Verbose logging enabled[/dim]")
            console.print(f"[dim]- Live progress: {self.show_live_progress}[/dim]")
        
        # Use our validation module
        validate_all_inputs(
            self.project_path,
            self.squad_profile,
            self.model
        )
    
    async def _initialize_components(self) -> None:
        """Initialize project manager and other core components."""
        if self.debug_mode:
            console.print("🔍 [DEBUG] Initializing components...")
        
        # Initialize project manager
        self.project_manager = ProjectManager(self.project_path)
        await self.project_manager.initialize()
        
        if self.debug_mode:
            console.print("🔍 [DEBUG] Project manager initialized")
        
        # Load configuration
        config = load_config()
        profile = load_squad_profile(self.squad_profile)
        
        if self.debug_mode:
            console.print(f"🔍 [DEBUG] Loaded config and profile: {self.squad_profile}")
        
        # Initialize orchestrator
        self.orchestrator = SquadOrchestrator(
            project_manager=self.project_manager,
            config=config,
            squad_profile=profile,
            model=self.model,
            verbose=self.verbose or self.debug_mode,  # Force verbose in debug mode
            show_live_progress=self.show_live_progress,
            debug_mode=self.debug_mode,
            max_messages=self.max_messages
        )
        
        if self.debug_mode:
            console.print("🔍 [DEBUG] Squad orchestrator created")
    
    async def _setup_progress_display(self) -> None:
        """Setup progress display based on mode."""
        if not self.show_live_progress:
            # Will use simple progress display during execution
            return
        
        # Setup live progress display
        progress_display = self.orchestrator.get_progress_display()
        if progress_display:
            progress_display.update_project_info(self.project_path.name)
            progress_display.update_round_info(1, self.rounds)
            
            if self.debug_mode:
                console.print("🔍 [DEBUG] Progress display configured")
            
            # Start live display in background
            try:
                if self.debug_mode:
                    console.print("🔍 [DEBUG] Starting live display task...")
                
                self.live_display_task = asyncio.create_task(
                    progress_display.start_live_display()
                )
                # Give the display a moment to initialize
                await asyncio.sleep(1)
                
                if self.debug_mode:
                    console.print("🔍 [DEBUG] Live display task started")
            
            except Exception as e:
                console.print(f"[yellow]Warning: Could not start live display: {e}[/yellow]")
                if self.debug_mode:
                    console.print(f"🔍 [DEBUG] Live display error: {type(e).__name__}: {e}")
                console.print("[yellow]Continuing with basic progress logging...[/yellow]")
                self.live_display_task = None
    
    async def _run_development_cycles(self) -> None:
        """Run the development cycles based on progress display mode."""
        if self.show_live_progress:
            await self._run_with_live_progress()
        else:
            await self._run_with_basic_progress()
    
    async def _run_with_live_progress(self) -> None:
        """Run development cycles with live progress display."""
        try:
            for round_num in range(self.rounds):
                progress_display = self.orchestrator.get_progress_display()
                
                if progress_display:
                    await self.orchestrator.run_round(round_num + 1, reflect=self.reflect)
                else:
                    # Fallback to basic progress logging
                    console.print(f"\n🔄 [bold yellow]Starting Round {round_num + 1}/{self.rounds}[/bold yellow]")
                    await self.orchestrator.run_round(round_num + 1, reflect=self.reflect)
                    console.print(f"✅ [bold green]Round {round_num + 1} completed[/bold green]")
                
                # Small delay between rounds
                if round_num < self.rounds - 1:
                    await asyncio.sleep(1)
        
        finally:
            await self._stop_live_display()
    
    async def _run_with_basic_progress(self) -> None:
        """Run development cycles with basic progress display."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Run development cycles
            task = progress.add_task(f"Running {self.rounds} development rounds...", total=self.rounds)
            
            for round_num in range(self.rounds):
                console.print(f"\n🔄 [bold yellow]Round {round_num + 1}/{self.rounds}[/bold yellow]")
                await self.orchestrator.run_round(round_num + 1, reflect=self.reflect)
                progress.update(task, advance=1)
    
    async def _stop_live_display(self) -> None:
        """Stop the live progress display."""
        if self.live_display_task and self.orchestrator:
            progress_display = self.orchestrator.get_progress_display()
            if progress_display:
                progress_display.stop_live_display()
            
            # Wait for display task to complete
            try:
                await asyncio.wait_for(self.live_display_task, timeout=2.0)
            except asyncio.TimeoutError:
                self.live_display_task.cancel()
                try:
                    await self.live_display_task
                except asyncio.CancelledError:
                    pass  # Expected when cancelling
    
    async def _display_final_summary(self) -> None:
        """Display final summary and token usage."""
        if not self.orchestrator:
            return
        
        progress_display = self.orchestrator.get_progress_display()
        if progress_display:
            console.print("\n")
            console.print(progress_display.display_summary())
        
        # Show token usage summary
        try:
            final_summary = await self.orchestrator.get_final_summary()
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
        except Exception as e:
            if self.debug_mode:
                console.print(f"[yellow]Warning: Could not display token summary: {e}[/yellow]")
    
    async def _handle_error(self, error: Exception) -> None:
        """Handle errors with appropriate formatting."""
        if isinstance(error, AutoSquadError):
            # Our custom errors already have good formatting
            console.print(Panel(
                str(error),
                title="❌ AutoSquad Error",
                border_style="red",
                expand=True
            ))
        else:
            # Standard error handling
            error_msg = str(error)
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
    
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        await self._stop_live_display()
        
        if self.orchestrator:
            await self.orchestrator.cleanup()


# Convenience function for the CLI
async def run_squad(
    project_path: Path,
    squad_profile: str,
    rounds: int,
    model: str,
    reflect: bool = True,
    verbose: bool = False,
    show_live_progress: bool = True,
    debug_mode: bool = False,
    max_messages: Optional[int] = None
) -> None:
    """
    Run an AutoSquad development session.
    
    This is the main entry point that replaces the old _run_squad function.
    """
    engine = SquadExecutionEngine(
        project_path=project_path,
        squad_profile=squad_profile,
        rounds=rounds,
        model=model,
        reflect=reflect,
        verbose=verbose,
        show_live_progress=show_live_progress,
        debug_mode=debug_mode,
        max_messages=max_messages
    )
    
    await engine.run() 