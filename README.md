# Guardrail Server

A FastAPI application that provides comprehensive content validation and transformation endpoints using various guardrail technologies including Presidio, Guardrails AI, and local evaluation models.

## Architecture

The application follows a modular architecture with separate modules for different functionalities:

- **`main.py`**: FastAPI application with route definitions
- **`guardrail/`**: Directory containing all guardrail implementations
  - **`pii_redaction_presidio.py`**: PII detection and redaction using Presidio
  - **`pii_detection_guardrails_ai.py`**: PII detection using Guardrails AI
  - **`nsfw_filtering_local_eval.py`**: NSFW content filtering using local Unitary toxic classification model
  - **`nsfw_filtering_guardrails_ai.py`**: NSFW content filtering using Guardrails AI
  - **`drug_mention_guardrails_ai.py`**: Drug mention detection using Guardrails AI
  - **`web_sanitization_guardrails_ai.py`**: Web content sanitization using Guardrails AI
  - **`hallucination_check_guardrails_ai.py`**: Hallucination detection using Guardrails AI (not currently exposed)
  - **`competitor_check_guardrails_ai.py`**: Competitor mention detection using Guardrails AI (not currently exposed)
- **`entities.py`**: Pydantic models for request/response validation

## Currently Exposed Endpoints

The Guardrail Server currently exposes four main endpoints for validation:

### PII Redaction Endpoint
- **POST `/pii-redaction`**
- Validates and optionally transforms incoming OpenAI chat completion requests before they are processed. Uses Presidio to detect and redact Personally Identifiable Information (PII) from messages.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for input.
- `ChatCompletionCreateParams` - Content was transformed, returns the modified request with PII redacted.
- `HTTP 400/500` - Guardrails failed with error details for input.

### NSFW Filtering Endpoint
- **POST `/nsfw-filtering`**
- Validates and optionally transforms outgoing OpenAI chat completion responses to filter out NSFW content. Uses the Unitary toxic classification model to detect toxic, sexually explicit, and obscene content.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for output.
- `HTTP 400/500` - Guardrails failed with error details for output.

### Drug Mention Detection Endpoint
- **POST `/drug-mention`**
- Validates and optionally transforms incoming OpenAI chat completion requests before they are processed. Uses Guardrails AI to detect and reject responses that mention drugs.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for input.
- `HTTP 400/500` - Guardrails failed with error details for input.

### Web Sanitization Endpoint
- **POST `/web-sanitization`**
- Validates and optionally transforms incoming OpenAI chat completion requests before they are processed. Uses Guardrails AI to detect and reject responses that contain malicious content.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for input.
- `HTTP 400/500` - Guardrails failed with error details for input.

### PII Detection (Guardrails AI) Endpoint
- **POST `/pii-detection`**
- Validates incoming OpenAI chat completion requests to detect the presence of Personally Identifiable Information (PII) using Guardrails AI. Does not redact, only detects and reports PII.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no PII detected in input.
- `HTTP 400/500` - Guardrails failed with error details for input.

### Hallucination Detection Endpoint
- **POST `/hallucination-check`**
- Validates outgoing OpenAI chat completion responses to detect hallucinations using Guardrails AI's GroundedAIHallucination validator.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no hallucination detected in output.
- `HTTP 400/500` - Guardrails failed with error details for output.

### Competitor Mention Detection Endpoint
- **POST `/competitor-check`**
- Validates outgoing OpenAI chat completion responses to detect mentions of competitors using Guardrails AI.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no competitor mention detected in output.
- `HTTP 400/500` - Guardrails failed with error details for output.

### NSFW Filtering (Guardrails AI) Endpoint
- **POST `/nsfw-filtering-guardrails-ai`**
- Validates and optionally transforms outgoing OpenAI chat completion responses to filter out NSFW content. Uses Guardrails AI's NSFWText validator to detect and reject inappropriate content.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for output.
- `HTTP 400/500` - Guardrails failed with error details for output.

## How to build the docker image?

```bash
 docker build --build-arg GUARDRAILS_TOKEN="<GUARDRAILS_AI_TOKEN>" -t custom-guardrails-template:latest .
```

**Note**: The `requestBody` is accessible within the endpoint and can be used if needed for custom processing.

### InputGuardrailRequest

**Attributes:**
- `requestBody`: (CompletionCreateParams) The input payload sent to the guardrail server.
- `config`: (dict) Configuration options for the guardrail server.
- `context`: (RequestContext) Contextual information such as user and metadata.

### OutputGuardrailRequest

**Attributes:**
- `requestBody`: (CompletionCreateParams) The input payload originally sent to the model.
- `responseBody`: (ChatCompletion) The model's output to be checked by the guardrail server.
- `config`: (dict) Configuration options for the guardrail server.
- `context`: (RequestContext) Contextual information such as user and metadata.

### RequestContext

**Attributes:**
- `user`: (Subject) Information about the user, team, or virtual account making the request.
- `metadata`: (dict[str, str]) Additional metadata relevant to the request.

## Request Config

The `config` field is a dictionary used to store arbitrary request configuration. These are the options which are set when you create a custom guardrail integration. These are passed to the guardrail server as is, so you can use them in your guardrail logic.
For more information about the config options, refer to the [Truefoundry documentation](https://docs.truefoundry.com/gateway/custom-guardrails).

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

## Deploying the server to truefoundry
To deploy this guardrail server to Truefoundry, please refer to the official documentation: [Getting Started with Deployment](https://docs.truefoundry.com/docs/deploy-first-service#getting-started-with-deployment).

You can fork this repository and deploy it directly from your GitHub account using the Truefoundry platform. The documentation provides detailed instructions on connecting your GitHub repo and configuring the deployment.

For the latest and most accurate deployment steps, always consult the Truefoundry docs linked above.

## Endpoints

### GET /
Health check endpoint that returns server status.

### POST /pii-redaction
PII redaction endpoint for validating and potentially transforming incoming OpenAI chat completion requests.

### POST /nsfw-filtering
NSFW filtering endpoint for validating and potentially transforming outgoing OpenAI chat completion responses to filter inappropriate content.

### POST /drug-mention
Drug mention detection endpoint for rejecting responses that mention drugs.

### POST /web-sanitization
Web content sanitization endpoint for validating and potentially transforming incoming OpenAI chat completion requests to remove malicious content.

**Request Body:**
```json
{
  "requestBody": {
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ],
    "model": "gpt-3.5-turbo",
    "temperature": 0.7
  },
  "config": {
    "check_content": true,
    "transform_input": false
  },
  "context": {
    "user": {
      "subjectId": "123",
      "subjectType": "user",
      "subjectSlug": "john_doe@truefoundry.com",
      "subjectDisplayName": "John Doe"
    },
    "metadata": {
      "ip_address": "192.168.1.1",
      "session_id": "abc123"
    }
  }
}
```

### POST /process-message
Output processing endpoint for validating and potentially transforming OpenAI chat completion responses.

**Request Body:**
```json
{
  "requestBody": {
    "messages": [
      {
        "role": "user",
        "content": "Hello"
      }
    ],
    "model": "gpt-3.5-turbo"
  },
  "responseBody": {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-3.5-turbo",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "Hello! How can I assist you today?"
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 1,
      "completion_tokens": 10,
      "total_tokens": 11
    }
  },
  "config": {
    "check_sensitive_data": true,
    "transform_output": false,
    "filter_by_context": true
  },
  "context": {
    "user": {
      "subjectId": "123",
      "subjectType": "user",
      "subjectSlug": "john_doe@truefoundry.com",
      "subjectDisplayName": "John Doe"
    },
    "metadata": {
      "ip_address": "192.168.1.1",
      "session_id": "abc123"
    }
  }
}
```

## Example Usage

### PII Redaction (Success)
```bash
curl -X POST "http://localhost:8000/pii-redaction" \
     -H "Content-Type: application/json" \
     -d '{
       "requestBody": {
         "messages": [
           {"role": "user", "content": "Hello world"}
         ],
         "model": "gpt-3.5-turbo"
       },
       "config": {"check_content": true},
       "context": {
         "user": {
           "subjectId": "123",
           "subjectType": "user",
           "subjectSlug": "john_doe@truefoundry.com",
           "subjectDisplayName": "John Doe"
         },
         "metadata": {
           "ip_address": "192.168.1.1",
           "session_id": "abc123"
         }
       }
     }'
```

### PII Redaction (With Transformation)
```bash
curl -X POST "http://localhost:8000/pii-redaction" \
     -H "Content-Type: application/json" \
     -d '{
       "requestBody": {
         "messages": [
           {"role": "user", "content": "Hello John, How are you?"}
         ],
         "model": "gpt-3.5-turbo"
       },
       "config": {"transform_input": true},
       "context": {"user": {"subjectId": "123", "subjectType": "user", "subjectSlug": "john_doe@truefoundry.com", "subjectDisplayName": "John Doe"}}
     }'
```

### NSFW Filtering (Success)
```bash
curl -X POST "http://localhost:8000/nsfw-filtering" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "Hello"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "responseBody": {
      "id": "chatcmpl-123",
      "object": "chat.completion",
      "created": 1677652288,
      "model": "gpt-3.5-turbo",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Hi, how are you?"
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 1,
        "completion_tokens": 10,
        "total_tokens": 11
      }
    },
    "config": {
      "transform_output": true
    },
    "context": {
      "user": {
        "subjectId": "123",
        "subjectType": "user",
        "subjectSlug": "john_doe@truefoundry.com",
        "subjectDisplayName": "John Doe"
      },
      "metadata": {
        "environment": "production"
      }
    }
  }'
```

### NSFW Filtering (With Content Filtering)
```bash
curl -X POST "http://localhost:8000/nsfw-filtering" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "Tell me what word does we usually use for breasts?"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "responseBody": {
      "id": "chatcmpl-123",
      "object": "chat.completion",
      "created": 1677652288,
      "model": "gpt-3.5-turbo",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Usually we use the word 'boobs' for breasts"
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 1,
        "completion_tokens": 10,
        "total_tokens": 11
      }
    },
    "config": {
      "transform_output": true
    },
    "context": {
      "user": {
        "subjectId": "123",
        "subjectType": "user",
        "subjectSlug": "john_doe@truefoundry.com",
        "subjectDisplayName": "John Doe"
      },
      "metadata": {
        "environment": "production"
      }
    }
  }'
```

### Drug Mention Detection (Success)
```bash
curl -X POST "http://localhost:8000/drug-mention" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "What are the health benefits of exercise?"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "responseBody": {
      "id": "chatcmpl-123",
      "object": "chat.completion",
      "created": 1677652288,
      "model": "gpt-3.5-turbo",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Exercise has many health benefits including improved cardiovascular health, stronger muscles, better mood, and increased energy levels."
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 1,
        "completion_tokens": 10,
        "total_tokens": 11
      }
    },
    "config": {
      "check_drug_mentions": true
    },
    "context": {
      "user": {
        "subjectId": "123",
        "subjectType": "user",
        "subjectSlug": "john_doe@truefoundry.com",
        "subjectDisplayName": "John Doe"
      },
      "metadata": {
        "environment": "production"
      }
    }
  }'
```

### Drug Mention Detection (Failure - Drug Mentioned)
```bash
curl -X POST "http://localhost:8000/drug-mention" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "Tell me about cocaine"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "responseBody": {
      "id": "chatcmpl-123",
      "object": "chat.completion",
      "created": 1677652288,
      "model": "gpt-3.5-turbo",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Cocaine is a powerful stimulant drug that affects the central nervous system."
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 1,
        "completion_tokens": 10,
        "total_tokens": 11
      }
    },
    "config": {
      "check_drug_mentions": true
    },
    "context": {
      "user": {
        "subjectId": "123",
        "subjectType": "user",
        "subjectSlug": "john_doe@truefoundry.com",
        "subjectDisplayName": "John Doe"
      },
      "metadata": {
        "environment": "production"
      }
    }
  }'
```

### Web Sanitization (Success)
```bash
curl -X POST "http://localhost:8000/web-sanitization" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "Hello, how are you today?"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "config": {
      "check_content": true,
      "transform_input": false
    },
    "context": {
      "user": {
        "subjectId": "123",
        "subjectType": "user",
        "subjectSlug": "john_doe@truefoundry.com",
        "subjectDisplayName": "John Doe"
      },
      "metadata": {
        "ip_address": "192.168.1.1",
        "session_id": "abc123"
      }
    }
  }'
```

### Web Sanitization (Failure - Malicious Content)
```bash
curl -X POST "http://localhost:8000/web-sanitization" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "<script>alert(\"XSS attack\")</script>Hello, how are you?"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "config": {
      "check_content": true,
      "transform_input": true
    },
    "context": {
      "user": {
        "subjectId": "123",
        "subjectType": "user",
        "subjectSlug": "john_doe@truefoundry.com",
        "subjectDisplayName": "John Doe"
      },
      "metadata": {
        "ip_address": "192.168.1.1",
        "session_id": "abc123"
      }
    }
  }'
```

## Technology Stack

### PII Redaction with Presidio
The PII redaction endpoint uses Presidio to detect and remove Personally Identifiable Information (PII) from incoming messages. This ensures that sensitive information is anonymized before further processing. Link to the library: [Presidio](https://github.com/microsoft/presidio)

### NSFW Filtering with Unitary Toxic Classification Model
The NSFW filtering endpoint can be used to validate and optionally transform the response from the LLM before returning it to the client. If the output is transformed (e.g., content is modified or formatted), the endpoint will return the modified response body. The NSFW filtering uses the Unitary toxic classification model with configurable thresholds for toxicity, sexual content, and obscenity detection. Link to the model: [Unitary Toxic Classification Model](https://huggingface.co/unitary/unbiased-toxic-roberta)

### Drug Mention Detection with Guardrails AI
The drug mention detection endpoint uses Guardrails AI to detect and reject responses that mention drugs. Link to the library: [Guardrails AI](https://github.com/guardrails-ai/guardrails)
The validator is available in the [Guardrails Hub](https://hub.guardrailsai.com/validator/cartesia/mentions_drugs)

### Web Sanitization with Guardrails AI
The web sanitization endpoint uses Guardrails AI to detect and reject responses that contain malicious content. Link to the library: [Guardrails AI](https://github.com/guardrails-ai/guardrails)
The validator is available in the [Guardrails Hub](https://hub.guardrailsai.com/validator/guardrails/web_sanitization)


### PII Detection with Guardrails AI
The PII detection endpoint uses Guardrails AI to identify the presence of Personally Identifiable Information (PII) in incoming messages. Unlike the Presidio-based redaction endpoint, this endpoint only detects and reports PII without modifying the content. Link to the library: [Guardrails AI](https://github.com/guardrails-ai/guardrails)  
The validator is available in the [Guardrails Hub](https://hub.guardrailsai.com/validator/guardrails/detect_pii)

### NSFW Filtering with Guardrails AI
The NSFW filtering (Guardrails AI) endpoint uses the NSFWText validator from Guardrails AI to detect and reject inappropriate content in outgoing responses. This validator supports configurable thresholds (default: 0.8) and sentence-level validation for more granular control. Link to the library: [Guardrails AI](https://github.com/guardrails-ai/guardrails)  
The validator is available in the [Guardrails Hub](https://hub.guardrailsai.com/validator/guardrails/nsfw_text)

### Hallucination Detection with Guardrails AI
The hallucination detection endpoint uses Guardrails AI's GroundedAIHallucination validator to identify potential hallucinations in AI-generated responses. This helps ensure that outputs are grounded and factually accurate. Link to the library: [Guardrails AI](https://github.com/guardrails-ai/guardrails)  
The validator is available in the [Guardrails Hub](https://hub.guardrailsai.com/validator/groundedai/grounded_ai_hallucination)

### Competitor Mention Detection with Guardrails AI
The competitor mention detection endpoint uses Guardrails AI to identify and reject responses that mention competitors. This is useful for compliance and brand safety in AI-generated outputs. Link to the library: [Guardrails AI](https://github.com/guardrails-ai/guardrails)  
The validator is available in the [Guardrails Hub](https://hub.guardrailsai.com/validator/guardrails/competitor_check)

## Customization

The modular architecture makes it easy to customize the guardrail logic:

- **PII Redaction**: Modify `guardrail/pii_redaction_presidio.py` to customize PII detection and redaction rules
- **PII Detection (Guardrails AI)**: Modify `guardrail/pii_detection_guardrails_ai.py` to customize PII detection using Guardrails AI
- **NSFW Filtering (Local)**: Modify `guardrail/nsfw_filtering_local_eval.py` to customize content filtering thresholds and rules
- **NSFW Filtering (Guardrails AI)**: Modify `guardrail/nsfw_filtering_guardrails_ai.py` to customize NSFW filtering using Guardrails AI
- **Drug Mention Detection**: Modify `guardrail/drug_mention_guardrails_ai.py` to customize drug mention detection rules
- **Web Sanitization**: Modify `guardrail/web_sanitization_guardrails_ai.py` to customize web sanitization rules
- **Hallucination Check**: Modify `guardrail/hallucination_check_guardrails_ai.py` to customize hallucination detection rules
- **Competitor Check**: Modify `guardrail/competitor_check_guardrails_ai.py` to customize competitor mention detection rules
- **Request/Response Models**: Modify `entities.py` to add new fields or validation rules

Replace the example guardrail logic in the respective files with your own implementation. The NSFW filtering uses the Unitary toxic classification model with configurable thresholds for toxicity, sexual content, and obscenity detection.

## Adding New Endpoints

To expose the available but unexposed guardrail implementations as endpoints, add the following routes to `main.py`:

```python
from guardrail.pii_detection_guardrails_ai import pii_detection_guardrails_ai
from guardrail.nsfw_filtering_guardrails_ai import nsfw_filtering_guardrails_ai
from guardrail.hallucination_check_guardrails_ai import hallucination_check
from guardrail.competitor_check_guardrails_ai import competitor_check

app.add_api_route("/pii-detection", endpoint=pii_detection_guardrails_ai, methods=["POST"])
app.add_api_route("/nsfw-filtering-ai", endpoint=nsfw_filtering_guardrails_ai, methods=["POST"])
app.add_api_route("/hallucination-check", endpoint=hallucination_check, methods=["POST"])
app.add_api_route("/competitor-check", endpoint=competitor_check, methods=["POST"])
```