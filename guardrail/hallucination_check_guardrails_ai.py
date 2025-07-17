from typing import Optional
from fastapi import HTTPException
from guardrails import Guard
from guardrails.hub import (
    GroundedAIHallucination
)
from entities import OutputGuardrailRequest

guard = Guard().use(GroundedAIHallucination, on_fail="exception",quant=False)

def hallucination_check(request: OutputGuardrailRequest) -> Optional[dict]:
    try:
        for choice in request.responseBody.get("choices", []):
            if "content" in choice.get("message", {}):
                guard.validate(choice["message"]["content"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
