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


class SquadOrchestrator:
    """Main orchestrator for managing AutoGen agent squads."""
    
    def __init__(
        self,
        project_manager: ProjectManager,
        config: AutoSquadConfig,
        squad_profile: SquadProfile,
        model: str,
        verbose: bool = False
    ):
        self.project_manager = project_manager
        self.config = config
        self.squad_profile = squad_profile
        self.model = model
        self.verbose = verbose
        
        # Initialize agents
        self.agents = []
        self.group_chat = None
        self.conversation_history = []
        
        # Initialize model client
        self.model_client = self._create_model_client()
    
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
                    # Extract specific error details
                    error_msg = "OpenAI API rate limit exceeded"
                    if is_quota_error:
                        error_msg = "OpenAI API quota exceeded - Please add credits to your account"
                    elif attempt >= max_retries:
                        error_msg = f"OpenAI API rate limit exceeded - Failed after {max_retries + 1} attempts"
                    
                    # Create a more helpful error message
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
                
                # Continue to next retry attempt
                continue
            
            except openai.APIError as e:
                if self.verbose:
                    print(f"⚠️ OpenAI API error in round {round_num} (attempt {attempt + 1}): {e}")
                
                # Don't retry API errors on the last attempt
                if attempt >= max_retries:
                    friendly_error = f"""
🚫 OpenAI API Error

💡 This might be a temporary issue. Please try:
   • Waiting a few minutes and retrying
   • Checking OpenAI status: https://status.openai.com/
   • Verifying your API key is valid

Original error: {str(e)}
"""
                    
                    raise RuntimeError(friendly_error) from e
                
                # Continue to next retry attempt for transient API errors
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
                    
                    # Continue to next retry attempt for transient API errors
                    continue
                
                else:
                    # Not an OpenAI error, re-raise immediately
                    if self.verbose:
                        print(f"Error in round {round_num}: {e}")
                    raise
            
            except Exception as e:
                if self.verbose:
                    print(f"Error in round {round_num}: {e}")
                raise
    
    def _create_round_prompt(
        self, 
        round_num: int, 
        project_context: Dict[str, Any], 
        workspace_summary: str
    ) -> str:
        """Create the prompt for a development round."""
        
        if round_num == 1:
            # First round - start from the project prompt
            prompt = f"""
🚀 DEVELOPMENT ROUND {round_num}

PROJECT PROMPT:
{project_context['prompt']}

WORKSPACE STATUS:
{workspace_summary}

TEAM OBJECTIVE:
This is the first development round. The PM should start by analyzing the requirements and breaking them down into actionable tasks. The Engineer should begin implementing core functionality. The Architect should provide guidance on structure and design patterns.

Each agent should contribute according to their role and coordinate with the team.
"""
        else:
            # Subsequent rounds - continue development
            prompt = f"""
🔄 DEVELOPMENT ROUND {round_num}

PROJECT PROMPT:
{project_context['prompt']}

CURRENT WORKSPACE:
{workspace_summary}

TEAM OBJECTIVE:
Continue development from the previous round. Review what has been accomplished, identify next priorities, and implement improvements. Each agent should build on the existing work and coordinate with the team.

Focus on making meaningful progress toward the project goals.
"""
        
        return prompt.strip()
    
    async def _process_round_result(self, round_num: int, result):
        """Process the result of a development round."""
        # Extract messages from the result
        messages = []
        
        if hasattr(result, 'messages'):
            for message in result.messages:
                messages.append({
                    "sender": message.source,
                    "content": message.content,
                    "timestamp": getattr(message, 'timestamp', None)
                })
        
        # Save the conversation and workspace state
        await self.project_manager.save_round_state(round_num, messages)
        
        # Store for our own tracking
        self.conversation_history.extend(messages)
        
        if self.verbose:
            print(f"Round {round_num} completed. {len(messages)} messages exchanged.")
    
    async def _run_reflection(self, round_num: int):
        """Run a reflection phase to assess progress."""
        if self.verbose:
            print(f"Running reflection after round {round_num}")
        
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
                    reflection_messages.append({
                        "sender": message.source,
                        "content": message.content,
                        "type": "reflection"
                    })
            
            # Save reflection logs
            self.project_manager.logs.log_conversation(
                round_num + 0.5,  # Use .5 to indicate reflection
                reflection_messages
            )
            
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
        
        return {
            **project_summary,
            "squad_summary": squad_summary
        }
    
    async def cleanup(self):
        """Cleanup resources."""
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