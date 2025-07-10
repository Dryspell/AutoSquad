"""
Configuration management for AutoSquad
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AutoSquadConfig:
    """Configuration container for AutoSquad settings."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        
    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for AutoGen agents."""
        llm_config = self.config.get("llm_config", {})
        
        # Substitute environment variables
        if "api_key" in llm_config:
            api_key = llm_config["api_key"]
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                llm_config["api_key"] = os.getenv(env_var)
        
        return llm_config
    
    @property
    def runtime_config(self) -> Dict[str, Any]:
        """Get runtime configuration for AutoGen."""
        return self.config.get("runtime_config", {})
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config.get("logging", {})


class SquadProfile:
    """Squad profile configuration."""
    
    def __init__(self, profile_dict: Dict[str, Any]):
        self.profile = profile_dict
        
    @property
    def agents(self) -> list:
        """Get list of agent configurations."""
        return self.profile.get("agents", [])
    
    @property
    def workflow(self) -> Dict[str, Any]:
        """Get workflow configuration."""
        return self.profile.get("workflow", {})
    
    @property
    def rounds(self) -> int:
        """Get default number of rounds."""
        return self.workflow.get("rounds", 3)
    
    @property
    def reflection_frequency(self) -> int:
        """Get reflection frequency."""
        return self.workflow.get("reflection_frequency", 2)


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path(__file__).parent.parent / "configs"


def load_config() -> AutoSquadConfig:
    """Load main AutoSquad configuration."""
    config_path = get_config_dir() / "autogen_config.yaml"
    
    if not config_path.exists():
        # Return default configuration
        return AutoSquadConfig({
            "llm_config": {
                "model": "gpt-4",
                "api_key": "${OPENAI_API_KEY}",
                "temperature": 0.1,
                "max_tokens": 2000
            },
            "runtime_config": {
                "code_execution": True,
                "execution_timeout": 30,
                "max_consecutive_auto_reply": 10
            },
            "logging": {
                "level": "INFO",
                "autogen_logs": True,
                "conversation_logs": True
            }
        })
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    return AutoSquadConfig(config_data)


def load_squad_profile(profile_name: str) -> SquadProfile:
    """Load a squad profile configuration."""
    profiles_path = get_config_dir() / "squad_profiles.yaml"
    
    if not profiles_path.exists():
        # Return default profiles
        default_profiles = get_default_squad_profiles()
        if profile_name in default_profiles:
            return SquadProfile(default_profiles[profile_name])
        else:
            raise ValueError(f"Squad profile '{profile_name}' not found in default profiles")
    
    with open(profiles_path, 'r') as f:
        profiles_data = yaml.safe_load(f)
    
    if profile_name not in profiles_data.get("profiles", {}):
        raise ValueError(f"Squad profile '{profile_name}' not found in {profiles_path}")
    
    return SquadProfile(profiles_data["profiles"][profile_name])


def get_default_squad_profiles() -> Dict[str, Dict[str, Any]]:
    """Get default squad profile configurations."""
    return {
        "mvp-team": {
            "agents": [
                {
                    "type": "pm",
                    "config": {
                        "focus": "minimum viable product",
                        "risk_tolerance": "medium"
                    }
                },
                {
                    "type": "engineer",
                    "config": {
                        "languages": ["python", "javascript"],
                        "frameworks": ["flask", "fastapi", "react"],
                        "focus": "rapid prototyping"
                    }
                },
                {
                    "type": "architect",
                    "config": {
                        "focus": ["maintainability", "simplicity"],
                        "review_style": "pragmatic"
                    }
                }
            ],
            "workflow": {
                "rounds": 3,
                "reflection_frequency": 2,
                "quality_gates": ["basic_testing", "code_review"]
            }
        },
        
        "full-stack": {
            "agents": [
                {
                    "type": "pm",
                    "config": {
                        "focus": "comprehensive product development",
                        "risk_tolerance": "low"
                    }
                },
                {
                    "type": "engineer",
                    "config": {
                        "languages": ["python", "javascript", "typescript"],
                        "frameworks": ["flask", "fastapi", "react", "nextjs"],
                        "focus": "production ready"
                    }
                },
                {
                    "type": "architect",
                    "config": {
                        "focus": ["scalability", "maintainability", "security"],
                        "review_style": "thorough"
                    }
                },
                {
                    "type": "qa",
                    "config": {
                        "focus": ["testing", "user_experience", "edge_cases"],
                        "testing_types": ["unit", "integration", "e2e"]
                    }
                }
            ],
            "workflow": {
                "rounds": 5,
                "reflection_frequency": 2,
                "quality_gates": ["code_review", "comprehensive_testing", "security_review"]
            }
        },
        
        "research-team": {
            "agents": [
                {
                    "type": "pm",
                    "config": {
                        "focus": "exploration and prototyping",
                        "risk_tolerance": "high"
                    }
                },
                {
                    "type": "engineer",
                    "config": {
                        "experimental": True,
                        "languages": ["python"],
                        "focus": "proof of concept"
                    }
                },
                {
                    "type": "qa",
                    "config": {
                        "focus": ["feasibility", "proof_of_concept"],
                        "testing_types": ["exploratory", "feasibility"]
                    }
                }
            ],
            "workflow": {
                "rounds": 4,
                "reflection_frequency": 1,
                "quality_gates": ["feasibility_check", "concept_validation"]
            }
        }
    }


def create_default_configs():
    """Create default configuration files if they don't exist."""
    config_dir = get_config_dir()
    config_dir.mkdir(exist_ok=True)
    
    # Create autogen_config.yaml
    autogen_config_path = config_dir / "autogen_config.yaml"
    if not autogen_config_path.exists():
        autogen_config = {
            "llm_config": {
                "model": "gpt-4",
                "api_key": "${OPENAI_API_KEY}",
                "temperature": 0.1,
                "max_tokens": 2000
            },
            "runtime_config": {
                "code_execution": True,
                "execution_timeout": 30,
                "max_consecutive_auto_reply": 10
            },
            "logging": {
                "level": "INFO",
                "autogen_logs": True,
                "conversation_logs": True
            }
        }
        
        with open(autogen_config_path, 'w') as f:
            yaml.dump(autogen_config, f, default_flow_style=False)
    
    # Create squad_profiles.yaml
    profiles_path = config_dir / "squad_profiles.yaml"
    if not profiles_path.exists():
        profiles_config = {
            "profiles": get_default_squad_profiles()
        }
        
        with open(profiles_path, 'w') as f:
            yaml.dump(profiles_config, f, default_flow_style=False) 