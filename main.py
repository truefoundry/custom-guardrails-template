from fastapi import FastAPI, HTTPException, Request
from typing import Optional
import logging

from openai.types.chat.chat_completion import ChatCompletion
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from openai.types.chat.completion_create_params import CompletionCreateParams
from openai.types.chat.chat_completion import ChatCompletion

from entities import InputGuardrailRequest, OutputGuardrailRequest

# Configure logging for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_presidio():
    """
    Initialize Presidio Analyzer and Anonymizer engines.
    Returns:
        tuple: (AnalyzerEngine, AnonymizerEngine)
    """
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    return analyzer, anonymizer

# Create FastAPI app instance
app = FastAPI(
    title="Guardrail Server",
    description="A FastAPI application for input and output guardrails",
    version="1.0.0"
)

@app.get("/")
async def root():
    """
    Health check endpoint to verify server status.
    Returns:
        dict: Server status and version.
    """
    return {"message": "Guardrail Server is running", "version": "1.0.0"}


@app.post("/input", response_model=Optional[dict])
async def input_guardrail(request: InputGuardrailRequest):
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
        logger.info(f"Processing input guardrail with config: {request.config}")

        # Extract request components
        request_body = request.requestBody
        config = request.config

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


@app.post("/output", response_model=Optional[dict])
async def output_guardrail(
    request: OutputGuardrailRequest,
):
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
        logger.info(f"Processing output guardrail with config: {request.config}")

        # Extract request components
        response_body = request.responseBody
        config = request.config

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


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global error handler for unhandled exceptions.

    Args:
        request: The incoming request.
        exc: The exception instance.

    Returns:
        dict: Error message and details.
    """
    logger.error(f"Global exception handler caught: {str(exc)}")
    return {"error": "Internal server error", "detail": str(exc)}

# Run the app using Uvicorn if this script is executed directly
if __name__ == "__main__":
    import uvicorn
    analyzer, anonymizer = initialize_presidio()
    uvicorn.run(app, host="0.0.0.0", port=8000) 