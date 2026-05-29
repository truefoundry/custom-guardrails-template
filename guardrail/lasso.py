import copy
import logging
import os
import uuid
from typing import Any, Optional

import requests
from fastapi import HTTPException

from entities import (
    InputGuardrailRequest,
    MutateGuardrailResponse,
    OutputGuardrailRequest,
    ValidateGuardrailResponse,
)

logger = logging.getLogger(__name__)

DEFAULT_API_BASE = "https://server.lasso.security/gateway/v3"
DEFAULT_TIMEOUT = 10.0


INVALID_API_KEY_MESSAGE = (
    "Invalid Lasso API key. Verify config.credentials.apiKey or LASSO_API_KEY."
)

_INVALID_API_KEY_PHRASES = (
    "invalid api key",
    "invalid lasso-api-key",
    "invalid apikey",
    "api key is invalid",
    "api key invalid",
    "invalid key",
    "authentication failed",
    "unauthorized",
    "forbidden",
    "access denied",
)


class LassoApiError(Exception):
    """Raised when the Lasso API returns a non-success response or malformed payload."""

    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _parse_lasso_error_body(response: requests.Response) -> Optional[dict[str, Any]]:
    try:
        data = response.json()
        return data if isinstance(data, dict) else None
    except ValueError:
        return None


def _body_indicates_invalid_api_key(status_code: int, body_text: str, body_json: Optional[dict[str, Any]]) -> bool:
    if status_code in (401, 403):
        return True

    haystack = body_text.lower()
    if any(phrase in haystack for phrase in _INVALID_API_KEY_PHRASES):
        return True

    if not body_json:
        return False

    for field in ("message", "error", "detail", "description", "title"):
        value = body_json.get(field)
        if isinstance(value, str) and any(phrase in value.lower() for phrase in _INVALID_API_KEY_PHRASES):
            return True

    errors = body_json.get("errors")
    if isinstance(errors, list):
        for item in errors:
            if isinstance(item, str) and any(phrase in item.lower() for phrase in _INVALID_API_KEY_PHRASES):
                return True
            if isinstance(item, dict):
                msg = item.get("message") or item.get("detail") or item.get("error")
                if isinstance(msg, str) and any(phrase in msg.lower() for phrase in _INVALID_API_KEY_PHRASES):
                    return True

    return False


def _lasso_http_error(response: requests.Response) -> LassoApiError:
    body_text = response.text or ""
    body_json = _parse_lasso_error_body(response)

    if _body_indicates_invalid_api_key(response.status_code, body_text, body_json):
        return LassoApiError(INVALID_API_KEY_MESSAGE, status_code=401)

    if body_json:
        for field in ("message", "detail", "error", "description"):
            value = body_json.get(field)
            if isinstance(value, str) and value.strip():
                return LassoApiError(
                    f"Lasso API error: {value.strip()}",
                    status_code=502 if response.status_code >= 500 else response.status_code,
                )

    if body_text.strip():
        return LassoApiError(
            f"Lasso API returned {response.status_code}: {body_text.strip()}",
            status_code=502 if response.status_code >= 500 else response.status_code,
        )

    return LassoApiError(
        f"Lasso API returned {response.status_code}",
        status_code=502 if response.status_code >= 500 else response.status_code,
    )


def _get_config_value(config: Optional[dict[str, Any]], *keys: str, default: Any = None) -> Any:
    if not config:
        return default
    value: Any = config
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    return value if value is not None else default


def _resolve_api_key(config: Optional[dict[str, Any]]) -> str:
    api_key = (
        _get_config_value(config, "credentials", "apiKey")
        or _get_config_value(config, "apiKey")
        or os.getenv("LASSO_API_KEY")
    )
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Lasso API key not configured. Set config.credentials.apiKey or LASSO_API_KEY.",
        )
    return api_key


def _resolve_api_base(config: Optional[dict[str, Any]]) -> str:
    base = _get_config_value(config, "api_base") or os.getenv("LASSO_API_BASE", DEFAULT_API_BASE)
    return base.rstrip("/")


def _resolve_timeout(config: Optional[dict[str, Any]]) -> float:
    timeout = _get_config_value(config, "timeout", default=DEFAULT_TIMEOUT)
    return float(timeout)


def _resolve_session_id(request: InputGuardrailRequest | OutputGuardrailRequest) -> str:
    session_id = _get_config_value(request.config, "sessionId")
    if session_id:
        return str(session_id)
    metadata = request.context.metadata or {}
    for key in ("session_id", "sessionId", "lasso-conversation-id"):
        if metadata.get(key):
            return str(metadata[key])
    return str(uuid.uuid4())


def _resolve_user_id(request: InputGuardrailRequest | OutputGuardrailRequest) -> Optional[str]:
    user_id = _get_config_value(request.config, "userId")
    if user_id:
        return str(user_id)
    user = request.context.user or {}
    for key in ("subjectSlug", "subjectId"):
        if user.get(key):
            return str(user[key])
    return None


def _extract_messages_from_request_body(body: dict[str, Any]) -> list[dict[str, str]]:
    messages = body.get("messages", [])
    result: list[dict[str, str]] = []
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") is not None and msg.get("content") is not None:
            result.append({"role": str(msg["role"]), "content": str(msg["content"])})
    return result


def _extract_messages_from_response_body(body: dict[str, Any]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for choice in body.get("choices", []):
        if not isinstance(choice, dict):
            continue
        message = choice.get("message", {})
        if isinstance(message, dict) and message.get("content") is not None:
            role = message.get("role", "assistant")
            messages.append({"role": str(role), "content": str(message["content"])})
    return messages


def _build_lasso_payload(
    messages: list[dict[str, str]],
    message_type: str,
    session_id: str,
    user_id: Optional[str],
    tools: list[Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "messages": messages,
        "messageType": message_type,
        "sessionId": session_id,
        "tools": tools,
    }
    if user_id:
        payload["userId"] = user_id
    return payload


def _block_details(findings: dict[str, Any]) -> tuple[bool, str]:
    details: list[str] = []
    for deputy, deputy_findings in findings.items():
        if not isinstance(deputy_findings, list):
            continue
        for finding in deputy_findings:
            if not isinstance(finding, dict):
                continue
            if finding.get("action") == "BLOCK":
                name = finding.get("name", "violation")
                severity = finding.get("severity", "")
                suffix = f" ({severity})" if severity else ""
                details.append(f"{deputy}/{name}{suffix}")
    if details:
        return True, "; ".join(details)
    return False, ""


def _finding_has_mask_span(finding: dict[str, Any]) -> bool:
    return (
        finding.get("start") is not None
        and finding.get("end") is not None
        and bool(finding.get("mask"))
    )


def _blocking_without_mask_spans(findings: dict[str, Any]) -> tuple[bool, str]:
    """BLOCK findings that classifix cannot redact via start/end/mask metadata."""
    details: list[str] = []
    for deputy, deputy_findings in findings.items():
        if not isinstance(deputy_findings, list):
            continue
        for finding in deputy_findings:
            if not isinstance(finding, dict):
                continue
            if finding.get("action") != "BLOCK":
                continue
            if _finding_has_mask_span(finding):
                continue
            name = finding.get("name", "violation")
            severity = finding.get("severity", "")
            suffix = f" ({severity})" if severity else ""
            details.append(f"{deputy}/{name}{suffix}")
    if details:
        return True, "; ".join(details)
    return False, ""


def _extract_mask_spans(findings: dict[str, Any]) -> list[tuple[int, int, int, str]]:
    spans: list[tuple[int, int, int, str]] = []
    for deputy_findings in findings.values():
        if not isinstance(deputy_findings, list):
            continue
        for finding in deputy_findings:
            if not isinstance(finding, dict) or not _finding_has_mask_span(finding):
                continue
            spans.append(
                (
                    int(finding.get("message_index", 0)),
                    int(finding["start"]),
                    int(finding["end"]),
                    str(finding["mask"]),
                )
            )
    return spans


def _apply_mask_spans_to_text(content: str, spans: list[tuple[int, int, str]]) -> str:
    updated = content
    for start, end, mask in sorted(spans, key=lambda item: item[0], reverse=True):
        if 0 <= start < end <= len(updated):
            updated = updated[:start] + mask + updated[end:]
    return updated


def _apply_finding_masks(
    body: dict[str, Any],
    findings: dict[str, Any],
    *,
    is_output: bool,
) -> tuple[dict[str, Any], bool]:
    spans = _extract_mask_spans(findings)
    if not spans:
        return body, False

    updated = copy.deepcopy(body)
    by_message: dict[int, list[tuple[int, int, str]]] = {}
    for message_index, start, end, mask in spans:
        by_message.setdefault(message_index, []).append((start, end, mask))

    transformed = False
    if is_output:
        choices = updated.get("choices", [])
        for message_index, message_spans in by_message.items():
            if message_index >= len(choices):
                continue
            choice = choices[message_index]
            if not isinstance(choice, dict):
                continue
            message = choice.get("message")
            if not isinstance(message, dict) or message.get("content") is None:
                continue
            original = str(message["content"])
            masked = _apply_mask_spans_to_text(original, message_spans)
            if masked != original:
                message["content"] = masked
                transformed = True
        return updated, transformed

    messages = updated.get("messages", [])
    if not isinstance(messages, list):
        return updated, False

    for message_index, message_spans in by_message.items():
        if message_index >= len(messages):
            continue
        message = messages[message_index]
        if not isinstance(message, dict) or message.get("content") is None:
            continue
        original = str(message["content"])
        masked = _apply_mask_spans_to_text(original, message_spans)
        if masked != original:
            message["content"] = masked
            transformed = True

    return updated, transformed


def _call_lasso(
    *,
    endpoint: str,
    payload: dict[str, Any],
    api_key: str,
    api_base: str,
    timeout: float,
    conversation_id: Optional[str],
    user_id: Optional[str],
) -> dict[str, Any]:
    url = f"{api_base}/{endpoint}"
    headers = {
        "lasso-api-key": api_key,
        "Content-Type": "application/json",
    }
    if conversation_id:
        headers["lasso-conversation-id"] = conversation_id
    if user_id:
        headers["lasso-user-id"] = user_id

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.error("Lasso API request failed: %s", exc)
        raise LassoApiError(f"Failed to connect to Lasso API: {exc}") from exc

    if not response.ok:
        logger.error("Lasso API error %s: %s", response.status_code, response.text)
        raise _lasso_http_error(response)

    try:
        return response.json()
    except ValueError as exc:
        raise LassoApiError(f"Invalid JSON from Lasso API: {exc}") from exc


def _invoke_lasso(
    request: InputGuardrailRequest | OutputGuardrailRequest,
    *,
    endpoint: str,
    message_type: str,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    if not messages:
        return {"violations_detected": False, "deputies": {}, "findings": {}}

    config = request.config
    api_key = _resolve_api_key(config)
    api_base = _resolve_api_base(config)
    timeout = _resolve_timeout(config)
    session_id = _resolve_session_id(request)
    user_id = _resolve_user_id(request)
    conversation_id = _get_config_value(config, "conversationId") or session_id

    tools = []
    if isinstance(request, InputGuardrailRequest):
        tools = request.requestBody.get("tools") or []

    payload = _build_lasso_payload(messages, message_type, session_id, user_id, tools)
    return _call_lasso(
        endpoint=endpoint,
        payload=payload,
        api_key=api_key,
        api_base=api_base,
        timeout=timeout,
        conversation_id=conversation_id,
        user_id=user_id,
    )


def _validate_response(lasso_response: dict[str, Any]) -> ValidateGuardrailResponse:
    blocked, detail = _block_details(lasso_response.get("findings", {}))
    if blocked:
        return ValidateGuardrailResponse(
            verdict=False,
            message=f"Lasso guardrail blocked: {detail}",
        )
    if lasso_response.get("violations_detected"):
        logger.info("Lasso reported violations without BLOCK action (e.g. WARN); allowing request")
    return ValidateGuardrailResponse(verdict=True)


def _apply_masked_messages(
    body: dict[str, Any],
    masked_messages: list[dict[str, Any]],
    *,
    is_output: bool,
) -> tuple[dict[str, Any], bool]:
    updated = copy.deepcopy(body)
    if is_output:
        choices = updated.get("choices", [])
        if not choices or not masked_messages:
            return updated, False
        choice = choices[0]
        if isinstance(choice, dict) and isinstance(choice.get("message"), dict):
            choice["message"]["content"] = masked_messages[0].get("content", choice["message"].get("content"))
            if len(masked_messages) > 1:
                logger.warning("Lasso returned multiple masked completion messages; applied first only")
            return updated, True
        return updated, False

    original = updated.get("messages", [])
    if not isinstance(original, list) or not masked_messages:
        return updated, False

    if len(masked_messages) != len(original):
        updated["messages"] = masked_messages
        return updated, True

    content_changed = any(
        isinstance(orig, dict)
        and isinstance(masked, dict)
        and str(orig.get("content", "")) != str(masked.get("content", ""))
        for orig, masked in zip(original, masked_messages)
    )
    if content_changed:
        updated["messages"] = masked_messages
        return updated, True
    return updated, False


def _mutate_response(
    body: dict[str, Any],
    lasso_response: dict[str, Any],
    *,
    is_output: bool,
) -> MutateGuardrailResponse:
    findings = lasso_response.get("findings", {}) or {}

    result = copy.deepcopy(body)
    transformed = False

    masked_messages = lasso_response.get("messages")
    if masked_messages:
        result, transformed = _apply_masked_messages(
            result, masked_messages, is_output=is_output
        )

    if not transformed:
        result, transformed = _apply_finding_masks(result, findings, is_output=is_output)

    block_without_mask, detail = _blocking_without_mask_spans(findings)
    if block_without_mask:
        return MutateGuardrailResponse(verdict=False, transformed=False, result=body)

    if transformed:
        return MutateGuardrailResponse(verdict=True, transformed=True, result=result)

    if lasso_response.get("violations_detected"):
        logger.info("Lasso violations detected on classifix without message transformation")
    return MutateGuardrailResponse(verdict=True, transformed=False, result=result)


def _handle_lasso_error(exc: Exception) -> None:
    if isinstance(exc, LassoApiError):
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    logger.exception("Unexpected Lasso guardrail error")
    raise HTTPException(status_code=500, detail=f"Lasso guardrail error: {exc}") from exc


def lasso_classify_input(request: InputGuardrailRequest) -> ValidateGuardrailResponse:
    """Validate user input (pre-call) via Lasso POST /classify."""
    try:
        messages = _extract_messages_from_request_body(request.requestBody)
        lasso_response = _invoke_lasso(
            request, endpoint="classify", message_type="PROMPT", messages=messages
        )
        return _validate_response(lasso_response)
    except HTTPException:
        raise
    except Exception as exc:
        _handle_lasso_error(exc)


def lasso_classify_output(request: OutputGuardrailRequest) -> ValidateGuardrailResponse:
    """Validate model output (post-call) via Lasso POST /classify."""
    try:
        messages = _extract_messages_from_response_body(request.responseBody)
        lasso_response = _invoke_lasso(
            request, endpoint="classify", message_type="COMPLETION", messages=messages
        )
        return _validate_response(lasso_response)
    except HTTPException:
        raise
    except Exception as exc:
        _handle_lasso_error(exc)


def lasso_classifix_input(request: InputGuardrailRequest) -> MutateGuardrailResponse:
    """Validate and mask PII in user input via Lasso POST /classifix."""
    try:
        body = copy.deepcopy(request.requestBody)
        messages = _extract_messages_from_request_body(body)
        lasso_response = _invoke_lasso(
            request, endpoint="classifix", message_type="PROMPT", messages=messages
        )
        return _mutate_response(body, lasso_response, is_output=False)
    except HTTPException:
        raise
    except Exception as exc:
        _handle_lasso_error(exc)


def lasso_classifix_output(request: OutputGuardrailRequest) -> MutateGuardrailResponse:
    """Validate and mask PII in model output via Lasso POST /classifix."""
    try:
        body = copy.deepcopy(request.responseBody)
        messages = _extract_messages_from_response_body(body)
        lasso_response = _invoke_lasso(
            request, endpoint="classifix", message_type="COMPLETION", messages=messages
        )
        return _mutate_response(body, lasso_response, is_output=True)
    except HTTPException:
        raise
    except Exception as exc:
        _handle_lasso_error(exc)
