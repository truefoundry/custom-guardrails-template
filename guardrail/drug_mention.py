from typing import Optional
from fastapi import HTTPException
from guardrail import Guard
from guardrails.hub import MentionsDrugs

from entities import OutputGuardrailRequest

# Setup the Guard with the validator
guard = Guard().use(MentionsDrugs, on_fail="exception")

def drug_mention(request: OutputGuardrailRequest) -> Optional[dict]:
    try:
        for choice in request.responseBody.get("choices", []):
            if "content" in choice.get("message", {}):
                guard.validate(choice["message"]["content"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
