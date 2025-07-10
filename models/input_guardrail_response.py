from typing import Optional, Any
from pydantic import BaseModel

class InputGuardrailResponse(BaseModel):
    result: Optional[Any] = None
    transformed: bool = False
    message: str = "Success"
