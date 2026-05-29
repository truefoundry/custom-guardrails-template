import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from guardrail.lasso import (
    lasso_classify_input,
    lasso_classify_output,
    lasso_classifix_input,
    lasso_classifix_output,
)

logging.basicConfig(level=logging.INFO)


def _load_dotenv() -> None:
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

app = FastAPI(
    title="Lasso Security Guardrail Server",
    description="TrueFoundry AI Gateway custom guardrails backed by Lasso Security API v3",
    version="1.0.0",
)


@app.get("/")
async def health_check():
    return {
        "message": "Lasso Security Guardrail Server is running",
        "version": "1.0.0",
        "lasso_api_version": "v3",
    }


# Validate — HTTP 200 + verdict true/false (TrueFoundry policy contract)
app.add_api_route(
    "/lasso-classify", endpoint=lasso_classify_input, methods=["POST"], status_code=200
)
app.add_api_route(
    "/lasso-classify-output",
    endpoint=lasso_classify_output,
    methods=["POST"],
    status_code=200,
)

# Mutate (PII masking via classifix; span masks from findings; safety BLOCK still denies)
app.add_api_route(
    "/lasso-classifix", endpoint=lasso_classifix_input, methods=["POST"], status_code=200
)
app.add_api_route(
    "/lasso-classifix-output",
    endpoint=lasso_classifix_output,
    methods=["POST"],
    status_code=200,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Guardrail server error", "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "Guardrail server error", "detail": exc.detail},
        )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
