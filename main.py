from fastapi import FastAPI, HTTPException
from typing import Optional
import logging

from entities import InputGuardrailRequest, OutputGuardrailRequest
from pii_redaction import process_input_guardrail
from output_processor import process_output_guardrail

# Configure logging for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


@app.post("/pii-redaction", response_model=Optional[dict])
async def input_guardrail(request: InputGuardrailRequest):
    return process_input_guardrail(request.requestBody, request.config)


@app.post("/process-output", response_model=Optional[dict])
async def output_guardrail(
    request: OutputGuardrailRequest,
):
    return process_output_guardrail(request.responseBody, request.config)


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
    uvicorn.run(app, host="0.0.0.0", port=8000) 