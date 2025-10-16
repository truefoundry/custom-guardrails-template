from enum import Enum
import logging
import os
from presidio_analyzer import AnalyzerEngine, EntityRecognizer, RecognizerRegistry
from presidio_analyzer.predefined_recognizers import (
    # US Recognizers
    UsSsnRecognizer,
    UsPassportRecognizer,
    UsLicenseRecognizer,
    UsItinRecognizer,
    UsBankRecognizer,
    AbaRoutingRecognizer,
    MedicalLicenseRecognizer,
    # UK Recognizers
    NhsRecognizer,
    UkNinoRecognizer,
    # Indian Recognizers
    InPanRecognizer,
    InAadhaarRecognizer,
    InVehicleRegistrationRecognizer,
    InPassportRecognizer,
    InVoterRecognizer,
    # Singapore Recognizers
    SgFinRecognizer,
    SgUenRecognizer,
    # Australian Recognizers
    AuAbnRecognizer,
    AuAcnRecognizer,
    AuTfnRecognizer,
    AuMedicareRecognizer,
    # Spanish Recognizers
    EsNifRecognizer,
    EsNieRecognizer,
    # Italian Recognizers
    ItDriverLicenseRecognizer,
    ItFiscalCodeRecognizer,
    ItIdentityCardRecognizer,
    ItPassportRecognizer,
    ItVatCodeRecognizer,
    # Polish Recognizers
    PlPeselRecognizer,
    # Korean Recognizers
    KrRrnRecognizer,
    # Finnish Recognizers
    FiPersonalIdentityCodeRecognizer,
    # Financial Recognizers
    CreditCardRecognizer,
    IbanRecognizer,
    CryptoRecognizer,
    # Contact & Technology Recognizers
    EmailRecognizer,
    PhoneRecognizer,
    IpRecognizer,
    UrlRecognizer,
    # Date & Time Recognizers
    DateRecognizer,
    # NLP Model-based Recognizers
    SpacyRecognizer,
    TransformersRecognizer,
    StanzaRecognizer,
    # Azure Recognizers
    AzureAILanguageRecognizer,
    AzureHealthDeidRecognizer,
    # GLiNER Recognizer
    GLiNERRecognizer,
)
from presidio_anonymizer import AnonymizerEngine


# Default configuration
DEFAULT_RECOGNIZERS = "ALL"
DEFAULT_LANGUAGE = "en"

# Configure logging
logger = logging.getLogger(__name__)

# Singleton anonymizer instance
anonymizer = AnonymizerEngine()


def parse_recognizers(recognizer_config: str | list[str]) -> list[str]:
    # Normalize input to list
    if isinstance(recognizer_config, str):
        # Split by comma if contains comma
        if ',' in recognizer_config:
            recognizer_config = [r.strip() for r in recognizer_config.split(',')]
        else:
            recognizer_config = [recognizer_config]
    
    recognizer_config = [r.strip().upper() for r in recognizer_config if r.strip()]
    
    if not recognizer_config:
        logger.warning("Empty recognizer configuration, using default: INDIAN")
        return PresidioRecognizerType.get_indian_recognizers()
    
    if "ALL" in recognizer_config or "COMPREHENSIVE" in recognizer_config:
        logger.info("Using ALL recognizers")
        return PresidioRecognizerType.get_all_recognizers()

    recognizers = []
    all_available = PresidioRecognizerType.get_all_recognizers()
    
    # Process each item in config
    for item in recognizer_config:
        try:
            # Try as preset first
            preset_recognizers = PresidioRecognizerType.get_from_preset(item)
            recognizers.extend(preset_recognizers)
            logger.debug(f"Added preset '{item}': {len(preset_recognizers)} recognizers")
        except ValueError:
            # Not a preset, check if it's a direct recognizer name
            if item in all_available:
                recognizers.append(item)
                logger.debug(f"Added recognizer: {item}")
            else:
                logger.warning(f"Unrecognized recognizer or preset: {item}")
    
    # Remove duplicates while preserving order
    recognizers = list(dict.fromkeys(recognizers))
    
    if not recognizers:
        raise ValueError(
            f"No valid recognizers found in configuration: {recognizer_config}. "
            f"Available presets: {', '.join(['INDIAN', 'US', 'UK', 'STANDARD', 'ALL'])}"
        )
    
    logger.info(f"Using {len(recognizers)} recognizers")
    return recognizers


def get_analyzer(recognizers: list[str], language: str = "en") -> AnalyzerEngine:
    filtered_registry = RecognizerRegistry()
    loaded_count = 0
    
    for recognizer_name in recognizers:
        try:
            recognizer_instance = PresidioRecognizerType.get_recognizer(recognizer_name)
            filtered_registry.add_recognizer(recognizer_instance)
            loaded_count += 1
            logger.debug(f"Loaded recognizer: {recognizer_name}")
        except ValueError as e:
            logger.warning(f"Recognizer '{recognizer_name}' not found: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load recognizer '{recognizer_name}': {str(e)}")
    
    if loaded_count == 0:
        logger.warning(f"No recognizers were loaded from requested list: {recognizers}")
    else:
        logger.info(f"Successfully loaded {loaded_count}/{len(recognizers)} recognizers")
    
    return AnalyzerEngine(registry=filtered_registry, supported_languages=[language])


class PresidioRecognizerType(str, Enum):
    """
    Comprehensive enum of all available Presidio recognizer types.
    
    Reference: https://github.com/microsoft/presidio
    Documentation: https://microsoft.github.io/presidio/supported_entities/
    """
    
    # ==================== US RECOGNIZERS ====================
    US_SSN = "UsSsnRecognizer"  # US Social Security Number
    US_PASSPORT = "UsPassportRecognizer"  # US Passport Number
    US_DRIVER_LICENSE = "UsLicenseRecognizer"  # US Driver License
    US_ITIN = "UsItinRecognizer"  # US Individual Taxpayer Identification Number
    US_BANK_ACCOUNT = "UsBankRecognizer"  # US Bank Account Number
    US_ABA_ROUTING = "AbaRoutingRecognizer"  # US ABA Routing Number
    
    # ==================== UK RECOGNIZERS ====================
    UK_NHS = "NhsRecognizer"  # UK National Health Service Number
    UK_NINO = "UkNinoRecognizer"  # UK National Insurance Number
    
    # ==================== INDIAN RECOGNIZERS ====================
    IN_PAN = "InPanRecognizer"  # Indian Permanent Account Number
    IN_AADHAAR = "InAadhaarRecognizer"  # Indian Aadhaar Number
    IN_VEHICLE_REGISTRATION = "InVehicleRegistrationRecognizer"  # Indian Vehicle Registration
    IN_PASSPORT = "InPassportRecognizer"  # Indian Passport Number
    IN_VOTER_ID = "InVoterRecognizer"  # Indian Voter ID
    
    # ==================== SINGAPORE RECOGNIZERS ====================
    SG_FIN = "SgFinRecognizer"  # Singapore Foreign Identification Number
    SG_UEN = "SgUenRecognizer"  # Singapore Unique Entity Number
    
    # ==================== AUSTRALIAN RECOGNIZERS ====================
    AU_ABN = "AuAbnRecognizer"  # Australian Business Number
    AU_ACN = "AuAcnRecognizer"  # Australian Company Number
    AU_TFN = "AuTfnRecognizer"  # Australian Tax File Number
    AU_MEDICARE = "AuMedicareRecognizer"  # Australian Medicare Number
    
    # ==================== SPANISH RECOGNIZERS ====================
    ES_NIF = "EsNifRecognizer"  # Spanish National Identity Document
    ES_NIE = "EsNieRecognizer"  # Spanish Foreigner Identity Document
    
    # ==================== ITALIAN RECOGNIZERS ====================
    IT_DRIVER_LICENSE = "ItDriverLicenseRecognizer"  # Italian Driver License
    IT_FISCAL_CODE = "ItFiscalCodeRecognizer"  # Italian Fiscal Code
    IT_IDENTITY_CARD = "ItIdentityCardRecognizer"  # Italian Identity Card
    IT_PASSPORT = "ItPassportRecognizer"  # Italian Passport
    IT_VAT_CODE = "ItVatCodeRecognizer"  # Italian VAT Code
    
    # ==================== POLISH RECOGNIZERS ====================
    PL_PESEL = "PlPeselRecognizer"  # Polish National Identification Number
    
    # ==================== KOREAN RECOGNIZERS ====================
    KR_RRN = "KrRrnRecognizer"  # Korean Resident Registration Number
    
    # ==================== FINNISH RECOGNIZERS ====================
    FI_PERSONAL_IDENTITY_CODE = "FiPersonalIdentityCodeRecognizer"  # Finnish Personal Identity Code
    
    # ==================== FINANCIAL RECOGNIZERS ====================
    CREDIT_CARD = "CreditCardRecognizer"  # Credit Card Numbers (Visa, Mastercard, Amex, etc.)
    IBAN = "IbanRecognizer"  # International Bank Account Number
    CRYPTO = "CryptoRecognizer"  # Cryptocurrency Wallet Addresses
    
    # ==================== TECHNOLOGY & CONTACT ====================
    EMAIL = "EmailRecognizer"  # Email Addresses
    PHONE = "PhoneRecognizer"  # Phone Numbers
    IP_ADDRESS = "IpRecognizer"  # IP Addresses (IPv4 and IPv6)
    URL = "UrlRecognizer"  # URLs and Web Addresses

    
    
    # ==================== DATE & TIME ====================
    DATE_TIME = "DateRecognizer"  # Date and Time Patterns
    MEDICAL_LICENSE = "MedicalLicenseRecognizer"  # Medical License Numbers
    
    # ==================== NLP MODEL-BASED RECOGNIZERS ====================
    SPACY = "SpacyRecognizer"  # Spacy-based NER recognizer
    TRANSFORMERS = "TransformersRecognizer"  # Transformers-based NER recognizer
    STANZA = "StanzaRecognizer"  # Stanza-based NER recognizer
    GLINER = "GLiNERRecognizer"  # GLiNER-based NER recognizer
    
    # ==================== AZURE RECOGNIZERS ====================
    AZURE_AI_LANGUAGE = "AzureAILanguageRecognizer"  # Azure AI Language Service
    AZURE_HEALTH_DEID = "AzureHealthDeidRecognizer"  # Azure Health De-identification
    
    
    @classmethod
    def get_us_recognizers(cls) -> list[str]:
        """Returns all US-specific recognizers."""
        return [
            cls.US_SSN.value,
            cls.US_PASSPORT.value,
            cls.US_DRIVER_LICENSE.value,
            cls.US_ITIN.value,
            cls.US_BANK_ACCOUNT.value,
            cls.US_ABA_ROUTING.value,
            cls.MEDICAL_LICENSE.value,
        ]
    
    @classmethod
    def get_indian_recognizers(cls) -> list[str]:
        """Returns all India-specific recognizers."""
        return [
            cls.IN_PAN.value,
            cls.IN_AADHAAR.value,
            cls.IN_VEHICLE_REGISTRATION.value,
            cls.IN_PASSPORT.value,
            cls.IN_VOTER_ID.value,
        ]
    
    @classmethod
    def get_financial_recognizers(cls) -> list[str]:
        """Returns all financial recognizers."""
        return [
            cls.CREDIT_CARD.value,
            cls.IBAN.value,
            cls.US_BANK_ACCOUNT.value,
            cls.CRYPTO.value,
        ]
    
    @classmethod
    def get_contact_recognizers(cls) -> list[str]:
        """Returns all contact-related recognizers."""
        return [
            cls.EMAIL.value,
            cls.PHONE.value,
            cls.IP_ADDRESS.value,
            cls.URL.value,
        ]
    
    @classmethod
    def get_all_recognizers(cls) -> list[str]:
        """Returns a list of all recognizer values."""
        return [recognizer.value for recognizer in cls]

    @classmethod
    def get_uk_recognizers(cls) -> list[str]:
        """Returns all UK-specific recognizers."""
        return [
            cls.UK_NHS.value,
            cls.UK_NINO.value,
        ]
    
    @classmethod
    def get_australian_recognizers(cls) -> list[str]:
        """Returns all Australia-specific recognizers."""
        return [
            cls.AU_ABN.value,
            cls.AU_ACN.value,
            cls.AU_TFN.value,
            cls.AU_MEDICARE.value,
        ]
    
    @classmethod
    def get_singapore_recognizers(cls) -> list[str]:
        """Returns all Singapore-specific recognizers."""
        return [
            cls.SG_FIN.value,
            cls.SG_UEN.value,
        ]
    
    @classmethod
    def get_european_recognizers(cls) -> list[str]:
        """Returns all European recognizers."""
        return [
            cls.ES_NIF.value,
            cls.ES_NIE.value,
            cls.IT_DRIVER_LICENSE.value,
            cls.IT_FISCAL_CODE.value,
            cls.IT_IDENTITY_CARD.value,
            cls.IT_PASSPORT.value,
            cls.IT_VAT_CODE.value,
            cls.PL_PESEL.value,
            cls.FI_PERSONAL_IDENTITY_CODE.value,
            cls.IBAN.value,
        ]
    
    @classmethod
    def get_standard_recognizers(cls) -> list[str]:
        """Returns standard recognizers (financial + contact + date)."""
        return [
            cls.CREDIT_CARD.value,
            cls.IBAN.value,
            cls.CRYPTO.value,
            cls.EMAIL.value,
            cls.PHONE.value,
            cls.IP_ADDRESS.value,
            cls.URL.value,
            cls.DATE_TIME.value,
        ]
    
    @classmethod
    def get_from_preset(cls, preset: str) -> list[str]:
        """
        Returns a list of recognizers from a preset.
        
        Args:
            preset: Name of the preset (case-insensitive)
            
        Returns:
            List of recognizer class names
            
        Raises:
            ValueError: If preset is not found
        """
        preset = preset.upper()
        
        presets = {
            "INDIAN": cls.get_indian_recognizers,
            "INDIA": cls.get_indian_recognizers,
            "US": cls.get_us_recognizers,
            "USA": cls.get_us_recognizers,
            "UK": cls.get_uk_recognizers,
            "AUSTRALIA": cls.get_australian_recognizers,
            "AU": cls.get_australian_recognizers,
            "SINGAPORE": cls.get_singapore_recognizers,
            "SG": cls.get_singapore_recognizers,
            "EUROPEAN": cls.get_european_recognizers,
            "EUROPE": cls.get_european_recognizers,
            "EU": cls.get_european_recognizers,
            "FINANCIAL": cls.get_financial_recognizers,
            "CONTACT": cls.get_contact_recognizers,
            "STANDARD": cls.get_standard_recognizers,
            "COMPREHENSIVE": cls.get_all_recognizers,
            "ALL": cls.get_all_recognizers,
        }
        
        if preset in presets:
            return presets[preset]()
        else:
            raise ValueError(
                f"Invalid preset '{preset}'. "
                f"Available presets: {', '.join(sorted(presets.keys()))}"
            )

    @classmethod
    def get_recognizer_instance(cls, recognizer_name: str) -> EntityRecognizer:
        """
        Factory method to create a recognizer instance by name.
        
        Args:
            recognizer_name: Name of the recognizer class
            
        Returns:
            Instance of the recognizer
            
        Raises:
            ValueError: If recognizer is not found
        """
        from presidio_analyzer.recognizer_registry import RecognizerRegistry
        
        # Create a temporary registry to get the recognizer
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()
        
        # Find the recognizer by class name
        all_recognizers = registry.get_recognizers()
        for recognizer in all_recognizers:
            if recognizer.__class__.__name__ == recognizer_name:
                return recognizer
        
        raise ValueError(
            f"Recognizer '{recognizer_name}' not found in Presidio registry. "
            f"Available recognizers: {', '.join(sorted(set([r.__class__.__name__ for r in all_recognizers])))}"
        )
    
    @classmethod
    def validate_recognizer_names(cls, recognizer_names: list[str]) -> tuple[list[str], list[str]]:
        """
        Validate a list of recognizer names.
        
        Args:
            recognizer_names: List of recognizer class names to validate
            
        Returns:
            Tuple of (valid_names, invalid_names)
        """
        all_recognizers = cls.get_all_recognizers()
        valid = []
        invalid = []
        
        for name in recognizer_names:
            if name in all_recognizers:
                valid.append(name)
            else:
                invalid.append(name)
        
        return valid, invalid

    @classmethod
    def get_recognizer(cls, recognizer_name: str) -> EntityRecognizer:
        """
        Returns a recognizer instance by name.
        """
        match (recognizer_name):
            case cls.AU_ABN._value_:
                return AuAbnRecognizer()
            case cls.AU_ACN._value_:
                return AuAcnRecognizer()
            case cls.AU_MEDICARE._value_:
                return AuMedicareRecognizer()
            case cls.AU_TFN._value_:
                return AuTfnRecognizer()
            case cls.CREDIT_CARD._value_:
                return CreditCardRecognizer()
            case cls.CRYPTO._value_:
                return CryptoRecognizer()
            case cls.DATE_TIME._value_:
                return DateRecognizer()
            case cls.EMAIL._value_:
                return EmailRecognizer()
            case cls.ES_NIE._value_:
                return EsNieRecognizer()
            case cls.ES_NIF._value_:
                return EsNifRecognizer()
            case cls.FI_PERSONAL_IDENTITY_CODE._value_:
                return FiPersonalIdentityCodeRecognizer()
            case cls.IBAN._value_:
                return IbanRecognizer()
            case cls.IN_AADHAAR._value_:
                return InAadhaarRecognizer()            
            case cls.IN_PAN._value_:
                return InPanRecognizer()
            case cls.IN_PASSPORT._value_:
                return InPassportRecognizer()
            case cls.IN_VEHICLE_REGISTRATION._value_:
                return InVehicleRegistrationRecognizer()
            case cls.IN_VOTER_ID._value_:
                return InVoterRecognizer()
            case cls.IP_ADDRESS._value_:
                return IpRecognizer()
            case cls.IT_DRIVER_LICENSE._value_:
                return ItDriverLicenseRecognizer()
            case cls.IT_FISCAL_CODE._value_:
                return ItFiscalCodeRecognizer()
            case cls.IT_IDENTITY_CARD._value_:
                return ItIdentityCardRecognizer()
            case cls.IT_PASSPORT._value_:
                return ItPassportRecognizer()
            case cls.IT_VAT_CODE._value_:
                return ItVatCodeRecognizer()
            case cls.KR_RRN._value_:
                return KrRrnRecognizer()
            case cls.MEDICAL_LICENSE._value_:
                return MedicalLicenseRecognizer()
            case cls.PHONE._value_:
                return PhoneRecognizer()
            case cls.PL_PESEL._value_:
                return PlPeselRecognizer()
            case cls.SG_FIN._value_:
                return SgFinRecognizer()
            case cls.SG_UEN._value_:
                return SgUenRecognizer()                
            case cls.UK_NHS._value_:
                return NhsRecognizer()
            case cls.UK_NINO._value_:
                return UkNinoRecognizer()
            case cls.URL._value_:
                return UrlRecognizer()
            case cls.US_ABA_ROUTING._value_:
                return AbaRoutingRecognizer()
            case cls.US_BANK_ACCOUNT._value_:
                return UsBankRecognizer()
            case cls.US_DRIVER_LICENSE._value_:
                return UsLicenseRecognizer()
            case cls.US_ITIN._value_:
                return UsItinRecognizer()
            case cls.US_PASSPORT._value_:
                return UsPassportRecognizer()
            case cls.US_SSN._value_:
                return UsSsnRecognizer()
            case cls.US_DRIVER_LICENSE._value_:
                return UsLicenseRecognizer()
            case cls.US_ITIN._value_:
                return UsItinRecognizer()
            case cls.US_PASSPORT._value_:
                return UsPassportRecognizer()
            case cls.US_SSN._value_:
                return UsSsnRecognizer()
            case cls.SPACY._value_:
                return SpacyRecognizer()
            case cls.TRANSFORMERS._value_:
                return TransformersRecognizer()
            case cls.STANZA._value_:
                return StanzaRecognizer()
            case cls.GLINER._value_:
                return GLiNERRecognizer()
            case cls.AZURE_AI_LANGUAGE._value_:
                return AzureAILanguageRecognizer()
            case cls.AZURE_HEALTH_DEID._value_:
                return AzureHealthDeidRecognizer()
            case _:
                raise ValueError(f"Recognizer '{recognizer_name}' not found---")

def preload_presidio():
    # Parse and get recognizers
    recognizers = parse_recognizers(DEFAULT_RECOGNIZERS)
    
    # Create analyzer with specified recognizers
    analyzer = get_analyzer(recognizers, DEFAULT_LANGUAGE)
            
    test_text = "My name is John Smith, my SSN is 123-45-6789 and email is john@example.com. My phone is +1 415-555-0199."
    results = analyzer.analyze(text=test_text, language=DEFAULT_LANGUAGE)
    logger.info(f"Preloaded Presidio recognizers. ")


if __name__ == "__main__":
    preload_presidio()