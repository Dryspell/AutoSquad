"""
AutoSquad: Autonomous Multi-Agent Development Framework

Built on Microsoft's AutoGen framework for orchestrating specialized development teams.
"""

__version__ = "0.1.0"
__author__ = "AutoSquad Team"

from .cli import main
from .orchestrator import SquadOrchestrator
from .project_manager import ProjectManager

__all__ = ["main", "SquadOrchestrator", "ProjectManager"] 