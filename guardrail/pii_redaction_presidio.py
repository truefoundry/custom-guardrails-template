from typing import Optional
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from entities import InputGuardrailRequest

# Initialize Presidio
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def process_input_guardrail(request: InputGuardrailRequest) -> Optional[dict]:
    if not request.config.get("transform_input", False):
        return None
    transformed = False
    messages = request.requestBody.get('messages', [])
    transformed_messages = []
    for message in messages:
        if isinstance(message, dict) and message.get("content"):
            results = analyzer.analyze(text=message["content"], entities=[], language='en')
            anonymized_content = anonymizer.anonymize(text=message["content"], analyzer_results=results)
            if anonymized_content.text != message["content"]:
                transformed = True
            transformed_messages.append({
                "role": message["role"],
                "content": anonymized_content.text
            })
    request.requestBody['messages'] = transformed_messages
    if transformed:
        return request.requestBody
    return None
