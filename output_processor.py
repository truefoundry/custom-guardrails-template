from fastapi import HTTPException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_output_guardrail(response_body, config):
    """
    Output guardrail endpoint for validating and optionally transforming outgoing OpenAI chat completion responses.

    Args:
        request (OutputRequest): Contains requestBody, responseBody, config, and context.
        raw_request (Request): The raw HTTP request object to access headers.

    Returns:
        Optional[dict]: Transformed responseBody if content was modified, otherwise None.

    Raises:
        HTTPException: If guardrails fail (e.g., missing/invalid headers or internal error).
    """
    try:
        logger.info(f"Processing output guardrail with config: {config}")

        if not config.get("transform_output", False):
            return None

        # Transform response content if transformation is enabled
        transformed_body = response_body.copy()  # Use dict copy method
        for choice in transformed_body.get("choices", []):
            if "content" in choice.get("message", {}):
                # Add a prefix to indicate the response was processed
                choice["message"]["content"] = f"[Processed] {choice['message']['content']}"
        
        logger.info("Output guardrail passed with transformation")
        return transformed_body

    except HTTPException:
        # Re-raise HTTP exceptions to be handled by FastAPI
        raise
    except Exception as e:
        # Log unexpected errors and raise as HTTP exception
        logger.error(f"Unhandled exception in output_guardrail: {str(e)}")
        raise 