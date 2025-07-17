"""
AutoSquad Agents - Specialized AutoGen agents for software development
"""

from .base import BaseSquadAgent
from .engineer import EngineerAgent
from .architect import ArchitectAgent
from .pm import PMAgent
from .qa import QAAgent
from .dynamic_agent import DynamicAgent

from typing import Any, Dict, Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def create_agent(
    agent_type: str,
    model_client: OpenAIChatCompletionClient,
    project_context: Dict[str, Any],
    agent_settings: Dict[str, Any],
    project_manager,
    role_config: Optional[Dict[str, Any]] = None,
    perspective_config: Optional[Dict[str, Any]] = None
) -> BaseSquadAgent:
    """Factory function to create specialized agents.
    
    Args:
        agent_type: Type of agent ('engineer', 'architect', 'pm', 'qa', 'dynamic')
        model_client: OpenAI client for agent communication
        project_context: Project-specific context and configuration
        agent_settings: Agent-specific settings
        project_manager: Project manager instance
        role_config: Optional custom role configuration for dynamic agents
        perspective_config: Optional perspective configuration for dynamic agents
    
    Returns:
        Initialized agent instance
    """
    
    # Handle dynamic agents with custom role/perspective configurations
    if agent_type == "dynamic" or role_config or perspective_config:
        if not role_config:
            raise ValueError("Dynamic agents require role_config")
        
        return DynamicAgent(
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            role_config=role_config,
            perspective_config=perspective_config
        )
    
    # Handle traditional static agents
    agent_classes = {
        "engineer": EngineerAgent,
        "architect": ArchitectAgent,
        "pm": PMAgent,
        "qa": QAAgent
    }
    
    if agent_type not in agent_classes:
        raise ValueError(f"Unknown agent type: {agent_type}. Supported types: {list(agent_classes.keys())} or 'dynamic'")
    
    agent_class = agent_classes[agent_type]
    
    # Create and initialize the agent
    agent = agent_class(
        model_client=model_client,
        project_context=project_context,
        agent_settings=agent_settings,
        project_manager=project_manager
    )
    
    return agent


def create_project_specific_agents(
    project_config: Dict[str, Any],
    model_client: OpenAIChatCompletionClient,
    project_context: Dict[str, Any],
    project_manager
) -> Dict[str, BaseSquadAgent]:
    """Create agents based on project-specific agent configurations.
    
    This function reads agent definitions from the project configuration
    and creates customized agents with specific roles and perspectives.
    
    Args:
        project_config: Project configuration containing agent definitions
        model_client: OpenAI client for agent communication
        project_context: Project-specific context
        project_manager: Project manager instance
    
    Returns:
        Dictionary of created agents keyed by agent name
    """
    agents = {}
    agent_configs = project_config.get("agents", [])
    
    for agent_config in agent_configs:
        role_config = agent_config.get("role", {})
        perspective_config = agent_config.get("perspective")
        agent_settings = agent_config.get("settings", {})
        
        agent = create_agent(
            agent_type="dynamic",
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            role_config=role_config,
            perspective_config=perspective_config
        )
        
        agents[agent.name] = agent
    
    return agents


__all__ = [
    "BaseSquadAgent",
    "EngineerAgent", 
    "ArchitectAgent",
    "PMAgent",
    "QAAgent",
    "DynamicAgent",
    "create_agent",
    "create_project_specific_agents"
] 