"""
AutoSquad Agents - Specialized AutoGen agents for software development
"""

from .base import BaseSquadAgent
from .engineer import EngineerAgent
from .architect import ArchitectAgent
from .pm import PMAgent
from .qa import QAAgent

from typing import Any, Dict
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def create_agent(
    agent_type: str,
    model_client: OpenAIChatCompletionClient,
    project_context: Dict[str, Any],
    agent_settings: Dict[str, Any],
    project_manager
) -> BaseSquadAgent:
    """Factory function to create specialized agents."""
    
    agent_classes = {
        "engineer": EngineerAgent,
        "architect": ArchitectAgent,
        "pm": PMAgent,
        "qa": QAAgent
    }
    
    if agent_type not in agent_classes:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    agent_class = agent_classes[agent_type]
    
    # Create and initialize the agent
    agent = agent_class(
        model_client=model_client,
        project_context=project_context,
        agent_settings=agent_settings,
        project_manager=project_manager
    )
    
    return agent


__all__ = [
    "BaseSquadAgent",
    "EngineerAgent", 
    "ArchitectAgent",
    "PMAgent",
    "QAAgent",
    "create_agent"
] 