from typing import Optional
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.predefined_recognizers import InAadhaarRecognizer
from presidio_analyzer.predefined_recognizers import InPanRecognizer
from presidio_analyzer.predefined_recognizers import InPassportRecognizer
from presidio_analyzer.predefined_recognizers import InVehicleRegistrationRecognizer
from presidio_analyzer.predefined_recognizers import InVoterRecognizer
from presidio_anonymizer import AnonymizerEngine

from entities import InputGuardrailRequest

# Initialize Presidio
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

adhoc_indian_recognizers = [InPanRecognizer(),InAadhaarRecognizer(),InPassportRecognizer(),InVehicleRegistrationRecognizer(),InVoterRecognizer()]

def process_input_guardrail(request: InputGuardrailRequest) -> Optional[dict]:
    if not request.config.get("transform_input", False):
        return None
    transformed = False
    messages = request.requestBody.get('messages', [])
    transformed_messages = []
    for message in messages:
        if isinstance(message, dict) and message.get("content"):
            if request.config.get("indian_pii_detection", False):
                results = analyzer.analyze(
                    text=message["content"], 
                    language='en', 
                    ad_hoc_recognizers=adhoc_indian_recognizers
                )
            else:
                results = analyzer.analyze(
                    text=message["content"],
                    language='en'
                )
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
