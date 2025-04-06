"""Custom exceptions for the assistant application."""

class AssistantError(Exception):
    """Base exception class for the assistant."""
    pass

class ConfigError(AssistantError):
    """Exception raised for configuration errors."""
    pass

class ScreenshotError(AssistantError):
    """Exception raised for errors during screen capture."""
    pass

class DesktopControlError(AssistantError):
    """Exception raised for errors during desktop interaction (mouse/keyboard)."""
    pass

class LLMError(AssistantError):
    """Exception raised for errors interacting with the LLM service."""
    pass

class VLMError(AssistantError):
    """Exception raised for errors interacting with the VLM service."""
    pass

class OrchestrationError(AssistantError):
    """Exception raised for errors during plan execution."""
    pass