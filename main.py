import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException

from guardrail.operant import process_operant_request, process_operant_response

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Operant Guardrail Server",
    description="TrueFoundry custom guardrail that proxies to Operant AI's /ai-firewall",
    version="1.0.0",
)


@app.get("/")
async def health_check():
    return {"message": "Operant Guardrail Server is running", "version": "1.0.0"}


app.add_api_route("/operant-request", endpoint=process_operant_request, methods=["POST"])
app.add_api_route("/operant-response", endpoint=process_operant_response, methods=["POST"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if isinstance(exc, HTTPException):
        return {"error": "Internal server error", "detail": str(exc.detail)}
    return {"error": "Internal server error", "detail": str(exc)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
