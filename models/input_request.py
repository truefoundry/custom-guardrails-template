from pydantic import BaseModel
from openai.types.chat.completion_create_params import CompletionCreateParams

from models.request_config import RequestConfig
from models.request_context import RequestContext

class InputRequest(BaseModel):
    requestBody: CompletionCreateParams
    config: RequestConfig
    context: RequestContext