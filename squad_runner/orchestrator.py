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
        show_live_progress: bool = True,
        debug_mode: bool = False,
        max_messages: Optional[int] = None
    ):
        self.project_manager = project_manager
        self.config = config
        self.squad_profile = squad_profile
        self.model = model
        self.verbose = verbose
        self.show_live_progress = show_live_progress
        self.debug_mode = debug_mode
        self.max_messages = max_messages or (10 if debug_mode else None)
        
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
            
        if self.debug_mode and self.verbose:
            print(f"[DEBUG] SquadOrchestrator initialized with max_messages: {self.max_messages}")
    
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
        
        if self.debug_mode and self.verbose:
            print(f"[DEBUG] Creating {len(self.squad_profile.agents)} agents...")
        
        for agent_config in self.squad_profile.agents:
            agent_type = agent_config["type"]
            agent_settings = agent_config.get("config", {})
            
            if self.debug_mode and self.verbose:
                print(f"[DEBUG] Creating {agent_type} agent...")
            
            agent = await create_agent(
                agent_type=agent_type,
                model_client=self.model_client,
                project_context=project_context,
                agent_settings=agent_settings,
                project_manager=self.project_manager
            )
            
            # Set up progress callbacks for the agent
            if self.progress_display and hasattr(agent, 'set_progress_callback'):
                def create_callback(agent_name):
                    def callback(event_type, *args):
                        if self.debug_mode and self.verbose:
                            print(f"[DEBUG] Progress callback: {agent_name} -> {event_type}: {args}")
                        
                        if event_type == "agent_action_started":
                            self.progress_display.agent_started_action(agent_name, args[0])
                        elif event_type == "agent_action_completed":
                            self.progress_display.agent_completed_action(agent_name, args[0] if args else "")
                        elif event_type == "file_operation":
                            if len(args) >= 2:
                                self.progress_display.agent_file_operation(agent_name, args[0], args[1])
                    return callback
                
                agent.set_progress_callback(create_callback(agent.name))
                
                if self.debug_mode and self.verbose:
                    print(f"[DEBUG] Progress callback set for {agent.name}")
            
            self.agents.append(agent)
            
            # Register agent with progress display
            if self.progress_display:
                self.progress_display.register_agent(agent.name, agent_type)
                
                if self.debug_mode and self.verbose:
                    print(f"[DEBUG] Agent {agent.name} registered with progress display")
            
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
    
    async def _run_monitored_group_chat(self, round_prompt: str, round_num: int):
        """Run group chat with progress monitoring."""
        if self.progress_display:
            self.progress_display.agent_started_action("System", f"Starting agent collaboration")
        
        # Start a background task to provide periodic updates
        monitor_task = None
        if self.progress_display:
            monitor_task = asyncio.create_task(self._monitor_chat_progress(round_num))
        
        try:
            # Run the actual group chat
            result = await self.group_chat.run(
                task=round_prompt
                # Note: v0.4 API parameters may be different
            )
            return result
        finally:
            # Stop monitoring
            if monitor_task:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
    
    async def _monitor_chat_progress(self, round_num: int):
        """Periodically update progress during chat execution."""
        update_count = 0
        while True:
            await asyncio.sleep(10)  # Update every 10 seconds
            update_count += 1
            
            if self.progress_display:
                # In debug mode, simulate progressive token usage
                if self.debug_mode:
                    # Simulate gradual token accumulation
                    simulated_tokens = update_count * 200  # 200 tokens per 10-second interval
                    simulated_cost = simulated_tokens * 0.00015 / 1000  # GPT-4o-mini input rate
                    
                    self.progress_display.update_token_usage(
                        self.token_optimizer.total_tokens_used + simulated_tokens,
                        simulated_cost
                    )
                    
                    if self.verbose:
                        print(f"[DEBUG] Simulated token progress: +{simulated_tokens} tokens, ${simulated_cost:.6f}")
                else:
                    # Update with actual usage
                    usage_summary = self.token_optimizer.get_usage_summary()
                    self.progress_display.update_token_usage(
                        usage_summary["total_tokens_used"],
                        usage_summary["estimated_cost_usd"]
                    )
                
                # Update status
                self.progress_display.agent_started_action(
                    "System", 
                    f"Round {round_num} in progress... ({update_count * 10}s elapsed)"
                )
    
    async def run_round(self, round_num: int, reflect: bool = True):
        """Run a single development round."""
        if not self.group_chat:
            await self._create_group_chat()
        
        # Update progress display
        if self.progress_display:
            self.progress_display.update_round_info(round_num, self.squad_profile.rounds or 5)
        
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
            
            # In debug mode, simulate some initial token usage
            if self.debug_mode:
                initial_tokens = 300  # Simulate initial prompt tokens
                initial_cost = initial_tokens * 0.00015 / 1000  # GPT-4o-mini rate
                self.token_optimizer.track_api_call(
                    input_tokens=initial_tokens,
                    output_tokens=0,
                    cost_estimate=initial_cost
                )
                usage_summary = self.token_optimizer.get_usage_summary()
                self.progress_display.update_token_usage(
                    usage_summary["total_tokens_used"],
                    usage_summary["estimated_cost_usd"]
                )
                if self.verbose:
                    print(f"[DEBUG] Initial token simulation: {initial_tokens} tokens, ${initial_cost:.6f}")
                    
        elif self.verbose:
            print(f"Starting round {round_num} with {len(self.agents)} agents...")
            print(f"Project context: {len(project_context.get('current_files', []))} files in workspace")
        
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
                result = await self._run_monitored_group_chat(round_prompt, round_num)
                
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

ROUND {round_num} MANDATORY REQUIREMENTS:

🏗️ **NEXT.JS 15 APP ROUTER STRUCTURE (REQUIRED):**
- Use App Router NOT Pages Router
- Create `app/` directory (NOT `src/pages/`)
- Main page: `app/page.tsx` (NOT `pages/index.tsx`)
- Layout: `app/layout.tsx` (NOT `pages/_app.tsx`)
- API routes: `app/api/[route]/route.ts`

📋 **ESSENTIAL PROJECT FILES (CREATE FIRST):**
1. **package.json** - Dependencies: next@15, react@18, typescript, tailwindcss, @types/node, @types/react
2. **next.config.js** - Next.js configuration
3. **tsconfig.json** - TypeScript configuration  
4. **tailwind.config.js** - Tailwind CSS configuration
5. **postcss.config.js** - PostCSS for Tailwind

🎯 **AGENT SPECIFIC TASKS:**
1. **PM**: Create project structure and essential config files
2. **Engineer**: Build App Router pages and API routes with working TypeScript
3. **Architect**: Design proper folder structure following Next.js 15 best practices  
4. **QA**: Verify all files can actually run (`npm run dev` should work)

⚠️ **CRITICAL REQUIREMENTS:**
- NEVER use `src/pages/` structure - this is DEPRECATED
- ALWAYS use `app/` directory for App Router
- Include ALL dependencies in package.json
- Create working, runnable Next.js 15 project
- Use server components where possible
- Implement proper TypeScript types

📁 **CORRECT STRUCTURE EXAMPLE:**
```
package.json
next.config.js
tsconfig.json
tailwind.config.js
app/
  ├── layout.tsx     (root layout)
  ├── page.tsx       (homepage)
  ├── globals.css    (global styles)
  ├── components/    (reusable components)
  └── api/           (API routes)
```

START WORKING NOW - CREATE PRODUCTION-READY NEXT.JS 15 APP ROUTER PROJECT!
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
                    
                    # Check if this message indicates an action started/completed
                    content_lower = message.content.lower()
                    if any(keyword in content_lower for keyword in ['creating', 'implementing', 'building', 'writing']):
                        self.progress_display.agent_started_action(message.source, "Working on implementation")
                    elif any(keyword in content_lower for keyword in ['completed', 'finished', 'done', 'ready']):
                        self.progress_display.agent_completed_action(message.source, "Task completed")
                    
                    # Check for file operations mentioned in messages
                    if any(keyword in content_lower for keyword in ['created file', 'wrote file', 'saved file']):
                        # Try to extract filename from message
                        import re
                        file_match = re.search(r'(?:created|wrote|saved)\s+(?:file\s+)?[`"]?([^\s`"]+)[`"]?', content_lower)
                        if file_match:
                            filename = file_match.group(1)
                            self.progress_display.agent_file_operation(message.source, "create", filename)
        
        # Track token usage for this round
        round_tokens = sum(self.token_optimizer.count_message_tokens(msg) for msg in messages)
        
        # In debug mode, simulate more realistic token usage
        if self.debug_mode:
            # Simulate realistic token usage for the conversation
            estimated_tokens = len(messages) * 150  # Rough estimate per message
            round_tokens = max(round_tokens, estimated_tokens)
            
            if self.verbose:
                print(f"[DEBUG] Simulated token usage: {round_tokens} tokens for {len(messages)} messages")
        
        token_call_data = self.token_optimizer.track_api_call(
            input_tokens=int(round_tokens * 0.7),  # 70% input
            output_tokens=int(round_tokens * 0.3),  # 30% output
            cost_estimate=None
        )
        
        # Update progress display with token usage
        if self.progress_display:
            usage_summary = self.token_optimizer.get_usage_summary()
            self.progress_display.update_token_usage(
                usage_summary["total_tokens_used"],
                usage_summary["estimated_cost_usd"]
            )
            
            if self.debug_mode and self.verbose:
                print(f"[DEBUG] Updated progress display - Tokens: {usage_summary['total_tokens_used']}, Cost: ${usage_summary['estimated_cost_usd']:.6f}")
        
        # Save the conversation and workspace state
        await self.project_manager.save_round_state(round_num, messages)
        
        # Store for our own tracking
        self.conversation_history.extend(messages)
        
        if self.verbose:
            print(f"Round {round_num} completed. {len(messages)} messages exchanged. "
                  f"Token usage: {token_call_data['total_tokens']} tokens, "
                  f"Estimated cost: ${usage_summary['estimated_cost_usd']:.6f}")
    
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
            reflection_result = await self._run_monitored_group_chat(reflection_prompt, round_num)
            
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

    async def test_progress_system(self):
        """Test the progress tracking system without making API calls."""
        if not self.progress_display:
            print("[DEBUG] No progress display available for testing")
            return
            
        print("[DEBUG] Testing progress system...")
        
        # Ensure agents are created
        if not self.agents:
            await self._create_agents()
        
        # Test progress updates for each agent
        for i, agent in enumerate(self.agents):
            agent_name = agent.name
            
            print(f"[DEBUG] Testing progress for {agent_name}")
            
            # Test action started
            if self.progress_display:
                self.progress_display.agent_started_action(agent_name, f"Test action {i+1}")
                await asyncio.sleep(1)
                
                # Test file operation
                self.progress_display.agent_file_operation(agent_name, "create", f"test-file-{i+1}.txt")
                await asyncio.sleep(1)
                
                # Test action completed
                self.progress_display.agent_completed_action(agent_name, f"Test completed {i+1}")
                await asyncio.sleep(1)
        
        # Test token updates
        if self.progress_display:
            self.progress_display.update_token_usage(1500, 0.025)
            
        print("[DEBUG] Progress system test completed")
        await asyncio.sleep(3)  # Let the display show updates


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