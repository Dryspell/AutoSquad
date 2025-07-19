"""
Token optimization utilities for AutoSquad - minimize OpenAI API token usage
"""

import tiktoken
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json


class TokenOptimizer:
    """Manages conversation context and token usage to minimize API costs."""
    
    def __init__(self, model: str = "gpt-4", max_context_tokens: int = 6000):
        self.model = model
        self.max_context_tokens = max_context_tokens
        self.encoding = tiktoken.encoding_for_model(model.replace("gpt-4", "gpt-4-0613"))  # Handle model variants
        self.conversation_memory = []
        self.total_tokens_used = 0
        self.api_calls_made = 0
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.encoding.encode(text))
    
    def count_message_tokens(self, message: Dict[str, Any]) -> int:
        """Count tokens in a message object."""
        # Basic token counting for message structure
        tokens = 4  # Base tokens for message structure
        
        if "content" in message:
            tokens += self.count_tokens(str(message["content"]))
        if "role" in message:
            tokens += self.count_tokens(str(message["role"]))
        if "name" in message:
            tokens += self.count_tokens(str(message["name"]))
            
        return tokens
    
    def optimize_conversation_context(self, messages: List[Dict[str, Any]], 
                                    system_message: str = "") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Optimize conversation context to fit within token limits.
        Returns (optimized_messages, optimization_stats)
        """
        # Count system message tokens
        system_tokens = self.count_tokens(system_message) if system_message else 0
        available_tokens = self.max_context_tokens - system_tokens - 500  # Reserve for response
        
        if not messages:
            return [], {"removed_messages": 0, "tokens_saved": 0, "compression_ratio": 1.0}
        
        # Start with the most recent messages and work backwards
        optimized_messages = []
        current_tokens = 0
        original_tokens = sum(self.count_message_tokens(msg) for msg in messages)
        
        # Always keep the last few messages for immediate context
        recent_messages = messages[-3:] if len(messages) > 3 else messages
        
        for message in reversed(recent_messages):
            msg_tokens = self.count_message_tokens(message)
            if current_tokens + msg_tokens <= available_tokens:
                optimized_messages.insert(0, message)
                current_tokens += msg_tokens
            else:
                break
        
        # If we have room, add more messages from earlier in the conversation
        if len(optimized_messages) < len(messages) and current_tokens < available_tokens * 0.8:
            older_messages = messages[:-3] if len(messages) > 3 else []
            
            for message in reversed(older_messages):
                msg_tokens = self.count_message_tokens(message)
                if current_tokens + msg_tokens <= available_tokens:
                    optimized_messages.insert(0, message)
                    current_tokens += msg_tokens
                else:
                    break
        
        # Calculate optimization stats
        removed_count = len(messages) - len(optimized_messages)
        tokens_saved = original_tokens - current_tokens
        compression_ratio = current_tokens / original_tokens if original_tokens > 0 else 1.0
        
        optimization_stats = {
            "removed_messages": removed_count,
            "tokens_saved": tokens_saved,
            "compression_ratio": compression_ratio,
            "final_token_count": current_tokens,
            "original_token_count": original_tokens
        }
        
        return optimized_messages, optimization_stats
    
    def create_conversation_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Create a concise summary of a conversation for context compression."""
        if not messages:
            return ""
        
        # Extract key information from messages
        agents_mentioned = set()
        key_actions = []
        decisions_made = []
        files_created = []
        
        for message in messages:
            content = str(message.get("content", ""))
            sender = message.get("sender", "Unknown")
            agents_mentioned.add(sender)
            
            # Look for file operations
            if "write_file" in content or "created file" in content.lower():
                # Extract file names if possible
                files_created.append(f"{sender} created/modified files")
            
            # Look for decisions or implementations
            if any(keyword in content.lower() for keyword in ["implemented", "decided", "chosen", "completed"]):
                decisions_made.append(f"{sender}: {content[:100]}...")
            
            # Look for specific actions
            if any(keyword in content.lower() for keyword in ["task", "feature", "bug", "issue"]):
                key_actions.append(f"{sender}: {content[:80]}...")
        
        # Create summary
        summary_parts = []
        
        if agents_mentioned:
            summary_parts.append(f"Participants: {', '.join(agents_mentioned)}")
        
        if files_created:
            summary_parts.append(f"File operations: {len(files_created)} files created/modified")
        
        if key_actions:
            summary_parts.append(f"Key actions: {len(key_actions)} actions taken")
        
        if decisions_made:
            summary_parts.append(f"Decisions: {len(decisions_made)} decisions made")
        
        return " | ".join(summary_parts) if summary_parts else "No significant activity"
    
    def track_api_call(self, input_tokens: int, output_tokens: int, cost_estimate: float = None):
        """Track an API call for monitoring purposes."""
        self.total_tokens_used += input_tokens + output_tokens
        self.api_calls_made += 1
        
        call_data = {
            "timestamp": datetime.now().isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_estimate": cost_estimate,
            "cumulative_tokens": self.total_tokens_used,
            "call_number": self.api_calls_made
        }
        
        return call_data
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of token usage and costs."""
        # Updated pricing for different models (as of late 2024)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # Very cheap!
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        }
        
        # Determine model pricing
        model_key = self.model.lower()
        if "gpt-4o-mini" in model_key:
            rates = pricing["gpt-4o-mini"]
        elif "gpt-4o" in model_key:
            rates = pricing["gpt-4o"]
        elif "gpt-4-turbo" in model_key:
            rates = pricing["gpt-4-turbo"]
        elif "gpt-4" in model_key:
            rates = pricing["gpt-4"]
        elif "gpt-3.5" in model_key:
            rates = pricing["gpt-3.5-turbo"]
        else:
            # Default to GPT-4 pricing for unknown models
            rates = pricing["gpt-4"]
        
        # Estimate cost (simplified - assumes 70% input, 30% output)
        input_tokens = int(self.total_tokens_used * 0.7)
        output_tokens = int(self.total_tokens_used * 0.3)
        
        estimated_cost = (
            (input_tokens * rates["input"] / 1000) + 
            (output_tokens * rates["output"] / 1000)
        )
        
        return {
            "total_tokens_used": self.total_tokens_used,
            "api_calls_made": self.api_calls_made,
            "estimated_cost_usd": round(estimated_cost, 6),  # More precision for cheap models
            "average_tokens_per_call": self.total_tokens_used // max(self.api_calls_made, 1),
            "model": self.model,
            "input_cost_per_1k": rates["input"],
            "output_cost_per_1k": rates["output"]
        }
    
    def should_compress_context(self, messages: List[Dict[str, Any]], system_message: str = "") -> bool:
        """Determine if context compression is needed."""
        total_tokens = self.count_tokens(system_message)
        total_tokens += sum(self.count_message_tokens(msg) for msg in messages)
        
        return total_tokens > self.max_context_tokens * 0.8  # Compress if using >80% of limit 