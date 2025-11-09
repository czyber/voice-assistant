from types import SimpleNamespace
from pathlib import Path
import json
import sys

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.append(project_root)

from audio_output.stt import STTOpenAI, _merge_transcript
from core import AudioChunk, TranscribedText


class DummyConfig:
    openai_api_key = "test-key"
    openai_organization = ""


class DummyOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        self.audio = SimpleNamespace(
            transcriptions=SimpleNamespace(
                create=lambda *a, **k: SimpleNamespace(text="", language=None, segments=None)
            )
        )


class FakeWebSocket:
    def __init__(self, events: list[dict]) -> None:
        self.events = events
        self.sent_messages: list[dict] = []
        self.timeout_values: list[float | None] = []
        self.closed = False

    def send(self, message: str) -> None:
        self.sent_messages.append(json.loads(message))

    def recv(self):
        if not self.events:
            return None
        event = self.events.pop(0)
        return json.dumps(event)

    def settimeout(self, value: float | None) -> None:
        self.timeout_values.append(value)

    def close(self) -> None:
        self.closed = True


def make_chunk() -> AudioChunk:
    return AudioChunk(
        data=b"\x01\x00" * 4096,
        sample_rate=16_000,
        timestamp=0.0,
        channels=1,
        sample_width=2,
    )


def test_stream_transcribe_realtime(monkeypatch):
    import audio_output.stt as stt_module

    fake_events = [
        {"type": "input_audio_buffer.committed", "item_id": "item_001"},
        {
            "type": "conversation.item.input_audio_transcription.delta",
            "item_id": "item_001",
            "delta": "hi",
        },
        {
            "type": "conversation.item.input_audio_transcription.completed",
            "item_id": "item_001",
            "transcript": "hi there",
        },
    ]
    fake_ws = FakeWebSocket(fake_events)

    monkeypatch.setattr(stt_module, "websocket", SimpleNamespace(create_connection=lambda *a, **k: fake_ws))
    monkeypatch.setattr(stt_module, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(stt_module, "get_config", lambda: DummyConfig())

    stt = STTOpenAI()
    assert stt.realtime_model == "gpt-4o-realtime-preview"
    assert stt.transcription_model == "gpt-4o-transcribe"

    results = list(
        stt.stream_transcribe([make_chunk()], instructions="test", commit_every_chunk=True)
    )
    assert [res.text for res in results] == ["hi", "hi there"]

    # Ensure audio was appended and commits were issued (per chunk + final)
    message_types = [msg["type"] for msg in fake_ws.sent_messages]
    assert "session.update" in message_types
    assert message_types.count("input_audio_buffer.append") >= 1
    assert message_types.count("input_audio_buffer.commit") >= 2

    session_updates = [msg for msg in fake_ws.sent_messages if msg["type"] == "session.update"]
    assert session_updates
    session_body = session_updates[0]["session"]
    assert session_body["type"] == "transcription"
    transcription_cfg = session_body["audio"]["input"]["transcription"]
    assert transcription_cfg["model"] == "gpt-4o-transcribe"
    assert transcription_cfg["prompt"] == "test"

    assert fake_ws.closed


def test_merge_transcript_handles_final_overwrite():
    base = "hi"
    rewritten = _merge_transcript(base, "hi there", True)
    assert rewritten == "hi there"


def test_stream_transcribe_file_streaming(monkeypatch, tmp_path):
    import audio_output.stt as stt_module

    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake-audio")

    fake_stream_events = ["hi", " there"]

    class FakeStream:
        def __init__(self) -> None:
            self._events = iter(fake_stream_events)
            self.final_response = SimpleNamespace(text="hi there")

        def __iter__(self):
            return self

        def __next__(self):
            return next(self._events)

    captured_kwargs: dict[str, object] = {}

    def fake_create(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return FakeStream()

    monkeypatch.setattr(stt_module, "OpenAI", DummyOpenAI)
    monkeypatch.setattr(stt_module, "get_config", lambda: DummyConfig())

    stt = STTOpenAI()
    stt._client = SimpleNamespace(
        audio=SimpleNamespace(
            transcriptions=SimpleNamespace(create=fake_create)
        )
    )

    generator = stt.stream_transcribe_file(
        audio_path, model="gpt-4o-mini-transcribe"
    )

    partials: list[TranscribedText] = []
    try:
        while True:
            partials.append(next(generator))
    except StopIteration as stop:
        final = stop.value

    assert [partial.text for partial in partials] == ["hi", "hi there"]
    assert final.text == "hi there"

    assert captured_kwargs["stream"] is True
    assert captured_kwargs["response_format"] == "text"
    assert captured_kwargs["model"] == "gpt-4o-mini-transcribe"
