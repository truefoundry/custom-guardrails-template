import os
import logging
from typing import Optional

from entities import InputGuardrailRequest
from presidio_entities import DEFAULT_LANGUAGE, DEFAULT_RECOGNIZERS, parse_recognizers, get_analyzer, anonymizer

# Configure logging
logger = logging.getLogger(__name__)



def process_input_guardrail(request: InputGuardrailRequest) -> Optional[dict]:    # Check if transformation is enabled
    if not request.config.get("transform_input", False):
        logger.debug("Transform input disabled, skipping PII redaction")
        return None
    
    # Get recognizer configuration
    recognizer_config = request.config.get("recognizers",DEFAULT_RECOGNIZERS)
    
    # Get language configuration
    language = request.config.get("language", DEFAULT_LANGUAGE)
        
    try:
        # Parse and get recognizers
        recognizers = parse_recognizers(recognizer_config)
        
        # Create analyzer with specified recognizers
        analyzer = get_analyzer(recognizers, language)
        
        # Process messages
        messages = request.requestBody.get('messages', [])
        transformed = False
        transformed_messages = []
        
        for message in messages:
            if isinstance(message, dict) and message.get("content"):
                # Analyze for PII
                results = analyzer.analyze(text=message["content"], language=language)
                
                # Anonymize detected PII
                anonymized_content = anonymizer.anonymize(
                    text=message["content"], 
                    analyzer_results=results
                )
                
                # Track if any transformation occurred
                if anonymized_content.text != message["content"]:
                    transformed = True
                    logger.info(
                        f"PII detected and redacted. "
                        f"Entities found: {[r.entity_type for r in results]}"
                    )
                
                transformed_messages.append({
                    "role": message["role"],
                    "content": anonymized_content.text
                })
        
        # Return transformed body only if PII was actually redacted
        if transformed:
            request.requestBody['messages'] = transformed_messages
            return request.requestBody
        else:
            logger.debug("No PII detected, returning None")
            return None
            
    except Exception as e:
        logger.error(f"Error during PII redaction: {str(e)}", exc_info=True)
        raise
