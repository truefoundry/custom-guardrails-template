from typing import Optional, Any
from pydantic import BaseModel

class InputGuardrailResponse(BaseModel):
    """
    InputGuardrailResponse is a model for the response from the input guardrail.
    
    Attributes:
        result (Optional[Any]): The result of the guardrail.
        transformed (bool): Whether the result was transformed.
        message (str): The message from the guardrail.
    """
    result: Optional[Any] = None
    transformed: bool = False
    message: str = "Success"
