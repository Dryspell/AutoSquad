"""
Project Configuration Parser - Reads enhanced project files with agent definitions
"""

import re
import yaml
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


class ProjectConfigParser:
    """Parse enhanced project files that include agent configurations."""
    
    def __init__(self):
        self.project_description = ""
        self.agent_configurations = []
        self.workflow_configuration = {}
    
    def parse_project_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a project file with embedded agent configurations.
        
        Args:
            file_path: Path to the project file (prompt.txt or .yaml)
            
        Returns:
            Dictionary containing project description, agent configs, and workflow settings
        """
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.yaml' or file_path.suffix.lower() == '.yml':
            return self._parse_yaml_file(file_path)
        else:
            return self._parse_text_file(file_path)
    
    def _parse_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a YAML configuration file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return {
            "project_description": config.get("project_description", ""),
            "agents": config.get("agents", []),
            "workflow": config.get("workflow", {}),
            "requirements": config.get("requirements", []),
            "success_metrics": config.get("success_metrics", [])
        }
    
    def _parse_text_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a text file with embedded YAML sections."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into sections
        project_description, agent_config, workflow_config = self._split_content_sections(content)
        
        # Parse agent configuration
        agents = []
        if agent_config:
            try:
                parsed_config = yaml.safe_load(agent_config)
                agents = parsed_config.get("agents", [])
            except yaml.YAMLError as e:
                print(f"Warning: Could not parse agent configuration: {e}")
        
        # Parse workflow configuration  
        workflow = {}
        if workflow_config:
            try:
                workflow = yaml.safe_load(workflow_config)
            except yaml.YAMLError as e:
                print(f"Warning: Could not parse workflow configuration: {e}")
        
        return {
            "project_description": project_description.strip(),
            "agents": agents,
            "workflow": workflow,
            "requirements": self._extract_requirements(project_description),
            "success_metrics": self._extract_success_metrics(project_description)
        }
    
    def _split_content_sections(self, content: str) -> Tuple[str, str, str]:
        """Split content into project description, agent config, and workflow config sections."""
        
        # Look for agent configuration section
        agent_config_match = re.search(
            r'AGENT_CONFIGURATION:\s*\n(.*?)(?=\n\s*WORKFLOW_CONFIGURATION:|$)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        # Look for workflow configuration section
        workflow_config_match = re.search(
            r'WORKFLOW_CONFIGURATION:\s*\n(.*?)$',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        # Extract sections
        agent_config = agent_config_match.group(1).strip() if agent_config_match else ""
        workflow_config = workflow_config_match.group(1).strip() if workflow_config_match else ""
        
        # Extract project description (everything before agent configuration)
        if agent_config_match:
            project_description = content[:agent_config_match.start()].strip()
        else:
            project_description = content.strip()
        
        # Remove "PROJECT_DESCRIPTION:" header if present
        project_description = re.sub(r'^PROJECT_DESCRIPTION:\s*\n', '', project_description, flags=re.IGNORECASE)
        
        return project_description, agent_config, workflow_config
    
    def _extract_requirements(self, project_description: str) -> List[str]:
        """Extract requirements from project description."""
        requirements = []
        
        # Look for numbered requirements
        requirement_pattern = r'^\s*(\d+)\.\s*\*\*(.*?)\*\*\s*-\s*(.*?)$'
        for match in re.finditer(requirement_pattern, project_description, re.MULTILINE):
            title = match.group(2)
            description = match.group(3)
            requirements.append(f"{title}: {description}")
        
        # Look for bullet point requirements
        bullet_pattern = r'^\s*[-*]\s*\*\*(.*?)\*\*\s*-?\s*(.*?)$'
        for match in re.finditer(bullet_pattern, project_description, re.MULTILINE):
            title = match.group(1)
            description = match.group(2)
            if description:
                requirements.append(f"{title}: {description}")
            else:
                requirements.append(title)
        
        return requirements
    
    def _extract_success_metrics(self, project_description: str) -> List[str]:
        """Extract success metrics from project description."""
        metrics = []
        
        # Look for success metrics section
        metrics_section = re.search(
            r'(?:Success Metrics|Success Criteria):\s*\n(.*?)(?=\n\s*##|\n\s*---|\n\s*[A-Z_]+:|$)',
            project_description,
            re.DOTALL | re.IGNORECASE
        )
        
        if metrics_section:
            metrics_text = metrics_section.group(1)
            
            # Extract bullet points
            bullet_pattern = r'^\s*[-*]\s*(.*?)$'
            for match in re.finditer(bullet_pattern, metrics_text, re.MULTILINE):
                metrics.append(match.group(1).strip())
        
        return metrics
    
    def validate_agent_configuration(self, agent_config: Dict[str, Any]) -> bool:
        """Validate that an agent configuration has required fields."""
        required_role_fields = ["name", "description", "responsibilities", "expertise"]
        
        role = agent_config.get("role", {})
        for field in required_role_fields:
            if field not in role:
                print(f"Warning: Agent configuration missing required field: role.{field}")
                return False
        
        return True
    
    def create_default_agents_if_missing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create default agent configuration if none specified."""
        if not config.get("agents"):
            # Determine project type from description
            project_type = self._detect_project_type(config.get("project_description", ""))
            config["agents"] = self._get_default_agents_for_type(project_type)
        
        return config
    
    def _detect_project_type(self, description: str) -> str:
        """Detect project type from description text."""
        description_lower = description.lower()
        
        if any(term in description_lower for term in ["restaurant", "food", "dining", "kitchen", "menu"]):
            return "restaurant"
        elif any(term in description_lower for term in ["writing", "story", "book", "author", "publish"]):
            return "creative_writing"
        elif any(term in description_lower for term in ["legal", "contract", "compliance", "law"]):
            return "legal"
        elif any(term in description_lower for term in ["marketing", "campaign", "social media", "advertising"]):
            return "marketing"
        elif any(term in description_lower for term in ["finance", "financial", "budget", "accounting"]):
            return "finance"
        elif any(term in description_lower for term in ["website", "web", "sales", "b2b", "lead"]):
            return "web_business"
        else:
            return "software_development"
    
    def _get_default_agents_for_type(self, project_type: str) -> List[Dict[str, Any]]:
        """Get default agent configurations for different project types."""
        
        defaults = {
            "software_development": [
                {
                    "role": {
                        "name": "Product Manager",
                        "description": "Requirements analysis and project coordination specialist",
                        "type": "planner",
                        "responsibilities": ["Define requirements", "Manage scope", "Coordinate team"],
                        "expertise": ["Product management", "Requirements analysis", "Project coordination"]
                    }
                },
                {
                    "role": {
                        "name": "Software Engineer", 
                        "description": "Code implementation and technical execution specialist",
                        "type": "builder",
                        "responsibilities": ["Implement features", "Write code", "Create technical solutions"],
                        "expertise": ["Software development", "Programming", "Technical implementation"]
                    }
                },
                {
                    "role": {
                        "name": "Quality Assurance",
                        "description": "Testing and quality validation specialist", 
                        "type": "tester",
                        "responsibilities": ["Test features", "Validate quality", "Find issues"],
                        "expertise": ["Quality assurance", "Testing", "Bug detection"]
                    }
                }
            ],
            
            "restaurant": [
                {
                    "role": {
                        "name": "Operations Manager",
                        "description": "Restaurant operations and efficiency specialist",
                        "type": "planner",
                        "responsibilities": ["Optimize workflows", "Manage operations", "Plan strategies"],
                        "expertise": ["Restaurant operations", "Workflow optimization", "Staff management"]
                    }
                },
                {
                    "role": {
                        "name": "Systems Developer", 
                        "description": "Restaurant technology and system implementation specialist",
                        "type": "builder",
                        "responsibilities": ["Build systems", "Implement technology", "Create solutions"],
                        "expertise": ["Restaurant technology", "System integration", "Process automation"]
                    }
                }
            ],
            
            "creative_writing": [
                {
                    "role": {
                        "name": "Story Architect",
                        "description": "Plot and narrative development specialist",
                        "type": "planner", 
                        "responsibilities": ["Develop plots", "Plan narratives", "Structure stories"],
                        "expertise": ["Narrative structure", "Plot development", "Character design"]
                    }
                },
                {
                    "role": {
                        "name": "Content Creator",
                        "description": "Writing and prose development specialist",
                        "type": "builder",
                        "responsibilities": ["Write content", "Develop prose", "Create narratives"], 
                        "expertise": ["Creative writing", "Prose composition", "Content creation"]
                    }
                }
            ]
        }
        
        return defaults.get(project_type, defaults["software_development"])


def parse_project_configuration(project_path: str) -> Dict[str, Any]:
    """Convenience function to parse a project configuration file.
    
    Args:
        project_path: Path to the project configuration file
        
    Returns:
        Parsed project configuration
    """
    parser = ProjectConfigParser()
    config = parser.parse_project_file(project_path)
    config = parser.create_default_agents_if_missing(config)
    
    return config


def create_agents_from_config(
    config: Dict[str, Any],
    model_client,
    project_context: Dict[str, Any],
    project_manager
) -> List:
    """Create dynamic agents from project configuration.
    
    Args:
        config: Parsed project configuration
        model_client: OpenAI client
        project_context: Project context
        project_manager: Project manager instance
        
    Returns:
        List of created agents
    """
    from .agents import create_agent
    
    agents = []
    
    for agent_config in config.get("agents", []):
        try:
            agent = create_agent(
                agent_type="dynamic",
                model_client=model_client,
                project_context=project_context,
                agent_settings={},
                project_manager=project_manager,
                role_config=agent_config.get("role", {}),
                perspective_config=agent_config.get("perspective")
            )
            agents.append(agent)
        except Exception as e:
            print(f"Warning: Could not create agent from config: {e}")
    
    return agents 