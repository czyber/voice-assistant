"""
Speech-to-text adapters backed by OpenAI APIs.

Provides both the classic Whisper file-based transcription and a realtime
streaming pipeline using the Realtime WebSocket API so we can forward
microphone audio chunks with lower perceived latency.
"""

from __future__ import annotations

import audioop
import base64
import io
import os
import json
import wave
from pathlib import Path
from typing import Any, Generator, Iterable, Optional
from urllib.parse import urlencode

from openai import OpenAI

try:  # pragma: no cover - optional dependency
    import websocket  # type: ignore
    from websocket import (  # type: ignore
        WebSocketConnectionClosedException,
        WebSocketTimeoutException,
        WebSocketBadStatusException,
    )
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    websocket = None  # type: ignore
    WebSocketConnectionClosedException = None  # type: ignore
    WebSocketTimeoutException = None  # type: ignore
    WebSocketBadStatusException = None  # type: ignore

from core import AudioChunk, ISTTEngine, TranscribedText
from core.config import get_config
from core.logging_utils import get_logger, log_activity

logger = get_logger(__name__)


def _char_count(value: object) -> int:
    if value is None:
        return 0
    try:
        return len(value)  # type: ignore[arg-type]
    except TypeError:
        return len(str(value))


class STTOpenAI(ISTTEngine):
    """Speech-to-text engine using OpenAI Whisper and the Realtime API."""

    def __init__(
        self,
        *,
        transcription_model: str = "gpt-4o-transcribe",
        realtime_model: str = "gpt-4o-realtime-preview",
    ) -> None:
        config = get_config()
        self.api_key = config.openai_api_key
        self.organization = config.openai_organization or None

        if not self.api_key:
            raise RuntimeError(
                "OpenAI API key missing. Add it to config.local.json under `openai.api_key`."
            )

        self._client = OpenAI(api_key=self.api_key, organization=self.organization)
        self.transcription_model = transcription_model
        self.realtime_model = realtime_model
        query = urlencode({"model": self.realtime_model})
        self._realtime_url = f"wss://api.openai.com/v1/realtime?{query}"
        logger.info(
            "Initialized STT client transcription_model=%s realtime_model=%s has_org=%s",
            self.transcription_model,
            self.realtime_model,
            bool(self.organization),
        )

    # ------------------------------------------------------------------
    # File-based transcription helpers
    # ------------------------------------------------------------------
    def transcribe_path(self, audio_path: Path) -> TranscribedText:
        ...
    def transcribe(self, audio: AudioChunk) -> TranscribedText:
        ...

    def stream_transcribe_file(
        self,
        audio_path: Path,
        *,
        model: Optional[str] = None,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> Generator[TranscribedText, None, TranscribedText]:

        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        with log_activity(
            logger,
            "stt.stream_transcribe_file",
            details={
                "audio_path": str(audio_path),
                "language": language or "auto",
                "prompt_supplied": bool(prompt),
                "model": model or "gpt-4o-mini-transcribe",
            },
        ):
            audio_file = open(Path.joinpath(Path(__file__).parent.parent, "core", audio_path), "rb")
            stream = client.audio.transcriptions.create(
                file=audio_file,
                model="gpt-4o-mini-transcribe",
                language=language,
                stream=True
            )

            for event in stream:
                if event.type == "transcript.text.delta":
                    logger.debug(
                        "Received partial transcript chars=%s",
                        _char_count(event.delta),
                    )
                    yield TranscribedText(text=event.delta, confidence=1.0)
                elif event.type == "transcript.text.done":
                    logger.info(
                        "Received final transcript chars=%s",
                        _char_count(event.text),
                    )
                    yield TranscribedText(text=event.text, confidence=1.0)

    # ------------------------------------------------------------------
    # Realtime streaming
    # ------------------------------------------------------------------
    def stream_transcribe(
        self,
        audio_stream: Iterable[AudioChunk],
        *,
        instructions: str = "Transcribe the provided audio into text only.",
        language: Optional[str] = None,
        commit_every_chunk: bool = False,
    ) -> Generator[TranscribedText, None, TranscribedText]:
        ... 
