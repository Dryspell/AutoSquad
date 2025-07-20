"""
Input validation utilities for AutoSquad CLI.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import openai
from rich.console import Console

from .config import load_config, load_squad_profile
from .exceptions import (
    APIError, ConfigurationError, ModelError, ProjectError, 
    SquadProfileError, ValidationError
)

console = Console()


def validate_api_key(api_key: Optional[str] = None) -> str:
    """
    Validate OpenAI API key exists and is accessible.
    
    Args:
        api_key: Optional API key to validate. If None, checks environment.
        
    Returns:
        Valid API key string
        
    Raises:
        APIError: If API key is missing or invalid
    """
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise APIError(
            "🚫 OpenAI API key not found!\n"
            "Please set the OPENAI_API_KEY environment variable or configure it in your settings.\n"
            "Get your API key from: https://platform.openai.com/api-keys"
        )
    
    if not api_key.startswith(("sk-", "sk-proj-")):
        raise APIError(
            "🚫 Invalid OpenAI API key format!\n"
            "API keys should start with 'sk-' or 'sk-proj-'.\n"
            "Please check your API key and try again."
        )
    
    # Test API connectivity
    try:
        client = openai.OpenAI(api_key=api_key)
        # Simple test call to verify API access
        client.models.list()
        return api_key
    except openai.AuthenticationError:
        raise APIError(
            "🚫 OpenAI API authentication failed!\n"
            "Your API key appears to be invalid or expired.\n"
            "Please check your API key and try again."
        )
    except openai.RateLimitError:
        raise APIError(
            "🚫 OpenAI API rate limit exceeded!\n"
            "Please wait a moment and try again, or check your API usage limits."
        )
    except Exception as e:
        raise APIError(
            f"🚫 OpenAI API connectivity test failed!\n"
            f"Error: {str(e)}\n"
            "Please check your internet connection and API key."
        )


def validate_project(project_path: Path) -> Tuple[Path, str]:
    """
    Validate project directory and prompt file.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Tuple of (validated_path, prompt_content)
        
    Raises:
        ProjectError: If project structure is invalid
    """
    if not project_path.exists():
        raise ProjectError(
            f"🚫 Project directory not found: {project_path}\n"
            "Please check the path and try again."
        )
    
    if not project_path.is_dir():
        raise ProjectError(
            f"🚫 Project path is not a directory: {project_path}\n"
            "Please provide a valid project directory."
        )
    
    # Check for prompt.txt
    prompt_file = project_path / "prompt.txt"
    if not prompt_file.exists():
        raise ProjectError(
            f"🚫 No prompt.txt found in project directory: {project_path}\n"
            "Please create a prompt.txt file with your project description.\n"
            f"You can create one with: autosquad create --name {project_path.name}"
        )
    
    try:
        prompt_content = prompt_file.read_text(encoding='utf-8').strip()
    except Exception as e:
        raise ProjectError(
            f"🚫 Could not read prompt.txt: {e}\n"
            "Please check file permissions and encoding."
        )
    
    if not prompt_content:
        raise ProjectError(
            f"🚫 Empty prompt.txt file in {project_path}\n"
            "Please add your project description to prompt.txt"
        )
    
    # Create required directories if they don't exist
    workspace_dir = project_path / "workspace"
    logs_dir = project_path / "logs"
    
    try:
        workspace_dir.mkdir(exist_ok=True)
        logs_dir.mkdir(exist_ok=True)
    except Exception as e:
        raise ProjectError(
            f"🚫 Could not create project directories: {e}\n"
            "Please check directory permissions."
        )
    
    return project_path, prompt_content


def validate_squad_profile(profile_name: str) -> None:
    """
    Validate squad profile exists and is properly configured.
    
    Args:
        profile_name: Name of the squad profile to validate
        
    Raises:
        SquadProfileError: If profile is invalid or missing
    """
    try:
        profile = load_squad_profile(profile_name)
    except ValueError as e:
        # Get available profiles for helpful error message
        try:
            from .config import get_default_squad_profiles
            available = list(get_default_squad_profiles().keys())
            available_str = ", ".join(available)
        except:
            available_str = "mvp-team, full-stack, research-team"
        
        raise SquadProfileError(
            f"🚫 Squad profile '{profile_name}' not found!\n"
            f"Available profiles: {available_str}\n"
            "Use 'autosquad list-profiles' to see detailed descriptions."
        )
    
    # Validate profile structure
    if not profile.agents:
        raise SquadProfileError(
            f"🚫 Squad profile '{profile_name}' has no agents configured!\n"
            "Please check the profile configuration."
        )
    
    # Validate agent types
    valid_agent_types = {"pm", "engineer", "architect", "qa"}
    for agent_config in profile.agents:
        agent_type = agent_config.get("type")
        if not agent_type:
            raise SquadProfileError(
                f"🚫 Agent in profile '{profile_name}' is missing 'type' field!\n"
                "Please check the profile configuration."
            )
        
        if agent_type not in valid_agent_types:
            raise SquadProfileError(
                f"🚫 Unknown agent type '{agent_type}' in profile '{profile_name}'!\n"
                f"Valid types: {', '.join(valid_agent_types)}"
            )


def validate_model(model_name: str) -> None:
    """
    Validate model name and availability.
    
    Args:
        model_name: Name of the model to validate
        
    Raises:
        ModelError: If model is invalid or unavailable
    """
    # Known supported models (can be expanded)
    supported_models = {
        "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
    }
    
    if model_name not in supported_models:
        console.print(
            f"[yellow]⚠️  Warning: Model '{model_name}' is not in the known supported list.[/yellow]\n"
            f"[yellow]   Supported models: {', '.join(sorted(supported_models))}[/yellow]\n"
            f"[yellow]   Proceeding anyway - this may work if it's a valid OpenAI model.[/yellow]"
        )


def validate_configuration() -> None:
    """
    Validate AutoSquad configuration.
    
    Raises:
        ConfigurationError: If configuration is invalid
    """
    try:
        config = load_config()
    except Exception as e:
        raise ConfigurationError(
            f"🚫 Could not load AutoSquad configuration: {e}\n"
            "Please check your configuration files."
        )
    
    # Validate LLM config
    llm_config = config.llm_config
    if not llm_config:
        raise ConfigurationError(
            "🚫 Missing LLM configuration!\n"
            "Please check your autogen_config.yaml file."
        )
    
    # Check API key in config
    api_key = llm_config.get("api_key")
    if api_key and api_key.startswith("${") and api_key.endswith("}"):
        # Environment variable reference - validate it exists
        env_var = api_key[2:-1]
        if not os.getenv(env_var):
            raise ConfigurationError(
                f"🚫 Environment variable '{env_var}' is not set!\n"
                f"Referenced in configuration: {api_key}\n"
                "Please set this environment variable or update your configuration."
            )


def validate_all_inputs(
    project_path: Path,
    squad_profile: str,
    model: str,
    api_key: Optional[str] = None
) -> Tuple[Path, str, str]:
    """
    Validate all inputs before starting AutoSquad.
    
    Args:
        project_path: Path to project directory
        squad_profile: Name of squad profile
        model: Model name
        api_key: Optional API key override
        
    Returns:
        Tuple of (validated_project_path, prompt_content, validated_api_key)
        
    Raises:
        Various validation errors if inputs are invalid
    """
    console.print("[dim]🔍 Validating inputs...[/dim]")
    
    # Validate configuration first
    validate_configuration()
    
    # Validate API key
    validated_api_key = validate_api_key(api_key)
    
    # Validate project
    validated_project_path, prompt_content = validate_project(project_path)
    
    # Validate squad profile
    validate_squad_profile(squad_profile)
    
    # Validate model (with warning for unknown models)
    validate_model(model)
    
    console.print("[dim]✅ All inputs validated successfully[/dim]")
    
    return validated_project_path, prompt_content, validated_api_key 