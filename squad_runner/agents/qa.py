"""
QA Agent - Specialized for quality assurance and testing
"""

from typing import Any, Dict, List

from autogen_ext.models.openai import OpenAIChatCompletionClient

from .base import BaseSquadAgent


class QAAgent(BaseSquadAgent):
    """QA agent focused on quality assurance and testing."""
    
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
            name="Quality_Assurance_Engineer",
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            # No system_message parameter = use enhanced prompts automatically
        )
        
        # QA-specific settings
        self.focus_areas = agent_settings.get("focus", ["functionality", "usability"])
        self.testing_types = agent_settings.get("testing_types", ["functional", "edge_case"])
    
    def get_agent_capabilities(self) -> List[str]:
        """Get the QA agent's specific capabilities."""
        base_capabilities = super().get_agent_capabilities()
        qa_capabilities = [
            "Functional testing and validation",
            "Edge case identification and testing",
            "User experience evaluation",
            "Bug detection and reporting",
            "Test case generation and execution",
            "Quality criteria assessment"
        ]
        return base_capabilities + qa_capabilities 