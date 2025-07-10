from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel
from openai.types.chat.completion_create_params import CompletionCreateParams
from openai.types.chat.chat_completion import ChatCompletion

class SubjectType(str, Enum):
    user = 'user'
    team = 'team'
    serviceaccount = 'serviceaccount'

class Subject(BaseModel):
    subjectId: str
    subjectType: SubjectType
    subjectSlug: Optional[str] = None
    subjectDisplayName: Optional[str] = None


class RequestContext(BaseModel):
    """
    RequestContext encapsulates contextual information about the request.

    Attributes:
        user (Subject): Information about the user, team, or virtual account making the request.
        metadata (dict[str, str]): Additional metadata relevant to the request, such as IP address,
            session ID, or other request-scoped attributes. This is passed by user at the time of request from the client to AI Gateway.
    """
    user: Subject
    metadata: dict[str, str]



class OutputRequest(BaseModel):
    """
    OutputRequest is a model for the output request to the guardrail server.

    Attributes:
        requestBody (CompletionCreateParams): The request body to the guardrail server.
        responseBody (ChatCompletion): The response body from the guardrail server.
        config (RequestConfig): The configuration for the guardrail server.
        context (RequestContext): The context for the guardrail server.
    """
    requestBody: CompletionCreateParams
    responseBody: ChatCompletion
    config: dict
    context: RequestContext


class InputRequest(BaseModel):
    """
    InputRequest is a model for the input request to the guardrail server.

    Attributes:
        requestBody (CompletionCreateParams): The request body to the guardrail server.
        config (RequestConfig): The configuration for the guardrail server.
        context (RequestContext): The context for the guardrail server.
    """
    requestBody: CompletionCreateParams
    context: RequestContext
    config: dict

