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
from typing import Optional, Generator

try:
    import pyaudio
except ModuleNotFoundError as exc:  # pragma: no cover - import-time guard
    raise ModuleNotFoundError(
        "PyAudio is required for microphone capture. "
        "Install system PortAudio headers (e.g. `brew install portaudio`) "
        "then run `pip install pyaudio`."
    ) from exc

from core import AudioChunk, IAudioInput
from core.logging_utils import get_logger, log_activity

logger = get_logger(__name__)


class MicrophoneInput(IAudioInput):
    """Capture audio from the default system microphone."""

    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        channels: int = 1,
        chunk_size: int = 4_096,
        format_: Optional[int] = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self._pyaudio = pyaudio.PyAudio()
        self._stream = None
        self._format = format_ if format_ is not None else pyaudio.paInt16
        self.sample_width = self._pyaudio.get_sample_size(self._format)
        logger.info(
            "Initialized microphone adapter sample_rate=%s channels=%s chunk_size=%s format=%s",
            sample_rate,
            channels,
            chunk_size,
            self._format,
        )

    def stream(
            self,
            *,
            max_chunks: Optional[int] = None,
            duration_seconds: Optional[float] = None,
    ) -> Generator[AudioChunk, None, None]:
        logger.info(
            "Opening live microphone stream sample_rate=%s channels=%s chunk_size=%s max_chunks=%s duration_seconds=%s",
            self.sample_rate,
            self.channels,
            self.chunk_size,
            max_chunks,
            duration_seconds,
        )
        stream = self._pyaudio.open(
            format=self._format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

        try:
            chunks_yielded = 0
            start_time = time.time()
            while True:
                if max_chunks is not None and chunks_yielded >= max_chunks:
                    break

                timestamp = time.time()
                if (
                    duration_seconds is not None
                    and (timestamp - start_time) >= duration_seconds
                ):
                    break

                chunk = stream.read(self.chunk_size, exception_on_overflow=False)
                logger.debug(
                    "Captured chunk #%s bytes=%s timestamp=%s",
                    chunks_yielded + 1,
                    len(chunk),
                    timestamp,
                )
                yield AudioChunk(
                    data=chunk,
                    sample_rate=self.sample_rate,
                    timestamp=timestamp,
                    channels=self.channels,
                    sample_width=self.sample_width,
                )
                chunks_yielded += 1
        finally:
            stream.stop_stream()
            stream.close()
            logger.info("Closed live microphone stream")

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

        with log_activity(
            logger,
            "microphone.record",
            details={"duration_seconds": duration_seconds, "chunk_size": self.chunk_size},
        ):
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
                logger.debug("Closed fixed-duration recording stream")

        audio_chunk = AudioChunk(
            data=bytes(buffer),
            sample_rate=self.sample_rate,
            timestamp=timestamp,
            channels=self.channels,
            sample_width=self.sample_width,
        )
        logger.info(
            "Finished recording bytes=%s duration_seconds=%s sample_rate=%s",
            len(audio_chunk.data),
            duration_seconds,
            audio_chunk.sample_rate,
        )
        return audio_chunk

    def close(self) -> None:
        """Release underlying PyAudio resources."""
        if self._pyaudio is not None:
            self._pyaudio.terminate()
            self._pyaudio = None
            logger.info("Terminated PyAudio instance")

    def __enter__(self) -> "MicrophoneInput":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @staticmethod
    def save_wav(audio: AudioChunk, path: Path) -> None:
        """Persist an AudioChunk to a WAV file for manual testing."""
        logger.info(
            "Saving WAV path=%s sample_rate=%s channels=%s sample_width=%s bytes=%s",
            path,
            audio.sample_rate,
            audio.channels,
            audio.sample_width,
            len(audio.data),
        )
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(audio.channels)
            wav_file.setsampwidth(audio.sample_width)
            wav_file.setframerate(audio.sample_rate)
            wav_file.writeframes(audio.data)

    @staticmethod
    def save_stream_wav(
        chunks: list[AudioChunk], path: Path
    ) -> None:
        if not chunks:
            raise ValueError("No audio chunks to save.")
        logger.info(
            "Saving streamed WAV path=%s chunks=%s",
            path,
            len(chunks),
        )

        first_chunk = chunks[0]
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(first_chunk.channels)
            wav_file.setsampwidth(first_chunk.sample_width)
            wav_file.setframerate(first_chunk.sample_rate)
            for chunk in chunks:
                wav_file.writeframes(chunk.data)


def _prompt_and_record(output_path: Path) -> None:
    """Helper for `python -m audio_input.microphone` manual testing."""
    print("Press Enter to record 5 seconds of audio...")
    input()
    logger.info("Manual prompt acknowledged; recording 5 seconds")
    with MicrophoneInput() as mic:
        audio_chunk = mic.record(duration_seconds=5.0)
    MicrophoneInput.save_wav(audio_chunk, output_path)
    print(f"Saved recording to {output_path}. Play it back to verify clarity.")
    logger.info("Manual recording saved path=%s", output_path)


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    default_path = Path("test_recording.wav")
    _prompt_and_record(default_path)
