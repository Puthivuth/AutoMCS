"""Backward compatibility stub for DeepSeek provider."""
from .gemini import GeminiProvider, get_provider

# Alias for backwards compatibility with any serialized references
DeepSeekProvider = GeminiProvider

__all__ = ["DeepSeekProvider", "get_provider"]
