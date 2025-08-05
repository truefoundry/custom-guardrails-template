from fastapi import HTTPException
from .promptfoo_utils import (
    make_promptfoo_request,
    HarmDetectionRequest,
    HarmDetectionResponse
)

def harm_detection_endpoint(request: HarmDetectionRequest) -> HarmDetectionResponse:
    """Endpoint handler for harm detection"""
    result = make_promptfoo_request("harm", {"input": request.input})
    
    if not result.get("results") or len(result["results"]) == 0:
        raise HTTPException(status_code=500, detail="No results returned from harm detection")
        
    harm_result = result["results"][0]
    
    return HarmDetectionResponse(
        flagged=harm_result.get("flagged", False),
        categories=harm_result.get("categories", {}),
        category_scores=harm_result.get("category_scores", {}),
        model=result.get("model", "unknown")
    ) 