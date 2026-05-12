from guardrails import Guard
from guardrails.hub import DetectPII

from entities import InputGuardrailRequest, ValidateGuardrailResponse

# Setup the Guard with the validator
guard = Guard().use(DetectPII, on_fail="exception")


def pii_detection_guardrails_ai(request: InputGuardrailRequest) -> ValidateGuardrailResponse:
    try:
        messages = request.requestBody.get("messages", [])
        for message in messages:
            if isinstance(message, dict) and message.get("content"):
                guard.validate(message["content"])
    except Exception as e:
        return ValidateGuardrailResponse(verdict=False, message=str(e))
    return ValidateGuardrailResponse(verdict=True)
