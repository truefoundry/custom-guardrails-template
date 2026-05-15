"""Cisco AI Defense guardrail integration.

Calls the Cisco AI Defense Chat Inspection API
(`POST /api/v1/inspect/chat`) to evaluate prompts and completions for
security, safety, privacy and relevance violations.

API reference:
- https://developer.cisco.com/docs/ai-defense-inspection/inspect-conversations/
- https://pubhub.devnetcloud.com/media/ai-defense/docs/reference/openapi.json
"""

import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import HTTPException

from entities import InputGuardrailRequest, OutputGuardrailRequest


CISCO_REGION_HOSTS: Dict[str, str] = {
    "us": "https://us.api.inspect.aidefense.security.cisco.com",
    "eu": "https://eu.api.inspect.aidefense.security.cisco.com",
    "ap": "https://ap.api.inspect.aidefense.security.cisco.com",
}

CISCO_INSPECT_CHAT_PATH = "/api/v1/inspect/chat"

DEFAULT_REGION = "us"

REQUEST_TIMEOUT_SECONDS = 30.0


def _get_api_key(config: Optional[Dict[str, Any]]) -> str:
    """Resolve the Cisco AI Defense API key.

    Preference order:
    1. `config.credentials.apiKey` (set per integration via Truefoundry).
    2. `GUARDRAILS_TOKEN` environment variable.
    """
    if config and isinstance(config.get("credentials"), dict):
        api_key = config["credentials"].get("apiKey")
        if api_key:
            return api_key

    api_key = os.getenv("GUARDRAILS_TOKEN")
    if api_key:
        return api_key

    raise HTTPException(
        status_code=400,
        detail=(
            "Cisco AI Defense API key not provided. Set the `GUARDRAILS_TOKEN` "
            "environment variable or pass it via `config.credentials.apiKey`."
        ),
    )


def _resolve_base_url(config: Optional[Dict[str, Any]]) -> str:
    """Pick the Cisco AI Defense regional host based on config."""
    region = DEFAULT_REGION
    if config:
        region = str(config.get("region") or DEFAULT_REGION).lower()
    return CISCO_REGION_HOSTS.get(region, CISCO_REGION_HOSTS[DEFAULT_REGION])


def _normalize_messages(messages: Any) -> List[Dict[str, str]]:
    """Convert OpenAI-style messages into Cisco's `MessageObject` list.

    Cisco expects each message to have a string `content`. OpenAI allows
    `content` to be a list of content parts (text, image_url, etc.), so we
    flatten text parts here and drop non-text parts.
    """
    normalized: List[Dict[str, str]] = []
    if not isinstance(messages, list):
        return normalized

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if not role:
            continue

        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            parts: List[str] = []
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text" and isinstance(part.get("text"), str):
                        parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            text = "\n".join(parts)
        else:
            continue

        if not text:
            continue

        normalized.append({"role": str(role), "content": text})

    return normalized


def _build_cisco_config(config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Build the Cisco `ConfigObject` from the guardrail request config.

    Supported keys (all optional):
    - `enabled_rules`: list of rule objects (`{rule_name, ...}`) or rule name strings.
    - `integration_profile_id`, `integration_profile_version`,
      `integration_tenant_id`, `integration_type`: integration profile selectors.

    If none are provided, the Cisco API will use the tenant's default
    configuration tied to the API key.
    """
    if not config:
        return None

    cisco_config: Dict[str, Any] = {}

    enabled_rules = config.get("enabled_rules")
    if isinstance(enabled_rules, list) and enabled_rules:
        rules_payload: List[Dict[str, Any]] = []
        for rule in enabled_rules:
            if isinstance(rule, str):
                rules_payload.append({"rule_name": rule})
            elif isinstance(rule, dict) and rule.get("rule_name"):
                rules_payload.append(rule)
        if rules_payload:
            cisco_config["enabled_rules"] = rules_payload

    for key in (
        "integration_profile_id",
        "integration_profile_version",
        "integration_tenant_id",
        "integration_type",
    ):
        value = config.get(key)
        if value:
            cisco_config[key] = value

    return cisco_config or None


def _build_metadata(
    config: Optional[Dict[str, Any]],
    context_user: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Build the Cisco `MetadataObject` from request config and context."""
    metadata: Dict[str, Any] = {}

    if isinstance(context_user, dict):
        user_id = (
            context_user.get("subjectSlug")
            or context_user.get("subjectDisplayName")
            or context_user.get("subjectId")
        )
        if user_id:
            metadata["user"] = str(user_id)

    if config and isinstance(config.get("metadata"), dict):
        for key, value in config["metadata"].items():
            if value is not None:
                metadata[key] = value

    return metadata or None


def _call_cisco_inspect_chat(
    messages: List[Dict[str, str]],
    config: Optional[Dict[str, Any]],
    context_user: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """POST to Cisco AI Defense `/api/v1/inspect/chat` and return parsed JSON."""
    if not messages:
        return {}

    api_key = _get_api_key(config)
    base_url = _resolve_base_url(config)

    payload: Dict[str, Any] = {"messages": messages}

    cisco_config = _build_cisco_config(config)
    if cisco_config:
        payload["config"] = cisco_config

    metadata = _build_metadata(config, context_user)
    if metadata:
        payload["metadata"] = metadata

    try:
        response = requests.post(
            f"{base_url}{CISCO_INSPECT_CHAT_PATH}",
            json=payload,
            headers={
                "X-Cisco-AI-Defense-API-Key": api_key,
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach Cisco AI Defense API: {exc}",
        )

    if response.status_code == 200:
        try:
            return response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Invalid JSON received from Cisco AI Defense API: {exc}",
            )

    # Attempt to surface the upstream `message` field per the Cisco `Error` schema.
    try:
        error_body = response.json()
        upstream_message = error_body.get("message") if isinstance(error_body, dict) else None
    except ValueError:
        upstream_message = response.text or None

    if response.status_code in (400, 401, 403):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Cisco AI Defense rejected the request: {upstream_message or 'unauthorized'}",
        )

    raise HTTPException(
        status_code=502,
        detail=(
            f"Cisco AI Defense API error (HTTP {response.status_code}): "
            f"{upstream_message or 'unexpected error'}"
        ),
    )


def _raise_if_unsafe(cisco_response: Dict[str, Any], stage: str) -> None:
    """Raise an HTTP 400 if Cisco flagged the conversation as unsafe.

    Cisco signals a violation in two equivalent ways:
    1. `is_safe` is explicitly `false`.
    2. `is_safe` is missing but `classifications` / `rules` are non-empty.

    Anything else (including a successful response with no findings) is
    treated as safe and we return `None` to the caller.
    """
    if not cisco_response:
        return

    is_safe = cisco_response.get("is_safe")
    classifications = cisco_response.get("classifications") or []
    rules = cisco_response.get("rules") or []

    if is_safe is True:
        return
    if is_safe is None and not classifications and not rules:
        return

    rule_names = [
        rule.get("rule_name")
        for rule in rules
        if isinstance(rule, dict) and rule.get("rule_name")
    ]
    severity = cisco_response.get("severity") or "UNKNOWN"
    explanation = cisco_response.get("explanation")
    attack_technique = cisco_response.get("attack_technique")
    event_id = cisco_response.get("event_id")

    parts = [f"Cisco AI Defense flagged the {stage} as unsafe (severity={severity})"]
    if classifications:
        parts.append(f"classifications={classifications}")
    if rule_names:
        parts.append(f"rules={rule_names}")
    if attack_technique:
        parts.append(f"attack_technique={attack_technique}")
    if explanation:
        parts.append(f"explanation={explanation}")
    if event_id:
        parts.append(f"event_id={event_id}")

    raise HTTPException(status_code=400, detail="; ".join(parts))


async def cisco_ai_defense_input_guardrail(
    request: InputGuardrailRequest,
) -> Optional[dict]:
    """Input guardrail: inspect the user's prompt with Cisco AI Defense.

    Returns `None` when the prompt is safe (or there is nothing to inspect),
    and raises `HTTPException(status_code=400)` when Cisco AI Defense reports
    a violation.
    """
    messages = _normalize_messages(request.requestBody.get("messages", []))
    if not messages:
        return None

    context_user = request.context.user if request.context else None
    cisco_response = _call_cisco_inspect_chat(
        messages=messages,
        config=request.config,
        context_user=context_user,
    )
    _raise_if_unsafe(cisco_response, stage="input")
    return None


async def cisco_ai_defense_output_guardrail(
    request: OutputGuardrailRequest,
) -> Optional[dict]:
    """Output guardrail: inspect the LLM completion with Cisco AI Defense.

    The full conversation (original input messages plus the assistant's
    response) is sent to Cisco AI Defense so the model can evaluate the
    response in context.

    Returns `None` when the completion is safe (or there is nothing to
    inspect), and raises `HTTPException(status_code=400)` when Cisco AI
    Defense reports a violation.
    """
    input_messages = _normalize_messages(request.requestBody.get("messages", []))

    assistant_messages: List[Dict[str, str]] = []
    for choice in request.responseBody.get("choices", []) or []:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, str) or not content:
            # Cisco requires non-empty string content; skip tool-call-only choices.
            continue
        role = message.get("role") or "assistant"
        assistant_messages.append({"role": str(role), "content": content})

    messages = input_messages + assistant_messages
    if not assistant_messages:
        return None

    context_user = request.context.user if request.context else None
    cisco_response = _call_cisco_inspect_chat(
        messages=messages,
        config=request.config,
        context_user=context_user,
    )
    _raise_if_unsafe(cisco_response, stage="output")
    return None
