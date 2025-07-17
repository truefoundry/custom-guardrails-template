from fastapi import FastAPI, HTTPException
from guardrail.pii_detection_guardrails_ai import pii_detection_guardrails_ai
from guardrail.pii_redaction_presidio import process_input_guardrail
from guardrail.nsfw_filtering_local_eval import nsfw_filtering
from guardrail.drug_mention_guardrails_ai import drug_mention
from guardrail.web_sanitization_guardrails_ai import web_sanitization

# Create FastAPI app instance
app = FastAPI(
    title="Guardrail Server",
    description="A FastAPI application for input and output guardrails",
    version="1.0.0"
)

@app.get("/")
async def health_check():
    return {"message": "Guardrail Server is running", "version": "1.0.0"}



app.add_api_route( "/pii-redaction", endpoint=process_input_guardrail, methods=["POST"])

app.add_api_route("/nsfw-filtering",endpoint=nsfw_filtering,methods=["POST"])

app.add_api_route("/drug-mention",endpoint=drug_mention,methods=["POST"])

app.add_api_route("/web-sanitization",endpoint=web_sanitization,methods=["POST"])

app.add_api_route("/pii-detection",endpoint=pii_detection_guardrails_ai,methods=["POST"])





@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if isinstance(exc, HTTPException):
        return {"error": "Internal server error", "detail": str(exc.detail)}
    else:
        return {"error": "Internal server error", "detail": str(exc)}

# Run the app using Uvicorn if this script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 