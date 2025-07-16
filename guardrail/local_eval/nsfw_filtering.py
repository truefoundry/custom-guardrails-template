from typing import Optional

from fastapi import HTTPException
from entities import OutputGuardrailRequest
from transformers import pipeline

classifier = pipeline("text-classification", model="unitary/unbiased-toxic-roberta")

def nsfw_filtering(request: OutputGuardrailRequest) -> Optional[dict]:
    transformed_body = request.responseBody.copy()  # Use dict copy method
    for choice in transformed_body.get("choices", []):
        if "content" in choice.get("message", {}):
            classification_results = classifier(choice["message"]["content"])
            for result in classification_results:
                if (
                    (result['label'] == 'toxicity' and result['score'] > 0.2) or
                    (result['label'] == 'sexual_explicit' and result['score'] > 0.2) or
                    (result['label'] == 'obscene' and result['score'] > 0.2)
                ):
                    raise HTTPException(status_code=400, detail=f"This message is not allowed as it is NSFW")

