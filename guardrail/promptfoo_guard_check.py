from fastapi import HTTPException
from .promptfoo_utils import (
    make_promptfoo_request,
    GuardCheckRequest,
    GuardCheckResponse
)

def guard_check_endpoint(request: GuardCheckRequest) -> GuardCheckResponse:
    """Endpoint handler for guard check"""
    result = make_promptfoo_request("guard", {"input": request.input})
    
    if not result.get("results") or len(result["results"]) == 0:
        raise HTTPException(status_code=500, detail="No results returned from guard check")
        
    guard_result = result["results"][0]
    
    return GuardCheckResponse(
        flagged=guard_result.get("flagged", False),
        categories=guard_result.get("categories", {}),
        category_scores=guard_result.get("category_scores", {}),
        model=result.get("model", "unknown")
    ) 