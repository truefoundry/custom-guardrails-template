from typing import Optional
from fastapi import HTTPException
from guardrails import Guard
from guardrails.hub import (
    CompetitorCheck
)
from entities import OutputGuardrailRequest

guard = Guard().use(CompetitorCheck, on_fail="exception",competitors=["Apple","Samsung","Xiaomi","Poco","Realme","OnePlus","Vivo","Oppo","Huawei","Lenovo","Dell","HP","Toshiba","Sony","LG","Samsung","Xiaomi","Poco","Realme","OnePlus","Vivo","Oppo","Huawei","Lenovo","Dell","HP","Toshiba","Sony","LG"])

def competitor_check(request: OutputGuardrailRequest) -> Optional[dict]:
    try:
        for choice in request.responseBody.get("choices", []):
            if "content" in choice.get("message", {}):
                guard.validate(choice["message"]["content"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
