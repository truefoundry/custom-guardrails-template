from fastapi import FastAPI
from guardrails.pii_redaction import process_input_guardrail
from guardrails.nsfw_filtering import nsfw_filtering


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

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return {"error": "Internal server error", "detail": str(exc)}

# Run the app using Uvicorn if this script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 