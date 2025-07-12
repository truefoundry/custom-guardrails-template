from typing import Optional
from entities import OutputGuardrailRequest
from transformers import pipeline

classifier = pipeline("text-classification", model="unitary/unbiased-toxic-roberta")

def nsfw_filtering(request: OutputGuardrailRequest) -> Optional[dict]:
    if not request.config.get("transform_output", False):
        print("No transformation needed as transform_output is ", request.config.get("transform_output"))
        return None
    transformed_body = request.responseBody.copy()  # Use dict copy method
    for choice in transformed_body.get("choices", []):
        is_allowed = True
        if "content" in choice.get("message", {}):
            classification_results = classifier(choice["message"]["content"])
            for result in classification_results:
                if (
                    (result['label'] == 'toxicity' and result['score'] > 0.5) or
                    (result['label'] == 'sexual_explicit' and result['score'] > 0.5) or
                    (result['label'] == 'obscene' and result['score'] > 0.5)
                ):
                    is_allowed = False
                    break
            if not is_allowed:
                choice["message"]["content"] = f"This message is not allowed as it is NSFW"
    return transformed_body

