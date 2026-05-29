"""FastAPI app for the Lasso Security custom guardrail wrapper.

Endpoints (per-rail; one route per guardrail handler):

    GET  /                       health check (open)
    GET  /health                 health check (open)
    POST /lasso-classify         Lasso classify — input validate
    POST /lasso-classify-output  Lasso classify — output validate
    POST /lasso-classifix        Lasso classifix — input mutate
    POST /lasso-classifix-output Lasso classifix — output mutate
    GET  /debug/runtime-config   diagnostics (bearer-auth gated)

A shared bearer token gates the rail endpoints and /debug. Configure the same
token in the TrueFoundry dashboard under Custom Bearer Auth.

Response contract: per the TFY AI Gateway custom-guardrail contract (with
commit a1c551be on tfy-llm-gateway), validate handlers return HTTP 200 with
ValidateGuardrailResponse JSON. Allow is `{verdict: true}`; block is
`{verdict: false, message: ...}`. Mutate handlers return MutateGuardrailResponse.
Non-2xx is reserved for real errors.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from guardrail.lasso import (
    DEFAULT_API_BASE,
    DEFAULT_TIMEOUT,
    lasso_classify_input,
    lasso_classify_output,
    lasso_classifix_input,
    lasso_classifix_output,
)

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("lasso-guardrails-tfy")

WRAPPER_API_KEY = os.environ.get("WRAPPER_API_KEY", "").strip()


def require_bearer(request: Request) -> None:
    """Bearer-auth dependency. No key configured -> auth disabled (local dev only)."""
    if not WRAPPER_API_KEY:
        return
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    if header.split(" ", 1)[1].strip() != WRAPPER_API_KEY:
        raise HTTPException(status_code=401, detail="invalid bearer token")


app = FastAPI(
    title="lasso-guardrails-tfy",
    description="Lasso Security classify/classifix rails behind the TrueFoundry custom-guardrail contract.",
    version="1.0.0",
)


@app.get("/")
@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug/runtime-config", dependencies=[Depends(require_bearer)])
async def debug_runtime_config() -> dict:
    """Return non-secret runtime configuration for post-deploy verification."""
    return {
        "wrapper_version": os.environ.get("BUILD_REF", "unknown"),
        "lasso_api_base_env": os.environ.get("LASSO_API_BASE", DEFAULT_API_BASE),
        "default_timeout": DEFAULT_TIMEOUT,
        "lasso_api_key_configured": bool(os.environ.get("LASSO_API_KEY", "").strip()),
        "wrapper_auth_enabled": bool(WRAPPER_API_KEY),
        "routes": {
            "input_validate": "/lasso-classify",
            "output_validate": "/lasso-classify-output",
            "input_mutate": "/lasso-classifix",
            "output_mutate": "/lasso-classifix-output",
        },
    }


# Validate — HTTP 200 + verdict true/false (TrueFoundry policy contract)
app.add_api_route(
    "/lasso-classify",
    endpoint=lasso_classify_input,
    methods=["POST"],
    status_code=200,
    dependencies=[Depends(require_bearer)],
)
app.add_api_route(
    "/lasso-classify-output",
    endpoint=lasso_classify_output,
    methods=["POST"],
    status_code=200,
    dependencies=[Depends(require_bearer)],
)

# Mutate (PII masking via classifix; span masks from findings; safety BLOCK still denies)
app.add_api_route(
    "/lasso-classifix",
    endpoint=lasso_classifix_input,
    methods=["POST"],
    status_code=200,
    dependencies=[Depends(require_bearer)],
)
app.add_api_route(
    "/lasso-classifix-output",
    endpoint=lasso_classifix_output,
    methods=["POST"],
    status_code=200,
    dependencies=[Depends(require_bearer)],
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

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
