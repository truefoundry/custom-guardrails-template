# Guardrail Server

A FastAPI application that provides PII redaction and message processing endpoints for content validation and transformation.

## Architecture

The application follows a modular architecture with separate modules for different functionalities:

- **`main.py`**: FastAPI application with route definitions
- **`guardrails/pii_redaction.py`**: PII detection and redaction logic using Presidio (this is a sample implementation for reference, you can replace it with your own logic)
- **`guardrails/nsfw_filtering.py`**: NSFW content filtering using the Unitary toxic classification model (this is a sample implementation for reference, you can replace it with your own logic)
- **`entities.py`**: Pydantic models for request/response validation

## Endpoints

The Guardrail Server exposes two main endpoints for validation:

### PII Redaction Endpoint
- **POST `/pii-redaction`**
- Validates and optionally transforms incoming OpenAI chat completion requests before they are processed. Uses Presidio to detect and redact Personally Identifiable Information (PII) from messages.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for input.
- `ChatCompletionCreateParams` - Content was transformed, returns the modified request with PII redacted
- `HTTP 400/500` - Guardrails failed with error details for input.

### NSFW Filtering Endpoint
- **POST `/nsfw-filtering`**
- Validates and optionally transforms outgoing OpenAI chat completion responses to filter out NSFW content. Uses the Unitary toxic classification model to detect toxic, sexually explicit, and obscene content.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for output.
- `ChatCompletion` - Content was transformed, returns the modified response with NSFW content replaced
- `HTTP 400/500` - Guardrails failed with error details for output.




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

### NSFW Filtering with Unitary Toxic Classification Model

The NSFW filtering endpoint can be used to validate and optionally transform the response from the LLM before returning it to the client. If the output is transformed (e.g., content is modified or formatted), the endpoint will return the modified response body. The NSFW filtering uses the Unitary toxic classification model with configurable thresholds for toxicity, sexual content, and obscenity detection. Link to the model: [Unitary Toxic Classification Model](https://huggingface.co/unitary/unbiased-toxic-roberta)



### PII Redaction with Presidio
The PII redaction endpoint uses Presidio to detect and remove Personally Identifiable Information (PII) from incoming messages. This ensures that sensitive information is anonymized before further processing. Link to the library: [Presidio](https://github.com/microsoft/presidio)


## Customization

The modular architecture makes it easy to customize the guardrail logic:

- **PII Redaction**: Modify `guardrails/pii_redaction.py` to customize PII detection and redaction rules
- **NSFW Filtering**: Modify `guardrails/nsfw_filtering.py` to customize content filtering thresholds and rules
- **Request/Response Models**: Modify `entities.py` to add new fields or validation rules

Replace the example guardrail logic in the respective files with your own implementation. The NSFW filtering uses the Unitary toxic classification model with configurable thresholds for toxicity, sexual content, and obscenity detection.