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

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

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
    "user_id": "123",
    "session_id": "abc"
  }
}
```

**Response:**
- `null` - Guardrails passed, no transformation needed
- `ChatCompletionCreateParams` - Content was transformed, returns the modified request
- `HTTP 400/500` - Guardrails failed with error details

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
    "user_role": "restricted",
    "user_id": "123"
  }
}
```

**Response:**
- `null` - Guardrails passed, no transformation needed
- `ChatCompletion` - Content was transformed, returns the modified response
- `HTTP 400/500` - Guardrails failed with error details

## Configuration Options

The `config` parameter supports various options to control guardrail behavior:

### Input Guardrails
- `check_content`: Boolean - Check for prohibited content
- `transform_input`: Boolean - Apply input transformations

### Output Guardrails
- `check_sensitive_data`: Boolean - Check for sensitive information
- `transform_output`: Boolean - Apply output transformations
- `filter_by_context`: Boolean - Filter content based on user context

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
       "context": {"user_id": "123"}
     }'
```

### Input Guardrail (With Transformation)
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
       "config": {"transform_input": true},
       "context": {"user_id": "123"}
     }'
```

### Output Guardrail (Success)
```bash
curl -X POST "http://localhost:8000/output" \
     -H "Content-Type: application/json" \
     -d '{
       "requestBody": {
         "messages": [
           {"role": "user", "content": "Hello"}
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
       "config": {"check_sensitive_data": false},
       "context": {"user_role": "admin"}
     }'
```

## Customization

Replace the example guardrail logic in `main.py` with your actual implementation:
- Add your content validation rules
- Implement your transformation logic
- Configure appropriate error handling 