# Guardrail Server

A FastAPI application that provides input and output guardrail endpoints for content validation and transformation.

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


## Endpoints

### GET /
Health check endpoint that returns server status.

### POST /input
Input guardrail endpoint for validating and potentially transforming incoming OpenAI chat completion requests.



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
      "subjectSlug": "john_doe",
      "subjectDisplayName": "John Doe"
    },
    "metadata": {
      "ip_address": "192.168.1.1",
      "session_id": "abc123"
    }
  }
}
```

**Note**: The `requestBody` is accessible within the endpoint and can be used if needed for custom processing.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for input.
- `ChatCompletionCreateParams` - Content was transformed, returns the modified request
- `HTTP 400/500` - Guardrails failed with error details for input.

### POST /output
Output guardrail endpoint for validating and potentially transforming OpenAI chat completion responses.

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
      "subjectSlug": "john_doe",
      "subjectDisplayName": "John Doe"
    },
    "metadata": {
      "ip_address": "192.168.1.1",
      "session_id": "abc123"
    }
  }
}
```

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for output.
- `ChatCompletion` - Content was transformed, returns the modified response for output.
- `HTTP 400/500` - Guardrails failed with error details for output.


## Models
- [InputRequest](models/input_request.py) - The input request to the guardrail server in case of guardrail before input to model.
- [OutputRequest](models/output_request.py) - The output request to the guardrail server in case of guardrail after output from model.
- [RequestContext](models/request_context.py) - The contextual information like user, metadata, etc sent to the guardrail server.
- [RequestConfig](models/request_config.py) - The configuration for the guardrail server.
- [InputGuardrailResponse](models/input_guardrail_response.py) - The response from the guardrail server in case of guardrail before input to model.
- [OutputGuardrailResponse](models/output_guardrail_response.py) - The response from the guardrail server in case of guardrail after output from model.
- [RequestConfig](models/request_config.py) - The configuration for the guardrail server.
- [Metadata](models/metadata.py) - The metadata which is sent with the request to the ai-gateway so it can be used at guardrail server if needed.
- [Subject](models/subject.py) - This class is for user/team/virtual-account information.

### InputRequest

**Attributes:**
- `requestBody`: (dict) The input payload sent to the guardrail server.
- `config`: (RequestConfig) Configuration options for the guardrail server.
- `context`: (RequestContext) Contextual information such as user and metadata.

### OutputRequest

**Attributes:**
- `requestBody`: (dict) The input payload originally sent to the model.
- `responseBody`: (dict) The model's output to be checked by the guardrail server.
- `config`: (RequestConfig) Configuration options for the guardrail server.
- `context`: (RequestContext) Contextual information such as user and metadata.

### InputGuardrailResponse

**Attributes:**
- `result`: (dict) The processed or validated input, possibly transformed.
- `transformed`: (bool) Indicates if the input was modified by the guardrail.
- `message`: (str) Additional information or explanation from the guardrail.

### RequestContext

**Attributes:**
- `user`: (Subject) Information about the user, team, or virtual account making the request.
- `metadata`: (Metadata) Additional metadata relevant to the request.

## Request Config

The `RequestConfig` class is used to store arbitrary request configuration. Ensure that all configuration options are clearly defined and documented in the relevant sections above.

## Example Usage

### Input Guardrail (Success)
```bash
curl -X POST "http://localhost:8000/input" \
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
           "subjectSlug": "john_doe",
           "subjectDisplayName": "John Doe"
         },
         "metadata": {
           "ip_address": "192.168.1.1",
           "session_id": "abc123"
         }
       }
     }'
```

### Input Guardrail (With Transformation)
```bash
curl -X POST "http://localhost:8000/input" \
     -H "Content-Type: application/json" \
     -d '{
       "requestBody": {
         "messages": [
           {"role": "user", "content": "Hello John, How are you?"}
         ],
         "model": "gpt-3.5-turbo"
       },
       "config": {"transform_input": true},
       "context": {"user": {"subjectId": "123", "subjectType": "user", "subjectSlug": "john_doe", "subjectDisplayName": "John Doe"}}
     }'
```

### Output Guardrail (Success)
```bash
curl -X POST "http://localhost:8000/output" \
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
      "check_sensitive_data": false
    },
    "context": {
      "user": {
        "subjectId": "123",
        "subjectType": "user",
        "subjectSlug": "john_doe",
        "subjectDisplayName": "John Doe"
      },
      "metadata": {
        "environment": "production"
      }
    }
  }'
```

### Input Guardrail with PII Removal
The input guardrail endpoint uses Presidio to detect and remove Personally Identifiable Information (PII) from incoming messages. This ensures that sensitive information is anonymized before further processing.

**Example Usage with PII Removal**
```bash

  curl -X POST "http://localhost:8000/input" \
     -H "Content-Type: application/json" \
     -d '{
       "requestBody": {
         "messages": [
           {"role": "user", "content": "Hello John, How are you? Is this your email address? john@gmail.com"}
         ],
         "model": "gpt-3.5-turbo"
       },
       "config": {"transform_input": true},
       "context": {"user": {"subjectId": "123", "subjectType": "user", "subjectSlug": "john_doe", "subjectDisplayName": "John Doe"}}
     }'
```
In this example, Presidio will detect and anonymize the name and email address in the message content.

## Customization

Replace the example guardrail logic in `