"""
Microphone capture module.

Usage (manual test):
    python -m audio_input.microphone
"""

from __future__ import annotations

import math
import time
import wave
from pathlib import Path
from typing import Optional

try:
    import pyaudio
except ModuleNotFoundError as exc:  # pragma: no cover - import-time guard
    raise ModuleNotFoundError(
        "PyAudio is required for microphone capture. "
        "Install system PortAudio headers (e.g. `brew install portaudio`) "
        "then run `pip install pyaudio`."
    ) from exc

from core import AudioChunk, IAudioInput


class MicrophoneInput(IAudioInput):
    """Capture audio from the default system microphone."""

    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        channels: int = 1,
        chunk_size: int = 1_024,
        format_: Optional[int] = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self._pyaudio = pyaudio.PyAudio()
        self._format = format_ if format_ is not None else pyaudio.paInt16
        self.sample_width = self._pyaudio.get_sample_size(self._format)

    def record(self, duration_seconds: float) -> AudioChunk:
        """Record microphone input for `duration_seconds`."""
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than zero")

        stream = self._pyaudio.open(
            format=self._format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )
        buffer = bytearray()
        timestamp = time.time()

        try:
            num_chunks = math.ceil(
                duration_seconds * self.sample_rate / self.chunk_size
            )
            for _ in range(num_chunks):
                chunk = stream.read(self.chunk_size, exception_on_overflow=False)
                buffer.extend(chunk)
        finally:
            stream.stop_stream()
            stream.close()

        return AudioChunk(
            data=bytes(buffer),
            sample_rate=self.sample_rate,
            timestamp=timestamp,
            channels=self.channels,
            sample_width=self.sample_width,
        )

    def close(self) -> None:
        """Release underlying PyAudio resources."""
        if self._pyaudio is not None:
            self._pyaudio.terminate()
            self._pyaudio = None

    def __enter__(self) -> "MicrophoneInput":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @staticmethod
    def save_wav(audio: AudioChunk, path: Path) -> None:
        """Persist an AudioChunk to a WAV file for manual testing."""
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(audio.channels)
            wav_file.setsampwidth(audio.sample_width)
            wav_file.setframerate(audio.sample_rate)
            wav_file.writeframes(audio.data)


def _prompt_and_record(output_path: Path) -> None:
    """Helper for `python -m audio_input.microphone` manual testing."""
    print("Press Enter to record 5 seconds of audio...")
    input()
    with MicrophoneInput() as mic:
        audio_chunk = mic.record(duration_seconds=5.0)
    MicrophoneInput.save_wav(audio_chunk, output_path)
    print(f"Saved recording to {output_path}. Play it back to verify clarity.")


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    default_path = Path("test_recording.wav")
    _prompt_and_record(default_path)
