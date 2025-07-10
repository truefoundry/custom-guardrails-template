from pydantic import BaseModel
from openai.types.chat.completion_create_params import CompletionCreateParams
from openai.types.chat.chat_completion import ChatCompletion

from models.request_config import RequestConfig
from models.request_context import RequestContext

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
    config: RequestConfig
    context: RequestContext
