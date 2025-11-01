"""Core package exposing shared interfaces."""

from .interfaces import (
    AudioChunk,
    TranscribedText,
    SynthesizedAudio,
    ToolResult,
    IAudioInput,
    ISTTEngine,
    ITTSEngine,
    ITool,
)

__all__ = [
    "AudioChunk",
    "TranscribedText",
    "SynthesizedAudio",
    "ToolResult",
    "IAudioInput",
    "ISTTEngine",
    "ITTSEngine",
    "ITool",
]
