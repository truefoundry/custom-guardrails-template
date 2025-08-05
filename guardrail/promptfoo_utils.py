import requests
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from fastapi import HTTPException

# Request Models
class GuardCheckRequest(BaseModel):
    input: str = Field(..., description="Text input to check for injection and jailbreak attempts")

class PIIDetectionRequest(BaseModel):
    input: str = Field(..., description="Text input to check for PII")
    redact: bool = Field(default=False, description="Whether to redact detected PII")

class HarmDetectionRequest(BaseModel):
    input: str = Field(..., description="Text input to check for harmful content")

# Response Models
class GuardCheckResponse(BaseModel):
    flagged: bool = Field(..., description="Whether the input was flagged")
    categories: Dict[str, bool] = Field(..., description="Detection categories")
    category_scores: Dict[str, float] = Field(..., description="Confidence scores for each category")
    model: str = Field(..., description="Model used for detection")

class PIIEntity(BaseModel):
    entity_type: str = Field(..., description="Type of PII detected")
    start: int = Field(..., description="Start position of PII in text")
    end: int = Field(..., description="End position of PII in text")
    pii: str = Field(..., description="The detected PII text")

class PIIDetectionResponse(BaseModel):
    flagged: bool = Field(..., description="Whether PII was detected")
    categories: Dict[str, bool] = Field(..., description="Detection categories")
    category_scores: Dict[str, float] = Field(..., description="Confidence scores for each category")
    pii_entities: List[PIIEntity] = Field(..., description="List of detected PII entities")
    redacted_text: Optional[str] = Field(None, description="Text with PII redacted (if redact=True)")
    model: str = Field(..., description="Model used for detection")

class HarmDetectionResponse(BaseModel):
    flagged: bool = Field(..., description="Whether harmful content was detected")
    categories: Dict[str, bool] = Field(..., description="Detection categories")
    category_scores: Dict[str, float] = Field(..., description="Confidence scores for each category")
    model: str = Field(..., description="Model used for detection")

def make_promptfoo_request(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to the Promptfoo API"""
    try:
        response = requests.post(
            f"https://api.promptfoo.dev/v1/{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Promptfoo API error: {response.text}"
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Request to Promptfoo API failed: {str(e)}"
        ) 