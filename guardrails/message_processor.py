from typing import Optional
from openai.types.chat.chat_completion import ChatCompletion
from entities import OutputGuardrailRequest


def process_output_guardrail(request: OutputGuardrailRequest) -> Optional[dict]:
    if not request.config.get("transform_output", False):
        return None
    transformed_body = request.responseBody.copy()  # Use dict copy method
    for choice in transformed_body.get("choices", []):
        if "content" in choice.get("message", {}):
            choice["message"]["content"] = f"[Processed] {choice['message']['content']}"        
    return transformed_body

