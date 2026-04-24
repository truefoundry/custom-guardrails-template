# Operant Custom Guardrail for TrueFoundry AI Gateway

A minimal FastAPI server that integrates [Operant AI's](https://operant.ai/) `/ai-firewall` policy engine as a TrueFoundry [Custom Guardrail](https://www.truefoundry.com/docs/ai-gateway/custom-guardrails). It exposes two endpoints:

| Endpoint            | TrueFoundry Operation | Purpose                                                              |
| ------------------- | --------------------- | -------------------------------------------------------------------- |
| `POST /operant-request`  | Mutate (Input)   | Scans/redacts the user's prompt before it reaches the model.         |
| `POST /operant-response` | Mutate (Output)  | Scans/redacts the model's response before it reaches the end user.   |

Each endpoint forwards the message content to Operant's hosted gatekeeper (`https://pocgatekeeper.operant.ai/ai-firewall`) and translates Operant's verdict back into the response shape TrueFoundry expects.

## Verdict mapping

Operant returns one of three verdicts. We translate them as follows:

| Operant response                                         | What we return to TrueFoundry                                                              |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `{"verdict": "pass", "message": ""}`                   | `null` &mdash; request/response proceeds unchanged.                                        |
| `{"verdict": "pass", "mutatedBody": {...}}`            | The mutated `requestBody` (input) or the choices patched with redacted content (output). |
| `{"verdict": "pass", "mutatedResponseBody": {...}}`    | The full mutated `responseBody`, used as-is.                                              |
| `{"verdict": "fail", "message": "..."}`               | `HTTP 400` with `detail` set to Operant's policy message.                                 |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # then put your real Operant token in .env
python main.py        # serves on http://0.0.0.0:8000
```

The server reads `GUARDRAILS_TOKEN` from the environment (loaded from `.env` via `python-dotenv`) and sends it as `Authorization: Bearer <token>` on every call to Operant. It also injects the `x-upstream-gateway-type: truefoundry` header that Operant requires.

Optional environment overrides:

| Variable                  | Default                                              | Purpose                                |
| ------------------------- | ---------------------------------------------------- | -------------------------------------- |
| `OPERANT_URL`             | `https://pocgatekeeper.operant.ai/ai-firewall`        | Override the Operant endpoint.         |
| `OPERANT_TIMEOUT_SECONDS` | `10`                                                 | HTTP timeout for the Operant call.     |

## Quick test

Input scan with PII (Operant typically blocks):

```bash
curl -X POST http://localhost:8000/operant-request \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {"role": "user", "content": "My SSN is 123-45-6789 and card is 4111-1111-1111-1111"}
      ]
    },
    "context": {"user": {"subjectId": "u1", "subjectType": "user"}}
  }'
```

Output scan with PII in assistant content:

```bash
curl -X POST http://localhost:8000/operant-response \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {"messages": [{"role": "user", "content": "give me an example"}]},
    "responseBody": {
      "id": "c1", "object": "chat.completion", "created": 1, "model": "gpt-4o",
      "choices": [{
        "index": 0,
        "message": {"role": "assistant", "content": "SSN 123-45-6789 card 4111-1111-1111-1111"},
        "finish_reason": "stop"
      }]
    },
    "context": {"user": {"subjectId": "u1", "subjectType": "user"}}
  }'
```

## Wiring into TrueFoundry

In **AI Gateway -> Guardrails -> Add New Guardrails Group**, register two Custom Guardrail entries pointing at this server:

- `POST /operant-request` &mdash; Operation **Mutate**, Type **Input**
- `POST /operant-response` &mdash; Operation **Mutate**, Type **Output**

You do not need to configure Auth Data or Headers in the gateway; the server itself attaches the Operant bearer token. Leave the `Config` field empty (Operant applies its own server-side policies).

## File layout

```
main.py                  # FastAPI app + route registration
guardrail/operant.py     # The two handlers and shared httpx client
entities.py              # Pydantic models (InputGuardrailRequest, OutputGuardrailRequest, RequestContext)
requirements.txt         # fastapi, uvicorn, pydantic, httpx, python-dotenv
Dockerfile               # Container build
```

## Docker

```bash
docker build -t operant-guardrail .
docker run --rm -p 8000:8000 --env-file .env operant-guardrail
```
