"""
Engineer Agent - Specialized for code implementation and technical execution
"""

from typing import Any, Dict, List

from autogen_ext.models.openai import OpenAIChatCompletionClient

from .base import BaseSquadAgent


class EngineerAgent(BaseSquadAgent):
    """Engineer agent focused on code implementation and technical execution."""
    
    def __init__(
        self,
        model_client: OpenAIChatCompletionClient,
        project_context: Dict[str, Any],
        agent_settings: Dict[str, Any],
        project_manager
    ):
        # Define the system message template
        system_message_template = """
You are an experienced Software Engineer working on a development team. Your role is to implement features, write clean code, and solve technical problems.

CORE RESPONSIBILITIES:
- Write production-ready code based on requirements
- Create and modify files in the project workspace  
- Install necessary dependencies and manage project setup
- Debug issues and fix bugs in existing code
- Write basic tests for your implementations
- Follow best practices for the chosen technology stack

WORKING STYLE:
- Start with the simplest solution that works
- Write clear, readable code with appropriate comments
- Ask for clarification when requirements are unclear
- Test your code before considering it complete
- Communicate progress and blockers clearly

AVAILABLE TOOLS:
You have access to these function calling tools for workspace operations:

1. **write_file(file_path, content, description)** - Create or update files
   - Use this to implement code, create config files, documentation, etc.
   - Always provide complete, working file content
   - Include helpful descriptions

2. **read_file(file_path)** - Read existing files
   - Use this to understand current codebase before making changes
   - Review existing implementations and patterns

3. **list_files()** - See all current workspace files
   - Use this to understand project structure
   - Check what files already exist

4. **create_directory(dir_path)** - Create directory structures
   - Use this to organize code into proper folder structures

IMPLEMENTATION APPROACH:
When implementing features:
1. Use list_files() to see current workspace state
2. Use read_file() to understand existing code (if any)
3. Use write_file() to create/update implementation files
4. Use create_directory() to organize code structure

Always call the appropriate tools to actually create the files - don't just describe what you would do!

PROJECT CONTEXT:
{project_prompt}

CURRENT WORKSPACE: {workspace_path}
AVAILABLE FILES: {current_files}

Always work within the designated workspace and coordinate with your teammates.

IMPORTANT: When you need to create or modify files, use the write_file function tool. When you need to read files, use the read_file function tool. The team is counting on you to actually implement working code!
"""
        
        # Get enhanced system message with project context
        system_message = self.get_enhanced_system_message(system_message_template, project_context)
        
        # Initialize the base agent
        super().__init__(
            name="Engineer",
            model_client=model_client,
            project_context=project_context,
            agent_settings=agent_settings,
            project_manager=project_manager,
            system_message=system_message
        )
        
        # Engineer-specific settings
        self.preferred_languages = agent_settings.get("languages", ["python"])
        self.preferred_frameworks = agent_settings.get("frameworks", [])
        self.focus = agent_settings.get("focus", "general development")
    
    def get_agent_capabilities(self) -> List[str]:
        """Get the Engineer agent's specific capabilities."""
        base_capabilities = super().get_agent_capabilities()
        engineer_capabilities = [
            "Code implementation and development",
            "File creation and modification", 
            "Bug fixing and debugging",
            "Basic testing and validation",
            "Dependency management",
            "Project structure organization"
        ]
        return base_capabilities + engineer_capabilities
    
    def create_file_with_content(self, file_path: str, content: str, description: str = "") -> str:
        """Create a file and return a formatted announcement."""
        self.write_workspace_file(file_path, content)
        
        if description:
            action = f"Created `{file_path}` - {description}"
        else:
            action = f"Created `{file_path}`"
        
        return self.announce_action(
            action,
            self.format_code_block(content, self._get_file_language(file_path))
        )
    
    def update_file_with_content(self, file_path: str, content: str, description: str = "") -> str:
        """Update a file and return a formatted announcement."""
        self.write_workspace_file(file_path, content)
        
        if description:
            action = f"Updated `{file_path}` - {description}"
        else:
            action = f"Updated `{file_path}`"
        
        return self.announce_action(
            action,
            self.format_code_block(content, self._get_file_language(file_path))
        )
    
    def read_and_analyze_file(self, file_path: str) -> str:
        """Read a file and provide analysis."""
        try:
            content = self.read_workspace_file(file_path)
            return self.announce_action(
                f"Analyzed `{file_path}`",
                f"File contents:\n{self.format_code_block(content, self._get_file_language(file_path))}"
            )
        except FileNotFoundError:
            return self.announce_action(f"File `{file_path}` not found in workspace")
    
    def create_requirements_file(self, dependencies: List[str]) -> str:
        """Create a requirements.txt file for Python projects."""
        content = "\n".join(dependencies)
        return self.create_file_with_content(
            "requirements.txt",
            content,
            f"Added {len(dependencies)} dependencies"
        )
    
    def create_readme(self, project_title: str, description: str, usage_instructions: str = "") -> str:
        """Create a README.md file for the project."""
        content = f"""# {project_title}

{description}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

{usage_instructions or "Usage instructions to be added."}

## Features

- Core functionality implemented
- Basic error handling
- Clean, readable code structure

## Development

This project was generated using AutoSquad - an autonomous AI development framework.
"""
        
        return self.create_file_with_content(
            "README.md",
            content,
            "Added project documentation"
        )
    
    def suggest_project_structure(self, project_type: str = "python") -> str:
        """Suggest an appropriate project structure."""
        if project_type == "python":
            structure = """
Suggested Python project structure:
```
project/
├── main.py           # Entry point
├── requirements.txt  # Dependencies  
├── README.md        # Documentation
├── src/             # Source code
│   ├── __init__.py
│   └── core.py      # Core logic
├── tests/           # Test files
│   └── test_core.py
└── config/          # Configuration files
```
"""
        elif project_type == "web":
            structure = """
Suggested web project structure:
```
project/
├── index.html       # Main page
├── static/          # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── package.json     # Dependencies
└── README.md       # Documentation
```
"""
        else:
            structure = """
Suggested general project structure:
```
project/
├── main file        # Entry point
├── dependencies     # Dependency management
├── README.md       # Documentation
├── src/            # Source code
└── tests/          # Test files
```
"""
        
        return self.announce_action("Suggested project structure", structure)
    
    def get_development_status(self) -> str:
        """Get current development status summary."""
        files = self.get_workspace_files()
        workspace_summary = self.get_workspace_summary()
        
        status = f"""
Development Status Summary:
- Files created: {len(files)}
- Workspace: {workspace_summary}
- Focus: {self.focus}
- Preferred languages: {', '.join(self.preferred_languages)}
"""
        
        if self.preferred_frameworks:
            status += f"- Preferred frameworks: {', '.join(self.preferred_frameworks)}\n"
        
        return self.announce_action("Development Status", status) 