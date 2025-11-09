"""
Ad-hoc playground helpers for experimenting with microphone capture and STT.

Run this module directly to try the streaming transcription demo:

    python -m core.playground
"""

from __future__ import annotations

from pathlib import Path

from audio_input.microphone import MicrophoneInput
from audio_output.stt import STTOpenAI
from audio_output.tts import generate_speech, generate_speech_elevenlabs
from llm.openai import generate_answer
from core.logging_utils import get_logger, log_activity

logger = get_logger(__name__)


def example_batch_transcription() -> None:
    """Capture audio, save to WAV, and run classic Whisper transcription."""
    output_path = Path("vad_recording.wav")
    with log_activity(
        logger,
        "playground.batch_transcription",
        details={"output_path": str(output_path)},
    ):
        with MicrophoneInput() as mic:
            print("Press Enter to record 5 seconds (batch transcription demo)...")
            input()
            audio_chunk = mic.record(duration_seconds=5.0)
            MicrophoneInput.save_wav(audio_chunk, output_path)

        stt = STTOpenAI()
        result = stt.transcribe_path(output_path)
        print(f"[Batch] Transcript: {result.text}")
        logger.info(
            "Batch transcription complete chars=%s",
            len(result.text),
        )


def example_streaming_transcription() -> None:
    """Stream microphone audio to OpenAI while recording and print partial transcripts."""
    stt = STTOpenAI()
    with log_activity(logger, "playground.streaming_transcription"):
        with MicrophoneInput() as mic:
            print("Press Enter to start realtime transcription (~5 seconds)...")
            input()
            latest_partial = None
            stream = mic.stream(duration_seconds=5.0)
            for partial in stt.stream_transcribe(stream, instructions="Transcribe speech."):
                latest_partial = partial
                print(f"[Stream] {partial.text}")
                logger.debug(
                    "Received streaming partial chars=%s",
                    len(partial.text),
                )

        if latest_partial:
            print(f"[Stream] Final transcript: {latest_partial.text}")
            logger.info(
                "Realtime transcription finished chars=%s",
                len(latest_partial.text),
            )


if __name__ == "__main__":
    #example_streaming_transcription()
    logger.info("Launching playground demo")
    last = ""
    for partial in STTOpenAI().stream_transcribe_file(Path("vad_recording.wav")):
        last = partial.text
        logger.debug("Playground stream partial chars=%s", len(partial.text))
    for answer in generate_answer(last):
        logger.debug("LLM answer chunk chars=%s", len(answer))
    
    generate_speech_elevenlabs(answer)
    logger.info("TTS file updated")
