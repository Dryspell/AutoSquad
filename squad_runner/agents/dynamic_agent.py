"""
Dynamic Agent - Configurable agent with custom roles and perspectives
"""

from typing import Any, Dict, List, Optional

from autogen_ext.models.openai import OpenAIChatCompletionClient

from .base import BaseSquadAgent


class DynamicAgent(BaseSquadAgent):
    """Dynamic agent that can be configured with custom roles and perspectives."""
    
    def __init__(
        self,
        model_client: OpenAIChatCompletionClient,
        project_context: Dict[str, Any],
        agent_settings: Dict[str, Any],
        project_manager,
        role_config: Dict[str, Any],
        perspective_config: Optional[Dict[str, Any]] = None
    ):
        self.role_config = role_config
        self.perspective_config = perspective_config or {}
        
        # Build dynamic system message
        system_message = self._build_dynamic_system_message(
            role_config, perspective_config, project_context
        )
        
        # Generate agent name
        agent_name = self._generate_agent_name(role_config, perspective_config)
        
        # Initialize the base agent
        super().__init__(
            name=agent_name,
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            system_message=system_message
        )
        
        # Dynamic agent specific settings
        self.role_type = role_config.get("type", "custom")
        self.expertise_areas = role_config.get("expertise", [])
        self.perspective_background = perspective_config.get("background", {})
    
    def _build_dynamic_system_message(
        self, 
        role_config: Dict[str, Any], 
        perspective_config: Dict[str, Any],
        project_context: Dict[str, Any]
    ) -> str:
        """Build a dynamic system message based on role and perspective configurations."""
        
        # Role-based prompt section
        role_section = self._build_role_section(role_config)
        
        # Perspective-based prompt section
        perspective_section = self._build_perspective_section(perspective_config)
        
        # Tools and capabilities section
        tools_section = self._build_tools_section(role_config)
        
        # Project context section
        context_section = self._build_context_section(project_context)
        
        # Combine all sections
        system_message = f"""
{role_section}

{perspective_section}

{tools_section}

{context_section}

COLLABORATION STYLE:
- Build on others' ideas while bringing your unique perspective
- Ask questions that challenge assumptions respectfully
- Share insights from your background and experience
- Adapt your communication style to the team's needs
- Focus on delivering value while maintaining your authentic voice

Remember: Your diverse perspective is valuable - don't hesitate to suggest alternative approaches or highlight considerations others might miss.
"""
        
        return system_message.strip()
    
    def _build_role_section(self, role_config: Dict[str, Any]) -> str:
        """Build the role-specific section of the system message."""
        role_name = role_config.get("name", "Specialist")
        role_description = role_config.get("description", "A specialized team member")
        responsibilities = role_config.get("responsibilities", [])
        expertise = role_config.get("expertise", [])
        
        role_section = f"""
You are a {role_name} - {role_description}

CORE RESPONSIBILITIES:
{self._format_list(responsibilities)}

EXPERTISE AREAS:
{self._format_list(expertise)}

WORKING APPROACH:
- Focus on {role_config.get('focus', 'delivering high-quality solutions')}
- Prioritize {role_config.get('priorities', ['quality', 'user value'])}
- Collaborate using a {role_config.get('style', 'professional and constructive')} approach
"""
        return role_section
    
    def _build_perspective_section(self, perspective_config: Dict[str, Any]) -> str:
        """Build the perspective-specific section of the system message."""
        if not perspective_config:
            return ""
        
        background = perspective_config.get("background", {})
        cultural_context = perspective_config.get("cultural_context", {})
        market_experience = perspective_config.get("market_experience", [])
        unique_insights = perspective_config.get("unique_insights", [])
        
        location = background.get("location", "")
        professional_background = background.get("professional", "")
        
        perspective_section = f"""
BACKGROUND & PERSPECTIVE:
"""
        
        if location:
            perspective_section += f"- Geographic Context: {location}\n"
        
        if professional_background:
            perspective_section += f"- Professional Background: {professional_background}\n"
        
        if cultural_context:
            context_items = [f"{k}: {v}" for k, v in cultural_context.items()]
            perspective_section += f"- Cultural Context: {', '.join(context_items)}\n"
        
        if market_experience:
            perspective_section += f"- Market Experience: {', '.join(market_experience)}\n"
        
        if unique_insights:
            perspective_section += f"\nUNIQUE INSIGHTS YOU BRING:\n{self._format_list(unique_insights)}\n"
        
        return perspective_section
    
    def _build_tools_section(self, role_config: Dict[str, Any]) -> str:
        """Build the tools and capabilities section."""
        tools = role_config.get("tools", [])
        capabilities = role_config.get("capabilities", [])
        
        tools_section = f"""
AVAILABLE TOOLS & CAPABILITIES:
{self._format_list(tools + capabilities)}

When using tools, always:
1. Explain why you're using a specific tool
2. Describe what you expect to accomplish
3. Share insights from your unique perspective
"""
        return tools_section
    
    def _build_context_section(self, project_context: Dict[str, Any]) -> str:
        """Build the project context section."""
        return f"""
PROJECT CONTEXT:
{project_context.get('prompt', 'No project prompt available')}

CURRENT WORKSPACE: {project_context.get('workspace_path', 'Unknown')}
AVAILABLE FILES: {project_context.get('current_files', [])}
"""
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items for the system message."""
        if not items:
            return "- None specified"
        return "\n".join([f"- {item}" for item in items])
    
    def _generate_agent_name(
        self, 
        role_config: Dict[str, Any], 
        perspective_config: Dict[str, Any]
    ) -> str:
        """Generate a descriptive name for the agent."""
        role_name = role_config.get("name", "Specialist")
        
        if perspective_config and perspective_config.get("background", {}).get("location"):
            location = perspective_config["background"]["location"]
            return f"{role_name}_{location.replace(' ', '_').replace(',', '')}"
        
        return role_name
    
    def get_agent_capabilities(self) -> List[str]:
        """Get the dynamic agent's specific capabilities."""
        base_capabilities = super().get_agent_capabilities()
        role_capabilities = self.role_config.get("capabilities", [])
        
        # Add perspective-based capabilities
        perspective_capabilities = []
        if self.perspective_config:
            market_exp = self.perspective_config.get("market_experience", [])
            perspective_capabilities = [f"Market insight: {market}" for market in market_exp]
        
        return base_capabilities + role_capabilities + perspective_capabilities
    
    def get_role_summary(self) -> Dict[str, Any]:
        """Get a summary of this agent's role and perspective."""
        return {
            "name": self.name,
            "role": self.role_config.get("name", "Specialist"),
            "description": self.role_config.get("description", ""),
            "expertise": self.expertise_areas,
            "perspective": self.perspective_background,
            "capabilities": self.get_agent_capabilities()
        } 