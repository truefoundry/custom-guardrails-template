from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional, Union
import logging

# Import OpenAI types
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.completion_create_params import CompletionCreateParams

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Guardrail Server",
    description="A FastAPI application for input and output guardrails",
    version="1.0.0"
)

# Pydantic models for guardrail requests
class InputRequest(BaseModel):
    requestBody: CompletionCreateParams
    config: Dict[str, Any]
    context: Dict[str, Any]

class OutputRequest(BaseModel):
    requestBody: CompletionCreateParams
    responseBody: ChatCompletion
    config: Dict[str, Any]
    context: Dict[str, Any]

class GuardrailResponse(BaseModel):
    result: Optional[Any] = None
    transformed: bool = False
    message: str = "Success"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Guardrail Server is running", "version": "1.0.0"}

@app.post("/input", response_model=Optional[Any])
async def input_guardrail(request: InputRequest):
    """
    Input guardrail endpoint
    
    Args:
        request: Contains requestBody (ChatCompletionCreateParams), config, and context
        
    Returns:
        - None: If guardrails pass without transformation
        - ChatCompletionCreateParams: If content was transformed
        
    Raises:
        HTTPException: If guardrails fail
    """
    try:
        logger.info(f"Processing input guardrail with config: {request.config}")
        
        # Example guardrail logic - replace with your actual implementation
        request_body = request.requestBody
        config = request.config
        context = request.context
        
        # Example: Check if messages contain prohibited content
        if config.get("check_content", False):
            for message in request_body.get("messages", []):
                if isinstance(message, dict) and message.get("content"):
                    if "prohibited" in message["content"].lower():
                        raise HTTPException(status_code=400, detail="Content violates guardrail policy")
        
        # Example: Transform content if transformation is enabled
        if config.get("transform_input", False):
            # Example transformation: add a system message with timestamp
            transformed_body = dict(request_body)
            messages = list(transformed_body.get("messages", []))
            
            # Add a system message with processing timestamp
            system_message = {
                "role": "system",
                "content": f"Request processed at 2024-01-01T00:00:00Z"
            }
            messages.insert(0, system_message)
            transformed_body["messages"] = messages
            
            logger.info("Input content transformed")
            return transformed_body
        
        # If no transformation needed, return None (success)
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
async def output_guardrail(request: OutputRequest):
    """
    Output guardrail endpoint
    
    Args:
        request: Contains requestBody (ChatCompletionCreateParams), responseBody (ChatCompletion), config, and context
        
    Returns:
        - None: If guardrails pass without transformation
        - ChatCompletion: If content was transformed
        
    Raises:
        HTTPException: If guardrails fail
    """
    try:
        logger.info(f"Processing output guardrail with config: {request.config}")
        
        # Example guardrail logic - replace with your actual implementation
        request_body = request.requestBody
        response_body = request.responseBody
        config = request.config
        context = request.context
        
        # Example: Check if response choices contain sensitive information
        if config.get("check_sensitive_data", False):
            for choice in response_body.choices:
                if choice.message.content and "sensitive" in choice.message.content.lower():
                    raise HTTPException(status_code=400, detail="Response contains sensitive data")
        
        # Example: Transform response if transformation is enabled
        if config.get("transform_output", False):
            # Example transformation: modify response content
            transformed_body = response_body.model_copy(deep=True)
            
            for choice in transformed_body.choices:
                if choice.message.content:
                    # Add a prefix to indicate the response was processed
                    choice.message.content = f"[Processed] {choice.message.content}"
            
            logger.info("Output content transformed")
            return transformed_body
        
        # Example: Content filtering based on request context
        if config.get("filter_by_context", False):
            user_role = context.get("user_role", "")
            if user_role == "restricted":
                # Filter out admin-only content for restricted users
                transformed_body = response_body.model_copy(deep=True)
                
                for choice in transformed_body.choices:
                    if choice.message.content and "admin" in choice.message.content.lower():
                        choice.message.content = "[Content filtered based on user permissions]"
                
                logger.info("Output content filtered based on user context")
                return transformed_body
        
        # If no transformation needed, return None (success)
        logger.info("Output guardrail passed without transformation")
        return None
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors and raise as HTTP exception
        logger.error(f"Unexpected error in output guardrail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Guardrail processing failed: {str(e)}")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {str(exc)}")
    return {"error": "Internal server error", "detail": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 