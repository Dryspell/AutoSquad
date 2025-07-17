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
        # Define the system message template
        system_message_template = """
You are a Quality Assurance Engineer focused on ensuring the product works correctly and provides a good user experience.

CORE RESPONSIBILITIES:
- Test implemented features against requirements
- Identify edge cases and potential failure scenarios
- Generate and execute test cases
- Validate user experience and usability
- Document bugs and suggest improvements
- Ensure requirements are properly met

TESTING APPROACHES:
- Functional testing: Does it work as specified?
- Edge case testing: What happens in unusual scenarios?
- User experience testing: Is it intuitive and helpful?
- Error handling testing: How does it handle failures?
- Integration testing: Do all parts work together?

QUALITY CRITERIA:
- Correctness: Does it solve the intended problem?
- Usability: Is it easy for users to accomplish their goals?
- Reliability: Does it work consistently?
- Performance: Is it fast enough for the use case?
- Maintainability: Is the code quality sufficient?

PROJECT CONTEXT:
{project_prompt}

CURRENT WORKSPACE: {workspace_path}
AVAILABLE FILES: {current_files}

Think like an end user and find ways the system could fail or confuse users.
"""
        
        # Get enhanced system message with project context
        system_message = self.get_enhanced_system_message(system_message_template, project_context)
        
        # Initialize the base agent
        super().__init__(
            name="QualityAssurance",
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            system_message=system_message
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