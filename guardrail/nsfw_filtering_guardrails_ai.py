from typing import Optional
from fastapi import HTTPException
from guardrails import Guard
from guardrails.hub import (
    NSFWText
)

from entities import OutputGuardrailRequest

# Setup the Guard with the validator
guard = Guard().use(NSFWText, on_fail="exception",threshold=0.8,validation_method="sentence")

def nsfw_filtering_guardrails_ai(request: OutputGuardrailRequest) -> Optional[dict]:
    try:
        for choice in request.responseBody.get("choices", []):
            if "content" in choice.get("message", {}):
                guard.validate(choice["message"]["content"])
        return None
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
