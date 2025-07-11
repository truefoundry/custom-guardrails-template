from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel
from openai.types.chat.completion_create_params import CompletionCreateParams
from openai.types.chat.chat_completion import ChatCompletion


class RequestContext(BaseModel):
    """
    RequestContext encapsulates contextual information about the request.
    This context is added by the Truefoundry AI Gateway and includes user and metadata information
    relevant to the request lifecycle.

    Attributes:
        user (Subject): Information about the user, team, or virtual account making the request.
            The expected datatype is Subject (see class definition below), but for flexibility, the actual field is typed as dict.

            class Subject(BaseModel):
                subjectId: str
                subjectType: SubjectType
                subjectSlug: Optional[str] = None
                subjectDisplayName: Optional[str] = None

            class SubjectType(str, Enum):
                user = 'user'
                team = 'team'
                serviceaccount = 'serviceaccount'

        metadata (dict[str, str]): Additional metadata relevant to the request, such as IP address,
            session ID, or other request-scoped attributes. This is passed by user at the time of request from the client to AI Gateway.
    """
    user: dict  # Expected datatype: Subject (see docstring)
    metadata: Optional[dict[str, str]] = None



class OutputGuardrailRequest(BaseModel):
    """
    OutputGuardrailRequest represents the schema for requests sent to the output guardrail endpoint.
    It encapsulates the original model input (requestBody), the model's output (responseBody), 
    configuration options (config), and contextual information (context) about the request. 
    This model is used to validate and optionally transform the LLM's response before it is returned to the client, 
    enabling enforcement of output guardrails such as sensitive data filtering, content modification, or context-based checks.

    Attributes:
        requestBody (CompletionCreateParams): The request body to the guardrail server.
            See: https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py
        responseBody (ChatCompletion): The response body from the guardrail server.
            See: https://github.com/openai/openai-python/blob/main/src/openai/types/chat/chat_completion.py
        config (RequestConfig): The configuration for the guardrail server.
        context (RequestContext): The context for the guardrail server.
    """
    requestBody: dict  # See CompletionCreateParams class for schema
    responseBody: dict  # See ChatCompletion class for schema
    config: Optional[dict] = None
    context: RequestContext


class InputGuardrailRequest(BaseModel):
    """
    InputGuardrailRequest represents the schema for requests sent to the input guardrail endpoint.
    It encapsulates the original model input (requestBody), configuration options (config), 
    and contextual information (context) about the request. This model is used to validate and optionally transform 
    the LLM's input before it is sent to the model, enabling enforcement of input guardrails such as sensitive data filtering, 
    content modification, or context-based checks.

    Attributes:
        requestBody (CompletionCreateParams): The request body to the guardrail server.
            See: https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py
        config (RequestConfig): The configuration for the guardrail server.
        context (RequestContext): The context for the guardrail server.
    """
    requestBody: dict
    context: RequestContext
    config: Optional[dict] = None

