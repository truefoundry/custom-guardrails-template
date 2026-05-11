import copy
import logging
from typing import Any

from entities import InputGuardrailRequest
from presidio_entities import DEFAULT_LANGUAGE, DEFAULT_RECOGNIZERS, parse_recognizers, get_analyzer, anonymizer

# Configure logging
logger = logging.getLogger(__name__)


def _response(verdict: bool, transformed: bool, result: dict[str, Any]) -> dict[str, Any]:
    """AI Gateway mutate contract: 2xx JSON with verdict, transformed, and full requestBody in result."""
    return {"verdict": verdict, "transformed": transformed, "result": result}


def process_input_guardrail(request: InputGuardrailRequest) -> dict[str, Any]:
    body = copy.deepcopy(request.requestBody)

    if not request.config.get("transform_input", False):
        logger.debug("Transform input disabled, skipping PII redaction")
        return _response(True, False, body)

    recognizer_config = request.config.get("recognizers", DEFAULT_RECOGNIZERS)
    language = request.config.get("language", DEFAULT_LANGUAGE)

    try:
        recognizers = parse_recognizers(recognizer_config)
        analyzer = get_analyzer(recognizers, language)

        messages = body.get("messages", [])
        transformed = False
        transformed_messages: list[dict[str, Any]] = []

        for message in messages:
            if isinstance(message, dict) and message.get("content"):
                results = analyzer.analyze(text=message["content"], language=language)
                anonymized_content = anonymizer.anonymize(
                    text=message["content"],
                    analyzer_results=results,
                )
                if anonymized_content.text != message["content"]:
                    transformed = True
                    logger.info(
                        f"PII detected and redacted. "
                        f"Entities found: {[r.entity_type for r in results]}"
                    )
                transformed_messages.append(
                    {"role": message["role"], "content": anonymized_content.text}
                )

        if transformed:
            body["messages"] = transformed_messages
        else:
            logger.debug("No PII detected")

        return _response(True, transformed, body)

    except Exception as e:
        logger.error(f"Error during PII redaction: {str(e)}", exc_info=True)
        raise
