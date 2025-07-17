"""
Squad Orchestrator - Coordinates AutoGen agents for development workflows
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import openai
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import CancellationToken

from .agents import create_agent
from .config import AutoSquadConfig, SquadProfile
from .project_manager import ProjectManager
from .token_optimization import TokenOptimizer
from .progress_display import LiveProgressDisplay, create_progress_callback


class SquadOrchestrator:
    """Main orchestrator for managing AutoGen agent squads."""
    
    def __init__(
        self,
        project_manager: ProjectManager,
        config: AutoSquadConfig,
        squad_profile: SquadProfile,
        model: str,
        verbose: bool = False,
        show_live_progress: bool = True
    ):
        self.project_manager = project_manager
        self.config = config
        self.squad_profile = squad_profile
        self.model = model
        self.verbose = verbose
        self.show_live_progress = show_live_progress
        
        # Initialize agents
        self.agents = []
        self.group_chat = None
        self.conversation_history = []
        
        # Initialize model client
        self.model_client = self._create_model_client()
        
        # Initialize token optimization
        self.token_optimizer = TokenOptimizer(
            model=model,
            max_context_tokens=config.llm_config.get("max_tokens", 6000)
        )
        
        # Initialize progress display
        if show_live_progress:
            self.progress_display = LiveProgressDisplay()
            self.progress_callbacks = create_progress_callback(self.progress_display)
        else:
            self.progress_display = None
            self.progress_callbacks = {}
    
    def _create_model_client(self):
        """Create the model client for agents."""
        llm_config = self.config.llm_config
        
        return OpenAIChatCompletionClient(
            model=self.model,
            api_key=llm_config.get("api_key"),
            # Note: v0.4 API may have different parameter names
        )
    
    async def _create_agents(self):
        """Create agents based on the squad profile."""
        project_context = self.project_manager.get_project_context()
        
        for agent_config in self.squad_profile.agents:
            agent_type = agent_config["type"]
            agent_settings = agent_config.get("config", {})
            
            agent = await create_agent(
                agent_type=agent_type,
                model_client=self.model_client,
                project_context=project_context,
                agent_settings=agent_settings,
                project_manager=self.project_manager
            )
            
            self.agents.append(agent)
            
            # Register agent with progress display
            if self.progress_display:
                self.progress_display.register_agent(agent.name, agent_type)
            
            if self.verbose:
                print(f"Created {agent_type} agent: {agent.name}")
    
    async def _create_group_chat(self):
        """Create the AutoGen group chat."""
        if not self.agents:
            await self._create_agents()
        
        # Create round-robin group chat (v0.4 API)
        self.group_chat = RoundRobinGroupChat(
            self.agents  # v0.4 API may have different parameter structure
        )
        
        if self.verbose:
            print(f"Created group chat with {len(self.agents)} agents")
    
    async def run_round(self, round_num: int, reflect: bool = True):
        """Run a single development round."""
        if not self.group_chat:
            await self._create_group_chat()
        
        # Update progress display
        if self.progress_display:
            self.progress_display.update_round_info(round_num, self.squad_profile.max_rounds or 5)
        
        # Get project context for the round
        project_context = self.project_manager.get_project_context()
        workspace_summary = self.project_manager.get_workspace_summary()
        
        # Create the round prompt
        round_prompt = self._create_round_prompt(
            round_num=round_num,
            project_context=project_context,
            workspace_summary=workspace_summary
        )
        
        if self.verbose:
            print(f"Starting round {round_num} with prompt: {round_prompt[:100]}...")
        
        # Start progress tracking for this round
        if self.progress_display:
            self.progress_display.agent_started_action("System", f"Starting Round {round_num}")
        
        # Optimize conversation context before sending
        if self.conversation_history:
            optimized_history, optimization_stats = self.token_optimizer.optimize_conversation_context(
                self.conversation_history,
                system_message=round_prompt
            )
            
            if self.verbose and optimization_stats["removed_messages"] > 0:
                print(f"Token optimization: Removed {optimization_stats['removed_messages']} messages, "
                      f"saved {optimization_stats['tokens_saved']} tokens "
                      f"({optimization_stats['compression_ratio']:.1%} efficiency)")
                      
            # Update token usage display
            if self.progress_display:
                self.progress_display.update_token_usage(
                    self.token_optimizer.total_tokens_used,
                    self.token_optimizer.get_usage_summary()["estimated_cost_usd"]
                )
        
        # Run the conversation with retry logic for transient errors
        max_retries = 3
        retry_delay = 10  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    if self.verbose:
                        print(f"⏳ Retrying round {round_num} (attempt {attempt + 1}/{max_retries + 1}) after {retry_delay}s delay...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
                # Use AutoGen's group chat to run the conversation (v0.4 API)
                result = await self.group_chat.run(
                    task=round_prompt
                    # Note: v0.4 API parameters may be different
                )
                
                # Process the conversation result
                await self._process_round_result(round_num, result)
                
                # Reflection phase
                if reflect and round_num % self.squad_profile.reflection_frequency == 0:
                    await self._run_reflection(round_num)
                
                # Update progress display
                if self.progress_display:
                    self.progress_display.agent_completed_action("System", f"Round {round_num} completed")
                
                # If we get here, the round succeeded
                if attempt > 0 and self.verbose:
                    print(f"✅ Round {round_num} succeeded on attempt {attempt + 1}")
                break
            
            except openai.RateLimitError as e:
                if self.verbose:
                    print(f"⚠️ OpenAI rate limit error in round {round_num} (attempt {attempt + 1}): {e}")
                
                # Check if this is the last attempt or if it's a quota error (not retryable)
                is_quota_error = False
                if hasattr(e, 'response') and e.response:
                    try:
                        error_data = e.response.json() if hasattr(e.response, 'json') else {}
                        if 'error' in error_data:
                            error_type = error_data['error'].get('type', 'rate_limit')
                            is_quota_error = error_type == 'insufficient_quota'
                    except:
                        pass
                
                # Don't retry quota errors or if this is the last attempt
                if is_quota_error or attempt >= max_retries:
                    # Create a more helpful error message
                    if is_quota_error:
                        error_msg = "OpenAI API quota exceeded - Please add credits to your account"
                    else:
                        error_msg = f"OpenAI API rate limit exceeded - Failed after {max_retries + 1} attempts"
                    
                    friendly_error = f"""
🚫 {error_msg}

💡 To resolve this issue:
   • Check your OpenAI billing: https://platform.openai.com/settings/organization/billing
   • Add credits to your account if quota is exceeded
   • Wait a few minutes if hitting rate limits
   • Consider upgrading your plan for higher limits

Original error: {str(e)}
"""
                    
                    raise RuntimeError(friendly_error) from e
                
                # Continue to next retry attempt for retryable rate limits
                continue
            
            except RuntimeError as e:
                # Check if this is a wrapped OpenAI error from AutoGen
                error_str = str(e)
                if "RateLimitError" in error_str:
                    if self.verbose:
                        print(f"⚠️ OpenAI rate limit error in round {round_num} (attempt {attempt + 1}): {error_str}")
                    
                    # Check if this is a quota error (not retryable)
                    is_quota_error = "insufficient_quota" in error_str
                    
                    # Don't retry quota errors or if this is the last attempt
                    if is_quota_error or attempt >= max_retries:
                        # Create a more helpful error message
                        if is_quota_error:
                            error_msg = "OpenAI API quota exceeded - Please add credits to your account"
                        else:
                            error_msg = f"OpenAI API rate limit exceeded - Failed after {max_retries + 1} attempts"
                        
                        friendly_error = f"""
🚫 {error_msg}

💡 To resolve this issue:
   • Check your OpenAI billing: https://platform.openai.com/settings/organization/billing
   • Add credits to your account if quota is exceeded
   • Wait a few minutes if hitting rate limits
   • Consider upgrading your plan for higher limits

Original error: {error_str}
"""
                        
                        raise RuntimeError(friendly_error) from e
                    
                    # Continue to next retry attempt for retryable rate limits
                    continue
                
                elif "APIError" in error_str or "openai" in error_str.lower():
                    if self.verbose:
                        print(f"⚠️ OpenAI API error in round {round_num} (attempt {attempt + 1}): {error_str}")
                    
                    # Don't retry API errors on the last attempt
                    if attempt >= max_retries:
                        friendly_error = f"""
🚫 OpenAI API Error

💡 This might be a temporary issue. Please try:
   • Waiting a few minutes and retrying
   • Checking OpenAI status: https://status.openai.com/
   • Verifying your API key is valid

Original error: {error_str}
"""
                        
                        raise RuntimeError(friendly_error) from e
                    
                    # Continue to next retry attempt
                    continue
                
                # Re-raise non-OpenAI errors immediately
                raise
            
            except Exception as e:
                # Handle other unexpected errors
                if self.verbose:
                    print(f"⚠️ Unexpected error in round {round_num} (attempt {attempt + 1}): {e}")
                
                # Don't retry unexpected errors on the last attempt
                if attempt >= max_retries:
                    raise
                
                # Continue to next retry attempt for other errors
                continue
    
    def _create_round_prompt(self, round_num: int, project_context: Dict[str, Any], workspace_summary: str) -> str:
        """Create the prompt for a development round."""
        base_prompt = f"""
🚀 AutoSquad Development Round {round_num}

PROJECT OBJECTIVE:
{project_context.get('prompt', 'No prompt specified')}

CURRENT WORKSPACE STATE:
{workspace_summary}

ROUND INSTRUCTIONS:
This is round {round_num} of the development process. Each agent should:

1. **PM**: Review progress and guide next priorities
2. **Engineer**: Implement features and write code  
3. **Architect**: Review structure and suggest improvements
4. **QA**: Test functionality and identify issues

COLLABORATION GUIDELINES:
- Build upon previous work done in earlier rounds
- Coordinate to avoid conflicts and duplicate work
- Use function calls to actually modify workspace files
- Communicate clearly about what you're working on
- Focus on making measurable progress toward the project goal

Let's collaborate to move this project forward!
"""
        
        # Add conversation summary if we have history
        if self.conversation_history:
            summary = self.token_optimizer.create_conversation_summary(self.conversation_history)
            if summary and summary != "No significant activity":
                base_prompt += f"\n\nPREVIOUS PROGRESS SUMMARY:\n{summary}\n"
        
        return base_prompt
    
    async def _process_round_result(self, round_num: int, result):
        """Process the result of a development round."""
        # Extract messages from the result
        messages = []
        
        if hasattr(result, 'messages'):
            for message in result.messages:
                msg_data = {
                    "sender": message.source,
                    "content": message.content,
                    "timestamp": getattr(message, 'timestamp', None)
                }
                messages.append(msg_data)
                
                # Update progress display with each message
                if self.progress_display:
                    self.progress_display.agent_sent_message(message.source, message.content)
        
        # Track token usage for this round
        round_tokens = sum(self.token_optimizer.count_message_tokens(msg) for msg in messages)
        token_call_data = self.token_optimizer.track_api_call(
            input_tokens=round_tokens,
            output_tokens=round_tokens // 2,  # Rough estimate
            cost_estimate=None
        )
        
        # Update progress display with token usage
        if self.progress_display:
            usage_summary = self.token_optimizer.get_usage_summary()
            self.progress_display.update_token_usage(
                usage_summary["total_tokens_used"],
                usage_summary["estimated_cost_usd"]
            )
        
        # Save the conversation and workspace state
        await self.project_manager.save_round_state(round_num, messages)
        
        # Store for our own tracking
        self.conversation_history.extend(messages)
        
        if self.verbose:
            print(f"Round {round_num} completed. {len(messages)} messages exchanged. "
                  f"Token usage: {token_call_data['total_tokens']} tokens")
    
    async def _run_reflection(self, round_num: int):
        """Run a reflection phase to assess progress."""
        if self.verbose:
            print(f"Running reflection after round {round_num}")
        
        if self.progress_display:
            self.progress_display.agent_started_action("System", f"Reflection phase")
        
        # Create reflection prompt
        workspace_summary = self.project_manager.get_workspace_summary()
        reflection_prompt = f"""
🤔 REFLECTION PHASE - After Round {round_num}

CURRENT WORKSPACE:
{workspace_summary}

REFLECTION QUESTIONS:
1. What progress have we made toward the project goals?
2. What challenges or blockers have we encountered?
3. What should be our priorities for the next round?
4. Are there any issues with code quality, architecture, or user experience?
5. What improvements or changes should we make?

Each agent should reflect on the work from their perspective and suggest improvements for the next round.
"""
        
        try:
            # Run reflection conversation
            reflection_result = await self.group_chat.run(
                task=reflection_prompt,
                cancellation_token=CancellationToken()
            )
            
            # Log reflection results
            reflection_messages = []
            if hasattr(reflection_result, 'messages'):
                for message in reflection_result.messages:
                    msg_data = {
                        "sender": message.source,
                        "content": message.content,
                        "type": "reflection"
                    }
                    reflection_messages.append(msg_data)
                    
                    # Update progress display
                    if self.progress_display:
                        self.progress_display.agent_sent_message(
                            message.source, 
                            f"[REFLECTION] {message.content}"
                        )
            
            # Save reflection logs
            self.project_manager.logs.log_conversation(
                round_num + 0.5,  # Use .5 to indicate reflection
                reflection_messages
            )
            
            if self.progress_display:
                self.progress_display.agent_completed_action("System", f"Reflection complete")
            
        except Exception as e:
            if self.verbose:
                print(f"Error during reflection: {e}")
            # Continue even if reflection fails
    
    async def get_final_summary(self) -> Dict[str, Any]:
        """Get a final summary of the development session."""
        project_summary = self.project_manager.create_project_summary()
        
        # Add squad-specific information
        squad_summary = {
            "squad_profile": self.squad_profile.profile,
            "agents_used": [agent.name for agent in self.agents],
            "total_messages": len(self.conversation_history),
            "model_used": self.model
        }
        
        # Add token optimization summary
        token_summary = self.token_optimizer.get_usage_summary()
        
        return {
            **project_summary,
            "squad_summary": squad_summary,
            "token_usage": token_summary
        }
    
    def get_progress_display(self) -> Optional[LiveProgressDisplay]:
        """Get the progress display instance."""
        return self.progress_display
    
    async def cleanup(self):
        """Cleanup resources."""
        # Stop progress display
        if self.progress_display:
            self.progress_display.stop_live_display()
        
        # Close model client if needed
        if hasattr(self.model_client, 'close'):
            await self.model_client.close()
        
        if self.verbose:
            print("Squad orchestrator cleanup completed")


# Utility function for creating orchestrators
async def create_squad_orchestrator(
    project_path: str,
    squad_profile: str = "mvp-team",
    model: str = "gpt-4",
    verbose: bool = False
) -> SquadOrchestrator:
    """Factory function to create a squad orchestrator."""
    from pathlib import Path
    from .config import load_config, load_squad_profile
    
    # Initialize project manager
    project_manager = ProjectManager(Path(project_path))
    await project_manager.initialize()
    
    # Load configuration
    config = load_config()
    profile = load_squad_profile(squad_profile)
    
    # Create orchestrator
    orchestrator = SquadOrchestrator(
        project_manager=project_manager,
        config=config,
        squad_profile=profile,
        model=model,
        verbose=verbose
    )
    
    return orchestrator 