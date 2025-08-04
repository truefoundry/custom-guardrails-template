from typing import Optional, Dict, List
import requests
from fastapi import HTTPException
from entities import InputGuardrailRequest
from pydantic import BaseModel


class LassoMessage(BaseModel):
    """Represents a message in the Lasso API request."""
    role: str
    content: str


class LassoClassifyRequest(BaseModel):
    """Request model for Lasso classification API."""
    messages: List[LassoMessage]


class LassoClassifyResponse(BaseModel):
    """Response model from Lasso classification API."""
    deputies: Dict[str, bool]
    deputies_predictions: Dict[str, float]
    violations_detected: bool


async def lasso_classification_guardrail(request: InputGuardrailRequest) -> Optional[dict]:
    """
    Lasso classification guardrail that checks for violations using the Lasso API.

    Args:
        request: InputGuardrailRequest containing messages to classify

    Returns:
        None if no violations detected

    Raises:
        HTTPException: If violations are detected or API call fails
    """
    try:
        # Extract messages from request body
        messages_data = request.requestBody.get("messages", [])

        # Convert to LassoMessage format
        lasso_messages = []
        for msg in messages_data:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                lasso_messages.append(LassoMessage(
                    role=msg["role"],
                    content=msg["content"]
                ))

        if not lasso_messages:
            # No messages to classify, return None
            return None

        # Prepare request payload
        classify_request = LassoClassifyRequest(messages=lasso_messages)

        # Get API key from config
        api_key = None
        if request.config and "credentials" in request.config:
            api_key = request.config["credentials"].get("apiKey")

        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="Lasso API key not provided in config.credentials.apiKey"
            )

        # Make request to Lasso API using requests (sync)
        try:
            response = requests.post(
                "https://server.lasso.security/gateway/v2/classify",
                json=classify_request.model_dump(),
                headers={
                    "lasso-api-key": api_key,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        except requests.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Lasso API: {str(e)}"
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Lasso API error: {response.text}"
            )

        # Parse response
        try:
            response_data = response.json()
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Invalid JSON from Lasso API: {str(e)}"
            )

        try:
            lasso_response = LassoClassifyResponse(**response_data)
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Malformed response from Lasso API: {str(e)}"
            )

        # Check for violations
        if lasso_response.violations_detected:
            # Get details about which deputies detected violations
            violation_details = []
            for deputy, is_violation in lasso_response.deputies.items():
                if is_violation:
                    prediction = lasso_response.deputies_predictions.get(deputy, 0.0)
                    violation_details.append(f"{deputy}: {prediction:.3f}")

            raise HTTPException(
                status_code=400,
                detail=f"Lasso guardrail violations detected: {', '.join(violation_details)}"
            )

        # No violations detected
        return None

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(
            status_code=500,
            detail=f"Error in Lasso classification guardrail: {str(e)}"
        )