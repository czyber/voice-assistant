
from pathlib import Path

from core.config import get_config
from core.logging_utils import get_logger, log_activity

logger = get_logger(__name__)


def _preview(text: str, limit: int = 80) -> str:
    normalized = " ".join(text.split())
    return (normalized[:limit] + "…") if len(normalized) > limit else normalized


def generate_speech(text: str) -> None:
    from openai import OpenAI

    instructions = """Voice: Warm, empathetic, and professional, reassuring the customer that their issue is understood and will be resolved.\n\nPunctuation: Well-structured with natural pauses, allowing for clarity and a steady, calming flow.\n\nDelivery: Calm and patient, with a supportive and understanding tone that reassures the listener.\n\nPhrasing: Clear and concise, using customer-friendly language that avoids jargon while maintaining professionalism.\n\nTone: Empathetic and solution-focused, emphasizing both understanding and proactive assistance."""
    config = get_config()
    client = OpenAI(api_key=config.openai_api_key)
    speech_file_path = Path(__file__).parent / "speech.mp3"

    with log_activity(
        logger,
        "tts.generate_speech_openai",
        details={"chars": len(text), "output_path": str(speech_file_path)},
    ):
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text,
            instructions=instructions,
        ) as response:
            logger.info("Streaming TTS audio chunk preview=%s", _preview(text))
            response.stream_to_file(speech_file_path)


def generate_speech_elevenlabs(text: str) -> None:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import save

    client = ElevenLabs(
        api_key=get_config().elevenlabs_api_key
    )

    with log_activity(
        logger,
        "tts.generate_speech_elevenlabs",
        details={"chars": len(text)},
    ):
        audio = client.text_to_speech.convert(
            text= "[calm]" + text + "[calm]",
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            #model_id="eleven_flash_v2_5",
            model_id="eleven_v3",
            output_format="mp3_44100_128",
        )

        logger.info("Received ElevenLabs audio buffer preview=%s", _preview(text))
        save(audio, Path(__file__).parent / "speech.mp3")
