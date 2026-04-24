import logging
import os
from typing import Any, Optional

import httpx
from fastapi import HTTPException

from entities import InputGuardrailRequest, OutputGuardrailRequest

logger = logging.getLogger(__name__)

OPERANT_URL = os.getenv(
    "OPERANT_URL", "https://pocgatekeeper.operant.ai/ai-firewall"
)
OPERANT_TIMEOUT_SECONDS = float(os.getenv("OPERANT_TIMEOUT_SECONDS", "10"))

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=OPERANT_TIMEOUT_SECONDS)
    return _client


def _build_headers() -> dict[str, str]:
    token = os.getenv("GUARDRAILS_TOKEN")
    if not token:
        raise HTTPException(
            status_code=500,
            detail="GUARDRAILS_TOKEN is not configured for the Operant guardrail",
        )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "source-gateway": "truefoundry-gateway",
        "x-upstream-gateway-type": "truefoundry",
    }


async def _call_operant(messages: list[dict]) -> dict[str, Any]:
    payload = {"requestBody": {"messages": messages}}
    try:
        response = await _get_client().post(
            OPERANT_URL, json=payload, headers=_build_headers()
        )
    except httpx.HTTPError as exc:
        logger.error("Operant /ai-firewall call failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=502, detail=f"Failed to reach Operant guardrail: {exc}"
        ) from exc

    if response.status_code >= 400:
        logger.error(
            "Operant returned non-2xx %s: %s", response.status_code, response.text
        )
        raise HTTPException(
            status_code=502,
            detail=f"Operant guardrail returned status {response.status_code}",
        )

    try:
        return response.json()
    except ValueError as exc:
        logger.error("Operant returned non-JSON body: %s", response.text)
        raise HTTPException(
            status_code=502, detail="Operant guardrail returned invalid JSON"
        ) from exc


async def process_operant_request(
    request: InputGuardrailRequest,
) -> Optional[dict]:
    messages = request.requestBody.get("messages", [])
    if not messages:
        logger.debug("No messages in requestBody, skipping Operant input scan")
        return None

    verdict_json = await _call_operant(messages)
    verdict = verdict_json.get("verdict")

    if verdict == "fail":
        message = verdict_json.get("message") or "Blocked by Operant guardrail"
        logger.info("Operant blocked input: %s", message)
        raise HTTPException(status_code=400, detail=message)

    if verdict == "pass":
        mutated_body = verdict_json.get("mutatedBody")
        if mutated_body:
            mutated_messages = mutated_body.get("messages")
            if mutated_messages is not None:
                request.requestBody["messages"] = mutated_messages
            for key, value in mutated_body.items():
                if key == "messages":
                    continue
                request.requestBody[key] = value
            logger.info("Operant redacted input request")
            return request.requestBody
        return None

    logger.warning("Operant returned unexpected verdict: %s", verdict_json)
    return None


async def process_operant_response(
    request: OutputGuardrailRequest,
) -> Optional[dict]:
    choices = request.responseBody.get("choices", []) or []
    indexed_messages: list[tuple[int, dict]] = []
    for idx, choice in enumerate(choices):
        message = choice.get("message") if isinstance(choice, dict) else None
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if content is None:
            continue
        indexed_messages.append(
            (idx, {"role": message.get("role", "assistant"), "content": content})
        )

    if not indexed_messages:
        logger.debug("No assistant messages found in responseBody, skipping Operant output scan")
        return None

    messages_to_send = [m for _, m in indexed_messages]
    verdict_json = await _call_operant(messages_to_send)
    verdict = verdict_json.get("verdict")

    if verdict == "fail":
        message = verdict_json.get("message") or "Blocked by Operant guardrail"
        logger.info("Operant blocked output: %s", message)
        raise HTTPException(status_code=400, detail=message)

    if verdict == "pass":
        mutated_response_body = verdict_json.get("mutatedResponseBody")
        if mutated_response_body:
            logger.info("Operant returned mutatedResponseBody for output")
            return mutated_response_body

        mutated_body = verdict_json.get("mutatedBody")
        if mutated_body:
            mutated_messages = mutated_body.get("messages") or []
            mutated = False
            for (orig_idx, _), mutated_msg in zip(indexed_messages, mutated_messages):
                if not isinstance(mutated_msg, dict):
                    continue
                new_content = mutated_msg.get("content")
                if new_content is None:
                    continue
                original_content = request.responseBody["choices"][orig_idx]["message"].get("content")
                if new_content != original_content:
                    request.responseBody["choices"][orig_idx]["message"]["content"] = new_content
                    mutated = True
            if mutated:
                logger.info("Operant redacted output response")
                return request.responseBody
        return None

    logger.warning("Operant returned unexpected verdict: %s", verdict_json)
    return None
