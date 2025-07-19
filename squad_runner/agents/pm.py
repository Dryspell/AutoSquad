"""
PM Agent - Specialized for requirements analysis and project management
"""

from typing import Any, Dict, List

from autogen_ext.models.openai import OpenAIChatCompletionClient

from .base import BaseSquadAgent


class PMAgent(BaseSquadAgent):
    """PM agent focused on requirements analysis and project coordination."""
    
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
            name="Product_Manager",
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            # No system_message parameter = use enhanced prompts automatically
        )
        
        # PM-specific settings
        self.focus = agent_settings.get("focus", "user value")
        self.risk_tolerance = agent_settings.get("risk_tolerance", "medium")
    
    def get_agent_capabilities(self) -> List[str]:
        """Get the PM agent's specific capabilities."""
        base_capabilities = super().get_agent_capabilities()
        pm_capabilities = [
            "Requirements analysis and breakdown",
            "Feature prioritization and planning",
            "User story creation and management",
            "Project scope and timeline tracking",
            "Stakeholder communication",
            "Progress monitoring and reporting"
        ]
        return base_capabilities + pm_capabilities 