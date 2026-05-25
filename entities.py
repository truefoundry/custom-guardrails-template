from typing import Any, Optional

from pydantic import BaseModel


class ValidateGuardrailResponse(BaseModel):
    """Response body for validate-operation guardrails (TrueFoundry AI Gateway contract)."""

    verdict: bool
    message: Optional[str] = None


class MutateGuardrailResponse(BaseModel):
    """Response body for mutate-operation guardrails (TrueFoundry AI Gateway contract)."""

    verdict: bool
    transformed: bool
    result: dict[str, Any]


class RequestContext(BaseModel):
    """
    Context added by the TrueFoundry AI Gateway (user and request metadata).
    """

    user: dict
    metadata: Optional[dict[str, str]] = None


class OutputGuardrailRequest(BaseModel):
    requestBody: dict[str, Any]
    responseBody: dict[str, Any]
    config: Optional[dict[str, Any]] = None
    context: RequestContext


class InputGuardrailRequest(BaseModel):
    requestBody: dict[str, Any]
    context: RequestContext
    config: Optional[dict[str, Any]] = None
