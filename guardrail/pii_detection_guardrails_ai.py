from typing import Optional
from fastapi import HTTPException
from guardrails import Guard
from guardrails.hub import (
    DetectPII
)

from entities import InputGuardrailRequest

# Setup the Guard with the validator
guard = Guard().use(DetectPII, on_fail="exception")

def pii_detection_guardrails_ai(request: InputGuardrailRequest) -> Optional[dict]:
    try:
        messages = request.requestBody.get("messages", [])
        for message in messages:
            if isinstance(message, dict) and message.get("content"):
                guard.validate(message["content"])
        return None
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
