from openai import OpenAI
from openai.types.responses import ResponseCreatedEvent, ResponseOutputItemDoneEvent, ResponseTextDeltaEvent

from core.config import get_config
from core.logging_utils import get_logger, log_activity

logger = get_logger(__name__)


def _char_count(value) -> int:
    if value is None:
        return 0
    try:
        return len(value)  # type: ignore[arg-type]
    except TypeError:
        return len(str(value))


def generate_answer(prompt: str) -> str:
    config = get_config()
    client = OpenAI(api_key=config.openai_api_key)
    with log_activity(
        logger,
        "llm.generate_answer",
        details={"chars": len(prompt)},
    ):
        stream = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            instructions="You are a helpful assistant.",
            stream=True
        )
        for event in stream:
            if isinstance(event, ResponseCreatedEvent):
                logger.info("Response stream created")
            elif isinstance(event, ResponseTextDeltaEvent):
                logger.debug("Streaming text delta", extra={"chars": _char_count(event.delta)})
                yield event.delta
            elif isinstance(event, ResponseOutputItemDoneEvent):
                text = event.item.content[0].text
                logger.info("LLM response complete", extra={"chars": _char_count(text)})
                yield text
