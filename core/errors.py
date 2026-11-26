"""Custom exceptions for the CodeForge AI framework."""


class FrameworkError(Exception):
    """Base class for all framework errors."""


class ConfigError(FrameworkError):
    """Raised when configuration is missing or invalid."""


class MissingAPIKeyError(FrameworkError):
    """Raised when no OpenAI API key is available."""


class AIEngineError(FrameworkError):
    """Raised when the OpenAI API call fails after handling."""


class ValidationError(FrameworkError):
    """Raised when user input fails validation."""


class SafetyError(FrameworkError):
    """Raised when a request is blocked by domain safety rules."""
