# Guardrail Server

A FastAPI application that provides comprehensive content validation and transformation endpoints using various guardrail technologies including Presidio, Guardrails AI, and local evaluation models.

## Architecture

The application follows a modular architecture with separate modules for different functionalities:

- **`main.py`**: FastAPI application with route definitions
- **`guardrail/`**: Directory containing all guardrail implementations
  - **`pii_redaction_presidio.py`**: PII detection and redaction using Presidio
  - **`pii_detection_guardrails_ai.py`**: PII detection using Guardrails AI
  - **`nsfw_filtering_local_eval.py`**: NSFW content filtering using local Unitary toxic classification model
  - **`drug_mention_guardrails_ai.py`**: Drug mention detection using Guardrails AI
  - **`web_sanitization_guardrails_ai.py`**: Web content sanitization using Guardrails AI
- **`entities.py`**: Pydantic models for request/response validation

## Currently Exposed Endpoints

The Guardrail Server currently exposes two main endpoints for validation:

### PII Redaction Endpoint
- **POST `/pii-redaction`**
- Validates and optionally transforms incoming OpenAI chat completion requests before they are processed. Uses Presidio to detect and redact Personally Identifiable Information (PII) from messages.

#### What does guardrail server respond with?
- `null` - Guardrails passed, no transformation needed for input.
- `ChatCompletionCreateParams` - Content was transformed, returns the modified request with PII redacted.
- `HTTP 400/500` - Guardrails failed with error details for input.

### NSFW Filtering Endpoint (Local Model)
- **POST `/nsfw-filtering`**
- Validates and optionally transforms outgoing OpenAI chat completion responses to filter out NSFW content. Uses the Unitary toxic classification model to detect toxic, sexually explicit, and obscene content.

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





## Technology Stack

### PII Redaction with Presidio
The PII redaction endpoint uses Presidio to detect and remove Personally Identifiable Information (PII) from incoming messages. This ensures that sensitive information is anonymized before further processing. Link to the library: [Presidio](https://github.com/microsoft/presidio)

#### Configuring Presidio Recognizers

Presidio recognizers are configured via the `config` field in your request. The guardrail supports three configuration formats:

##### 1. Using Preset Configurations

Presets provide predefined sets of recognizers optimized for specific regions or use cases:

| Preset | Description | Recognizers Included |
|--------|-------------|---------------------|
| `INDIAN` / `INDIA` | Indian PII entities | PAN, Aadhaar, Voter ID, Passport, Vehicle Registration |
| `US` / `USA` | US PII entities | SSN, Passport, Driver License, ITIN, Bank Account, ABA Routing, Medical License |
| `UK` | UK PII entities | NHS Number, National Insurance Number (NINO) |
| `AUSTRALIAN` / `AU` / `AUSTRALIA` | Australian PII entities | ABN, ACN, TFN, Medicare |
| `SINGAPORE` / `SG` | Singapore PII entities | FIN, UEN |
| `EUROPEAN` / `EUROPE` / `EU` | European PII entities | Spanish NIF/NIE, Italian documents, Polish PESEL, Finnish ID, IBAN |
| `FINANCIAL` | Financial identifiers | Credit Card, IBAN, Bank Account, Crypto Wallet |
| `CONTACT` | Contact information | Email, Phone, IP Address, URL |
| `STANDARD` | Essential recognizers | Financial + Contact + Date/Time |
| `COMPREHENSIVE` / `ALL` | All available recognizers | All 35+ predefined recognizers |

**Example using a preset:**
```json
{
  "config": {
    "transform_input": true,
    "recognizers": "INDIAN"
  }
}
```

##### 2. Using Individual Recognizers

You can specify individual recognizers by their exact names:

**Example using specific recognizers:**
```json
{
  "config": {
    "transform_input": true,
    "recognizers": ["EmailRecognizer", "PhoneRecognizer", "CreditCardRecognizer"]
  }
}
```

**Available Individual Recognizers:**

| Category | Recognizers |
|----------|------------|
| **US** | `UsSsnRecognizer`, `UsPassportRecognizer`, `UsLicenseRecognizer`, `UsItinRecognizer`, `UsBankRecognizer`, `AbaRoutingRecognizer`, `MedicalLicenseRecognizer` |
| **UK** | `NhsRecognizer`, `UkNinoRecognizer` |
| **India** | `InPanRecognizer`, `InAadhaarRecognizer`, `InVehicleRegistrationRecognizer`, `InPassportRecognizer`, `InVoterRecognizer` |
| **Australia** | `AuAbnRecognizer`, `AuAcnRecognizer`, `AuTfnRecognizer`, `AuMedicareRecognizer` |
| **Singapore** | `SgFinRecognizer`, `SgUenRecognizer` |
| **Europe** | `EsNifRecognizer`, `EsNieRecognizer`, `ItDriverLicenseRecognizer`, `ItFiscalCodeRecognizer`, `ItIdentityCardRecognizer`, `ItPassportRecognizer`, `ItVatCodeRecognizer`, `PlPeselRecognizer`, `FiPersonalIdentityCodeRecognizer` |
| **Financial** | `CreditCardRecognizer`, `IbanRecognizer`, `CryptoRecognizer` |
| **Contact** | `EmailRecognizer`, `PhoneRecognizer`, `IpRecognizer`, `UrlRecognizer` |
| **Other** | `DateRecognizer`, `KrRrnRecognizer` |

##### 3. Combining Presets and Recognizers

You can mix presets with individual recognizers for flexible configuration:

**Example combining preset with additional recognizers:**
```json
{
  "config": {
    "transform_input": true,
    "recognizers": ["INDIAN", "EmailRecognizer", "CreditCardRecognizer"]
  }
}
```

**Example as comma-separated string:**
```json
{
  "config": {
    "transform_input": true,
    "recognizers": "FINANCIAL, CONTACT, InAadhaarRecognizer"
  }
}
```

##### 4. Language Configuration

You can specify the language for text analysis (default is `en`):

```json
{
  "config": {
    "transform_input": true,
    "recognizers": "US",
    "language": "en"
  }
}
```

Supported languages depend on the specific recognizers being used. Most recognizers work with English (`en`).

##### Complete Configuration Examples

**Example 1: Indian company protecting financial and contact info**
```bash
curl -X POST "http://localhost:8000/pii-redaction" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "My PAN is ABCDE1234F and email is john@example.com"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "config": {
      "transform_input": true,
      "recognizers": ["INDIAN", "CONTACT", "FINANCIAL"]
    },
    "context": {
      "user": {
        "subjectId": "123",
        "subjectType": "user",
        "subjectSlug": "john_doe@truefoundry.com",
        "subjectDisplayName": "John Doe"
      }
    }
  }'
```

**Example 2: US healthcare application with specific recognizers**
```bash
curl -X POST "http://localhost:8000/pii-redaction" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "SSN: 123-45-6789, Medical License: A123456"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "config": {
      "transform_input": true,
      "recognizers": ["UsSsnRecognizer", "MedicalLicenseRecognizer", "EmailRecognizer"]
    },
    "context": {
      "user": {
        "subjectId": "456",
        "subjectType": "user",
        "subjectSlug": "doctor@hospital.com",
        "subjectDisplayName": "Dr. Smith"
      }
    }
  }'
```

**Example 3: Global financial platform**
```bash
curl -X POST "http://localhost:8000/pii-redaction" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "Credit card: 4532-1234-5678-9010, IBAN: GB82WEST12345698765432"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "config": {
      "transform_input": true,
      "recognizers": "FINANCIAL"
    },
    "context": {
      "user": {
        "subjectId": "789",
        "subjectType": "user",
        "subjectSlug": "user@bank.com",
        "subjectDisplayName": "Banking User"
      }
    }
  }'
```

**Example 4: Check only without transformation**
```bash
curl -X POST "http://localhost:8000/pii-redaction" \
  -H "Content-Type: application/json" \
  -d '{
    "requestBody": {
      "messages": [
        {
          "role": "user",
          "content": "Hello world"
        }
      ],
      "model": "gpt-3.5-turbo"
    },
    "config": {
      "transform_input": false,
      "recognizers": "ALL"
    },
    "context": {
      "user": {
        "subjectId": "123",
        "subjectType": "user",
        "subjectSlug": "john_doe@truefoundry.com",
        "subjectDisplayName": "John Doe"
      }
    }
  }'
```

**Note**: If `transform_input` is `false`, the endpoint will not perform redaction even if PII is detected. Set it to `true` to enable PII redaction.

### NSFW Filtering with Unitary Toxic Classification Model
The NSFW filtering endpoint can be used to validate and optionally transform the response from the LLM before returning it to the client. If the output is transformed (e.g., content is modified or formatted), the endpoint will return the modified response body. The NSFW filtering uses the Unitary toxic classification model with configurable thresholds for toxicity, sexual content, and obscenity detection. Link to the model: [Unitary Toxic Classification Model](https://huggingface.co/unitary/unbiased-toxic-roberta)


## Customization

The modular architecture makes it easy to customize the guardrail logic:

- **PII Redaction**: Modify `guardrail/pii_redaction_presidio.py` to customize PII detection and redaction rules
- **NSFW Filtering (Local)**: Modify `guardrail/nsfw_filtering_local_eval.py` to customize content filtering thresholds and rules
- **Request/Response Models**: Modify `entities.py` to add new fields or validation rules

Replace the example guardrail logic in the respective files with your own implementation. The NSFW filtering uses the Unitary toxic classification model with configurable thresholds for toxicity, sexual content, and obscenity detection.

## Configuration Details

### NSFW Filtering (Local Model)
- **Thresholds**: 0.2 for toxicity, sexual_explicit, and obscene content
- **Model**: Unitary unbiased-toxic-roberta


## Adding Guardrails AI

This section provides comprehensive guidance on how to add new Guardrails AI validators to your guardrail server.

### Prerequisites

Before adding Guardrails AI validators, ensure you have:

1. **Guardrails AI Token**: Obtain a token from [Guardrails AI](https://guardrailsai.com/)
2. **Environment Setup**: Set the `GUARDRAILS_TOKEN` environment variable
3. **Dependencies**: Ensure `guardrails-ai` and `guardrails-ai[api]` are installed

### Setup Process

To set up Guardrails AI, you need to define the following function in your `setup.py` file and ensure it is called before any other application logic (such as importing or running your FastAPI app):


```python
# setup.py handles the configuration
def setup_guardrails():
    subprocess.run([
        "guardrails", "configure",
        "--disable-metrics",
        "--disable-remote-inferencing",
        "--token", GUARDRAILS_TOKEN
    ], check=True)

    subprocess.run([
        "guardrails", "hub", "install", "hub://guardrails/detect_pii"
    ], check=True)

```

### Example Guardrails AI Validators

This template includes example Guardrails AI validators to help you get started. You can use these as references when adding your own.

| Validator         | Purpose                                         | Hub URL                                 | File                          |
|-------------------|-------------------------------------------------|------------------------------------------|-------------------------------|
| `DetectPII`       | Detects Personally Identifiable Information     | `hub://guardrails/detect_pii`           | `pii_detection_guardrails_ai.py` |
| `MentionsDrugs`   | Detects drug mentions in content                | `hub://cartesia/mentions_drugs`         | `drug_mention_guardrails_ai.py`  |
| `WebSanitization` | Sanitizes web content and detects malicious code| `hub://guardrails/web_sanitization`     | `web_sanitization_guardrails_ai.py` |

Use these examples as a template for integrating additional Guardrails AI validators into your project.

### Creating a New Guardrails AI Validator

#### Step 1: Install the Validator

Add the validator installation to `setup.py`:

```python
def setup_guardrails():
    # ... existing setup code ...
    
    # Add your new validator
    subprocess.run([
        "guardrails", "hub", "install", "hub://your-org/your-validator"
    ], check=True)
```

#### Step 2: Create the Implementation File

Create a new file in the `guardrail/` directory following this pattern:

**For Input Validation** (e.g., `guardrail/your_validator_guardrails_ai.py`):
```python
from typing import Optional
from fastapi import HTTPException
from guardrails import Guard
from guardrails.hub import YourValidator  # Import your validator

from entities import InputGuardrailRequest

# Setup the Guard with the validator
guard = Guard().use(YourValidator, on_fail="exception")

def your_validator_function(request: InputGuardrailRequest) -> Optional[dict]:
    """
    Validate input using Guardrails AI validator.
    
    Args:
        request: Input guardrail request containing messages to validate
        
    Returns:
        None if validation passes, raises HTTPException if validation fails
    """
    try:
        messages = request.requestBody.get("messages", [])
        for message in messages:
            if isinstance(message, dict) and message.get("content"):
                guard.validate(message["content"])
        return None
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**For Output Validation** (e.g., `guardrail/your_output_validator_guardrails_ai.py`):
```python
from typing import Optional
from fastapi import HTTPException
from guardrails import Guard
from guardrails.hub import YourOutputValidator  # Import your validator

from entities import OutputGuardrailRequest

# Setup the Guard with the validator
guard = Guard().use(YourOutputValidator, on_fail="exception")

def your_output_validator_function(request: OutputGuardrailRequest) -> Optional[dict]:
    """
    Validate output using Guardrails AI validator.
    
    Args:
        request: Output guardrail request containing response to validate
        
    Returns:
        None if validation passes, raises HTTPException if validation fails
    """
    try:
        for choice in request.responseBody.get("choices", []):
            if "content" in choice.get("message", {}):
                guard.validate(choice["message"]["content"])
        return None
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### Step 3: Add the Route

Import and register your validator in `main.py`:

```python
# Add import
from guardrail.your_validator_guardrails_ai import your_validator_function

# Add route
app.add_api_route("/your-endpoint", endpoint=your_validator_function, methods=["POST"])
```

### Best Practices

1. **Error Handling**: Always wrap validator calls in try-catch blocks
2. **HTTP Status Codes**: Use appropriate status codes (400 for validation failures, 500 for server errors)
3. **Logging**: Consider adding logging for debugging and monitoring
4. **Testing**: Test your validators with various inputs including edge cases

## Adding New Endpoints

Currently, only PII redaction and NSFW filtering endpoints are exposed. To add new guardrail functionality:

1. Create a new guardrail implementation file in the `guardrail/` directory
2. Follow the existing pattern for input or output validation
3. Add the route to `main.py` using `app.add_api_route()`
4. Update this README with the new endpoint documentation