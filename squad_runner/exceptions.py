"""
Custom exceptions for AutoSquad CLI operations.
"""


class AutoSquadError(Exception):
    """Base exception for all AutoSquad errors."""
    pass


class ConfigurationError(AutoSquadError):
    """Raised when there are configuration-related issues."""
    pass


class ProjectError(AutoSquadError):
    """Raised when there are project-related issues."""
    pass


class APIError(AutoSquadError):
    """Raised when there are API connectivity or authentication issues."""
    pass


class ValidationError(AutoSquadError):
    """Raised when input validation fails."""
    pass


class SquadProfileError(AutoSquadError):
    """Raised when there are squad profile-related issues."""
    pass


class ModelError(AutoSquadError):
    """Raised when there are model-related issues."""
    pass 