from pydantic import BaseModel
from openai.types.chat.completion_create_params import CompletionCreateParams
from openai.types.chat.chat_completion import ChatCompletion

from models.request_config import RequestConfig
from models.request_context import RequestContext

class OutputRequest(BaseModel):
    requestBody: CompletionCreateParams
    responseBody: ChatCompletion
    config: RequestConfig
    context: RequestContext
