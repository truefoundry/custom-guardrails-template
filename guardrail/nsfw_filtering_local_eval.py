from entities import OutputGuardrailRequest, ValidateGuardrailResponse
from transformers import pipeline

classifier = pipeline("text-classification", model="unitary/unbiased-toxic-roberta")


def nsfw_filtering(request: OutputGuardrailRequest) -> ValidateGuardrailResponse:
    for choice in request.responseBody.get("choices", []):
        if "content" in choice.get("message", {}):
            classification_results = classifier(choice["message"]["content"])
            for result in classification_results:
                if (
                    (result["label"] == "toxicity" and result["score"] > 0.2)
                    or (result["label"] == "sexual_explicit" and result["score"] > 0.2)
                    or (result["label"] == "obscene" and result["score"] > 0.2)
                ):
                    return ValidateGuardrailResponse(
                        verdict=False,
                        message="This message is not allowed as it is NSFW",
                    )
    return ValidateGuardrailResponse(verdict=True)
