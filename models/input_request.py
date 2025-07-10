from pydantic import BaseModel
from openai.types.chat.completion_create_params import CompletionCreateParams

from models.request_config import RequestConfig
from models.request_context import RequestContext


class InputRequest(BaseModel):
    """
    InputRequest is a model for the input request to the guardrail server.

    Attributes:
        requestBody (CompletionCreateParams): The request body to the guardrail server.
        config (RequestConfig): The configuration for the guardrail server.
        context (RequestContext): The context for the guardrail server.
    """
    requestBody: CompletionCreateParams
    config: RequestConfig
    context: RequestContext