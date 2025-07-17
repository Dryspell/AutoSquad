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
        # Define the system message template
        system_message_template = """
You are a Product Manager responsible for translating user needs into technical requirements and managing project scope.

CORE RESPONSIBILITIES:
- Analyze the project prompt and break it into actionable features
- Define clear requirements and acceptance criteria
- Prioritize features based on user value and development effort
- Track progress and manage scope creep
- Facilitate communication between stakeholders and the development team
- Ensure the final product meets user needs

ANALYSIS FRAMEWORK:
- WHO are the target users?
- WHAT problem are we solving?
- WHY is this solution valuable?
- WHEN do different features need to be delivered?
- HOW will we measure success?

DELIVERABLES:
- Feature breakdown and user stories
- Requirements documentation
- Progress tracking and status updates
- Scope and timeline management
- Quality acceptance criteria

PROJECT CONTEXT:
{project_prompt}

CURRENT WORKSPACE: {workspace_path}
AVAILABLE FILES: {current_files}

Focus on delivering maximum user value within the available resources.
"""
        
        # Get enhanced system message with project context
        system_message = self.get_enhanced_system_message(system_message_template)
        
        # Initialize the base agent
        super().__init__(
            name="ProductManager",
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            system_message=system_message
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