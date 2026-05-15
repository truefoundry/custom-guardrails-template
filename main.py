from fastapi import FastAPI, HTTPException

from guardrail.cisco_ai_defense_guardrail import (
    cisco_ai_defense_input_guardrail,
    cisco_ai_defense_output_guardrail,
)

app = FastAPI(
    title="Cisco AI Defense Guardrail Server",
    description="Input/output guardrails backed by the Cisco AI Defense Chat Inspection API",
    version="1.0.0",
)


@app.get("/")
async def health_check():
    return {"message": "Cisco AI Defense Guardrail Server is running", "version": "1.0.0"}


app.add_api_route(
    "/cisco-ai-defense/input",
    endpoint=cisco_ai_defense_input_guardrail,
    methods=["POST"],
)

app.add_api_route(
    "/cisco-ai-defense/output",
    endpoint=cisco_ai_defense_output_guardrail,
    methods=["POST"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if isinstance(exc, HTTPException):
        return {"error": "Internal server error", "detail": str(exc.detail)}
    return {"error": "Internal server error", "detail": str(exc)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
