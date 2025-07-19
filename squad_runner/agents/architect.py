"""
Architect Agent - Specialized for code review and architecture design
"""

from typing import Any, Dict, List

from autogen_ext.models.openai import OpenAIChatCompletionClient

from .base import BaseSquadAgent


class ArchitectAgent(BaseSquadAgent):
    """Architect agent focused on code review and architecture design."""
    
    def __init__(
        self,
        model_client: OpenAIChatCompletionClient,
        project_context: Dict[str, Any],
        agent_settings: Dict[str, Any],
        project_manager
    ):
        # Initialize with enhanced prompts (no custom system_message)
        # The base class will automatically use enhanced prompts based on agent type
        super().__init__(
            name="Technical_Architect",
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            # No system_message parameter = use enhanced prompts automatically
        )
        
        # Architect-specific settings
        self.focus_areas = agent_settings.get("focus", ["maintainability", "scalability"])
        self.review_style = agent_settings.get("review_style", "balanced")
    
    def get_agent_capabilities(self) -> List[str]:
        """Get the Architect agent's specific capabilities."""
        base_capabilities = super().get_agent_capabilities()
        architect_capabilities = [
            "Code quality review and analysis",
            "Architecture design and planning",
            "Performance and scalability assessment",
            "Security consideration evaluation",
            "Refactoring recommendations",
            "Technical documentation guidance"
        ]
        return base_capabilities + architect_capabilities 