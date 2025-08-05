from typing import List
from fastapi import HTTPException
from .promptfoo_utils import (
    make_promptfoo_request,
    PIIDetectionRequest,
    PIIDetectionResponse,
    PIIEntity
)

def _redact_pii(text: str, pii_entities: List[PIIEntity]) -> str:
    """Redact PII entities from text by replacing them with [ENTITY_TYPE] markers"""
    sorted_entities = sorted(pii_entities, key=lambda x: x.start, reverse=True)
    redacted_text = text
    for entity in sorted_entities:
        mask_text = f"[{entity.entity_type.upper()}]"
        redacted_text = (
            redacted_text[:entity.start] + 
            mask_text + 
            redacted_text[entity.end:]
        )
    return redacted_text

def pii_detection_endpoint(request: PIIDetectionRequest) -> PIIDetectionResponse:
    """Endpoint handler for PII detection"""
    result = make_promptfoo_request("pii", {"input": request.input})
    
    if not result.get("results") or len(result["results"]) == 0:
        raise HTTPException(status_code=500, detail="No results returned from PII detection")
        
    pii_result = result["results"][0]
    
    # Extract PII entities
    pii_entities = []
    if pii_result.get("payload", {}).get("pii"):
        for entity in pii_result["payload"]["pii"]:
            pii_entities.append(PIIEntity(
                entity_type=entity.get("entity_type", ""),
                start=entity.get("start", 0),
                end=entity.get("end", 0),
                pii=entity.get("pii", "")
            ))
    
    # Handle redaction if requested
    redacted_text = None
    if request.redact and pii_result.get("flagged", False) and pii_entities:
        redacted_text = _redact_pii(request.input, pii_entities)
    
    return PIIDetectionResponse(
        flagged=pii_result.get("flagged", False),
        categories=pii_result.get("categories", {}),
        category_scores=pii_result.get("category_scores", {}),
        pii_entities=pii_entities,
        redacted_text=redacted_text,
        model=result.get("model", "unknown")
    ) 