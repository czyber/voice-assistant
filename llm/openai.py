import json
from openai import OpenAI
from openai.types.responses import ResponseCreatedEvent, ResponseFunctionCallArgumentsDeltaEvent, ResponseFunctionToolCall, ResponseOutputItemAddedEvent, ResponseOutputItemDoneEvent, ResponseTextDeltaEvent

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

tools = [
    {
        "type": "function",
        "name": "get_horoscope",
        "description": "Get today's horoscope for an astrological sign.",
        "parameters": {
            "type": "object",
            "properties": {
                "sign": {
                    "type": "string",
                    "description": "An astrological sign like Taurus or Aquarius",
                },
            },
            "required": ["sign"],
        },
    },
]

def get_horoscope(sign):
    return f"{sign}: Next Tuesday you will befriend a baby otter."

def generate_answer(prompt: str) -> str:
    config = get_config()
    client = OpenAI(api_key=config.openai_api_key)
    with log_activity(
        logger,
        "llm.generate_answer",
        details={"chars": len(prompt)},
    ):
        text = "I am a Aquarius, what is my horoscope"
        final_tool_calls = {}
        stream = client.responses.create(
            model="gpt-4o-mini",
            input=text,
            tools=tools,
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
                if event.item.type == "function_call":
                    if event.item.name == "get_horoscope":
                        result = get_horoscope(**json.loads(event.item.arguments))
                        logger.info("Called tool", extra={"tool": event.item.name, "arguments": event.item.arguments, "result": result})
                        yield result
                        
                else:
                    text = event.item.content[0].text
                    logger.info("LLM response complete", extra={"chars": _char_count(text)})
                    yield text
            elif isinstance(event, ResponseOutputItemAddedEvent):
                final_tool_calls[event.output_index] = event.item;
            elif isinstance(event, ResponseFunctionCallArgumentsDeltaEvent):
                index = event.output_index
                if final_tool_calls[index]:
                    final_tool_calls[index].arguments += event.delta
