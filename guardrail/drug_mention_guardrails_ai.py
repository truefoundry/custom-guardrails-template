from guardrails import Guard
from guardrails.hub import MentionsDrugs

from entities import OutputGuardrailRequest, ValidateGuardrailResponse

# Setup the Guard with the validator
guard = Guard().use(MentionsDrugs, on_fail="exception")


def drug_mention(request: OutputGuardrailRequest) -> ValidateGuardrailResponse:
    try:
        for choice in request.responseBody.get("choices", []):
            if "content" in choice.get("message", {}):
                guard.validate(choice["message"]["content"])
    except Exception as e:
        return ValidateGuardrailResponse(verdict=False, message=str(e))
    return ValidateGuardrailResponse(verdict=True)
