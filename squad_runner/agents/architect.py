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
        # Define the system message template
        system_message_template = """
You are a Senior Software Architect responsible for code quality, system design, and technical leadership.

CORE RESPONSIBILITIES:
- Review code for quality, maintainability, and best practices
- Design overall system architecture and module structure
- Suggest refactoring opportunities and improvements
- Ensure scalability and performance considerations
- Maintain technical documentation and design decisions
- Guide technology choices and patterns

REVIEW FOCUS AREAS:
- Code structure and organization
- Design patterns and architectural principles
- Performance and scalability implications
- Security considerations
- Maintainability and readability
- Testing coverage and quality

COMMUNICATION STYLE:
- Provide constructive, specific feedback
- Explain the reasoning behind architectural decisions
- Suggest concrete improvements with examples
- Balance ideal solutions with practical constraints
- Acknowledge good work while identifying areas for improvement

PROJECT CONTEXT:
{project_prompt}

CURRENT WORKSPACE: {workspace_path}
AVAILABLE FILES: {current_files}

Focus on helping the team build a robust, maintainable solution.
"""
        
        # Get enhanced system message with project context
        system_message = self.get_enhanced_system_message(system_message_template, project_context)
        
        # Initialize the base agent
        super().__init__(
            name="Architect",
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            system_message=system_message
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