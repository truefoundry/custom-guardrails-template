# lasso-guardrails-tfy

[Lasso Security](https://server.lasso.security) as a TrueFoundry AI Gateway custom guardrail. Forwards gateway traffic to Lasso API v3 (`classify` for validate, `classifix` for mutate).

## Endpoints

| Route | Operation | Use in TrueFoundry |
|---|---|---|
| `POST /lasso-classify` | validate | Input guardrail |
| `POST /lasso-classify-output` | validate | Output guardrail |
| `POST /lasso-classifix` | mutate | Input PII masking |
| `POST /lasso-classifix-output` | mutate | Output PII masking |

Health: `GET /` or `GET /health`  
Debug: `GET /debug/runtime-config` (requires bearer auth)

All POSTs require `Authorization: Bearer $WRAPPER_API_KEY` when set.

## Response contract

| Status | Body | Meaning |
|---|---|---|
| `200` | `{"verdict": true}` | Pass |
| `200` | `{"verdict": false, "message": "..."}` | Block |
| `200` | `{"verdict": true, "transformed": true/false, "result": {...}}` | Mutate |
| `5xx` | error JSON | Real error |

Set **Fail on error: false** on each Custom Guardrail Config in TrueFoundry.

## Local run

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
cp .env.example .env                            # set LASSO_API_KEY, WRAPPER_API_KEY
.venv\Scripts\uvicorn main:app --reload --port 8000
```

## Docker

```bash
docker build -t lasso-guardrails-tfy .
docker run --rm -p 8000:8000 --env-file .env lasso-guardrails-tfy
```

## Deploy to TrueFoundry

1. Create secret group `lasso-guardrails-tfy` with `lasso-api-key` and `wrapper-api-key`
2. Fill deploy fields in `.env`, then:

```bash
pip install -U truefoundry
tfy login
python deploy.py --wait
```

3. Register four Custom Guardrail Configs in **AI Gateway → Guardrails**:

| Name | Operation | URL |
|---|---|---|
| `lasso-classify-input` | Validate | `https://<host>/<path>/lasso-classify` |
| `lasso-classify-output` | Validate | `…/lasso-classify-output` |
| `lasso-classifix-input` | Mutate | `…/lasso-classifix` |
| `lasso-classifix-output` | Mutate | `…/lasso-classifix-output` |

Auth: **Custom Bearer Auth** with your `wrapper-api-key` value.  
Config: `{}` (Lasso key comes from deploy secret, or pass via `config.credentials.apiKey`).

## References

- [TrueFoundry custom guardrails](https://docs.truefoundry.com/gateway/custom-guardrails)
- [Lasso Security](https://server.lasso.security)
