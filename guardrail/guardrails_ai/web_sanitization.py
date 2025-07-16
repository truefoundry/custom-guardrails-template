from typing import Optional
from fastapi import HTTPException
from guardrails import Guard
from guardrails_grhub_web_sanitization import WebSanitization

from entities import InputGuardrailRequest

# Setup the Guard with the validator
guard = Guard().use(WebSanitization, on_fail="exception")

def web_sanitization(request: InputGuardrailRequest) -> Optional[dict]:
    try:
        messages = request.requestBody.get("messages", [])
        for message in messages:
            if isinstance(message, dict) and message.get("content"):
                guard.validate(message["content"])
        return None
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
