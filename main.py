from fastapi import FastAPI, HTTPException

from guardrail.drug_mention_guardrails_ai import drug_mention
from guardrail.nsfw_filtering_local_eval import nsfw_filtering

# from guardrail.pii_detection_guardrails_ai import pii_detection_guardrails_ai
# from guardrail.competitor_check_guardrails_ai import competitor_check
# from guardrail.hallucination_check_guardrails_ai import hallucination_check
from guardrail.pii_redaction_presidio import process_input_guardrail
from guardrail.web_sanitization_guardrails_ai import web_sanitization

# from guardrail.nsfw_filtering_guardrails_ai import nsfw_filtering_guardrails_ai

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

# app.add_api_route("/pii-detection",endpoint=pii_detection_guardrails_ai,methods=["POST"])

# app.add_api_route("/nsfw-filtering-guardrails-ai",endpoint=nsfw_filtering_guardrails_ai,methods=["POST"])

# app.add_api_route("/hallucination-check",endpoint=hallucination_check,methods=["POST"])

# app.add_api_route("/competitor-check",endpoint=competitor_check,methods=["POST"])


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
