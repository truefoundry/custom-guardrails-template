from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from fastapi import HTTPException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Presidio
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def process_input_guardrail(request_body, config):
    """
    Input guardrail endpoint for validating and optionally transforming incoming OpenAI chat completion requests.

    Args:
        request (InputRequest): Contains requestBody, config, and context.

    Returns:
        Optional[CompletionCreateParams]: Transformed requestBody if content was modified, otherwise None.

    Raises:
        HTTPException: Raised if guardrail checks fail (e.g., unauthorized user, prohibited content, or internal error).
    """
    try:
        logger.info(f"Processing input guardrail with config: {config}")

        if not config.get("transform_input", False):
            return None

        # Use Presidio to remove PII if transformation is enabled
        transformed = False
        messages = request_body.get("messages", [])
        transformed_messages = []
        for message in messages:
            logger.info(f"Message: {message}")
            if isinstance(message, dict) and message.get("content"):
                # Analyze and anonymize PII
                results = analyzer.analyze(text=message["content"], entities=[], language='en')
                anonymized_content = anonymizer.anonymize(text=message["content"], analyzer_results=results)
                if anonymized_content.text != message["content"]:
                    transformed = True
                transformed_messages.append({
                    "role": message["role"],
                    "content": anonymized_content.text
                })
        request_body["messages"] = transformed_messages
        if transformed:
            logger.info("Input guardrail passed with transformation")
            return request_body
        else:
            logger.info("Input guardrail passed without transformation")
            return None

    except HTTPException:
        # Re-raise HTTP exceptions to be handled by FastAPI
        raise
    except Exception as e:
        # Log unexpected errors and raise as HTTP exception
        logger.error(f"Unexpected error in input guardrail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Guardrail processing failed: {str(e)}") 