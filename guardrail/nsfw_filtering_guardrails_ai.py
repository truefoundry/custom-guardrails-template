from typing import Optional
from fastapi import HTTPException
from guardrails import Guard
from guardrails.hub import (
    NSFWText
)

from entities import InputGuardrailRequest

# Setup the Guard with the validator
guard = Guard().use(NSFWText, on_fail="exception", threshold=0.8, validation_method="sentence")

def nsfw_filtering_guardrails_ai(request: InputGuardrailRequest) -> Optional[dict]:
    try:
        # Assuming requestBody is a dict with a "messages" list, as in OpenAI API
        for message in request.requestBody.get("messages", []):
            if "content" in message:
                guard.validate(message["content"])
        return None
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
