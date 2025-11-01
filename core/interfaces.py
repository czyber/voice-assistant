"""
Core data structures and interfaces shared across the voice assistant project.

These definitions act as the contract between independently developed modules.
If every contribution sticks to the types and abc.ABCs below, we can plug the
pieces together without surprises at the end of the sprint.
"""

import abc
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AudioChunk:
    """Raw audio data captured from a microphone."""

    data: bytes
    sample_rate: int
    timestamp: float
    channels: int = 1
    sample_width: int = 2  # bytes per sample, defaults to 16-bit audio


@dataclass(frozen=True)
class TranscribedText:
    """Text produced by the speech-to-text system."""

    text: str
    confidence: float
    language: Optional[str] = None


@dataclass(frozen=True)
class SynthesizedAudio:
    """Audio produced by the text-to-speech system."""

    audio_data: bytes
    format: str
    voice: Optional[str] = None


@dataclass(frozen=True)
class ToolResult:
    """Normalized return value from any tool invoked by the LLM."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class IAudioInput(abc.ABC):
    """Microphone adapters implement this interface."""

    @abc.abstractmethod
    def record(self, duration_seconds: float) -> AudioChunk:
        """
        Capture audio for a fixed duration and return it as an AudioChunk.

        Implementations should raise an exception if the microphone is
        unavailable or recording fails.
        """


class ISTTEngine(abc.ABC):
    """Speech-to-text adapters implement this interface."""

    @abc.abstractmethod
    def transcribe(self, audio: AudioChunk) -> TranscribedText:
        """Convert microphone audio into text."""


class ITTSEngine(abc.ABC):
    """Text-to-speech adapters implement this interface."""

    @abc.abstractmethod
    def synthesize(self, text: str) -> SynthesizedAudio:
        """Generate spoken audio for the supplied text."""

    @abc.abstractmethod
    def play(self, synthesized: SynthesizedAudio) -> None:
        """Play audio through the system speakers."""


class ITool(abc.ABC):
    """Tools encapsulate external capabilities such as Spotify control."""

    name: str

    @abc.abstractmethod
    def execute(self, action: str, **kwargs: Any) -> ToolResult:
        """
        Perform an action and return a normalized ToolResult.

        `action` is a high-level command such as "play" or "pause".
        Extra keyword arguments carry any contextual details the tool needs.
        """

