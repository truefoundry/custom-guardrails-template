from fastapi import FastAPI, HTTPException, Depends, Request
from typing import Optional, Annotated
import logging

from openai.types.chat.chat_completion import ChatCompletion
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from models.input_guardrail_response import InputGuardrailResponse
from models.input_request import InputRequest
from models.output_request import OutputRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Presidio engines for PII detection and anonymization
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Create FastAPI app instance
app = FastAPI(
    title="Guardrail Server",
    description="A FastAPI application for input and output guardrails",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Health check endpoint to verify server status"""
    return {"message": "Guardrail Server is running", "version": "1.0.0"}


@app.post("/input", response_model=Optional[InputGuardrailResponse])
async def input_guardrail(request: InputRequest):
    """
    Input guardrail endpoint to process incoming requests.
    
    Args:
        request: InputRequest object containing requestBody, config, and context.
        headers: Dictionary of HTTP headers from the request.
        
    Returns:
        - None: If guardrails pass without transformation.
        - ChatCompletionCreateParams: If content was transformed.
        
    Raises:
        HTTPException: If guardrails fail.
    """
    try:
        logger.info(f"Processing input guardrail with config: {request.config}")
        
        # Extract request components
        request_body = request.requestBody
        config = request.config
        context = request.context
        
        # Check for prohibited content if enabled in config
        if config.get("check_content", False):
            for message in request_body.get("messages", []):
                if isinstance(message, dict) and message.get("content"):
                    if "prohibited" in message["content"].lower():
                        raise HTTPException(status_code=400, detail="Content violates guardrail policy")
        
        # Use Presidio to remove PII if transformation is enabled
        if config.get("transform_input", False):
            transformed_body = request_body.model_copy(deep=True)
            for message in transformed_body.get("messages", []):
                if isinstance(message, dict) and message.get("content"):
                    # Analyze and anonymize PII
                    results = analyzer.analyze(text=message["content"], entities=[], language='en')
                    anonymized_content = anonymizer.anonymize(text=message["content"], analyzer_results=results)
                    message["content"] = anonymized_content.text
            return transformed_body
        
        # Log success if no transformation is needed
        logger.info("Input guardrail passed without transformation")
        return None
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors and raise as HTTP exception
        logger.error(f"Unexpected error in input guardrail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Guardrail processing failed: {str(e)}")
    

@app.post("/output", response_model=Optional[ChatCompletion])
async def output_guardrail(
    request: OutputRequest,
    raw_request: Request  # Inject FastAPI's Request object to access headers
):
    """
    Output guardrail endpoint to process outgoing responses.
    
    Args:
        request: OutputRequest object containing requestBody, responseBody, config, and context.
        raw_request: The raw HTTP request object to access headers.
        
    Returns:
        - None: If guardrails pass without transformation.
        - ChatCompletion: If content was transformed.
        
    Raises:
        HTTPException: If guardrails fail.
    """
    try:
        logger.info(f"Processing output guardrail with config: {request.config}")
        
        # Extract request components
        # request_body = request.requestBody User can use this if they want to access the request body
        response_body = request.responseBody
        config = request.config
        context = request.context
        headers = dict(raw_request.headers)  # Extract all headers as lowercase keys
        
        # Check for required headers if specified in config
        if config.get("require_header"):
            required_header = config["require_header"].lower()
            if required_header not in headers:
                logger.warning(f"Missing required header: {required_header}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required header: {required_header}"
                )
            
            expected_value = config.get("require_header_value")
            if expected_value is not None:
                actual_value = headers.get(required_header)
                if actual_value != expected_value:
                    logger.warning(
                        f"Header {required_header} value mismatch: expected '{expected_value}', got '{actual_value}'"
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid value for header {required_header}"
                    )
        
        # Check for sensitive information in response choices
        if config.get("check_sensitive_data", False):
            for choice in response_body.choices:
                if choice.message.content and "sensitive" in choice.message.content.lower():
                    raise HTTPException(status_code=400, detail="Response contains sensitive data")
        
        # Transform response content if transformation is enabled
        if config.get("transform_output", False):
            transformed_body = response_body.model_copy(deep=True)
            for choice in transformed_body.choices:
                if choice.message.content:
                    # Add a prefix to indicate the response was processed
                    choice.message.content = f"[Processed] {choice.message.content}"
            return transformed_body
        
        # Filter content based on user context if enabled
        if config.get("filter_by_context", False):
            user_role = context.get("user_role", "")
            if user_role == "restricted":
                transformed_body = response_body.model_copy(deep=True)
                for choice in transformed_body.choices:
                    if choice.message.content and "admin" in choice.message.content.lower():
                        choice.message.content = "[Content filtered based on user permissions]"
                return transformed_body
        
        # Log success if no transformation is needed
        logger.info("Output guardrail passed without transformation")
        return None
        
    except Exception as e:
        # Log unexpected errors and raise as HTTP exception
        logger.error(f"Unhandled exception in output_guardrail: {str(e)}")
        raise


# Global error handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {str(exc)}")
    return {"error": "Internal server error", "detail": str(exc)}

# Run the app using Uvicorn if this script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 