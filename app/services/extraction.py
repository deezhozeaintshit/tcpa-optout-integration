import logging
import re
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.normalizer import normalize_phone, normalize_email

logger = logging.getLogger("optout_extraction")

class OptOutExtraction(BaseModel):
    is_opt_out: bool = Field(..., description="Whether the text indicates an opt-out, DNC (Do Not Call), or unsubscribe intent.")
    confidence_score: float = Field(..., description="Confidence score between 0.0 and 1.0.")
    extracted_target: str = Field(..., description="The phone number in E.164 format or valid email string if found in the text, else empty string.")
    target_type: str = Field(..., description="Type of target, either 'phone' or 'email'.")

class ExtractionService:
    """Uses structured local or remote Gemini API to evaluate text against TCPA revocation intent."""

    def __init__(self):
        self._initialized = False
        self._genai = None

    def _initialize_sdk(self):
        if self._initialized:
            return
        
        api_key = settings.GEMINI_API_KEY
        if api_key and api_key != "mock" and api_key != "default_gemini_key_change_me":
            try:
                import google.generativeai as genai
                from google.api_core import client_options
                
                # Configure API key
                kwargs = {"api_key": api_key}
                if settings.GEMINI_API_BASE_URL:
                    kwargs["client_options"] = client_options.ClientOptions(
                        api_endpoint=settings.GEMINI_API_BASE_URL
                    )
                genai.configure(**kwargs)
                self._genai = genai
                self._initialized = True
                logger.info(f"Gemini SDK successfully initialized with model {settings.GEMINI_MODEL}")
            except ImportError:
                logger.error("google-generativeai package is not installed. Falling back to rule-based parser.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini SDK: {e}. Falling back to rule-based parser.")

    async def extract_intent(self, text: str) -> OptOutExtraction:
        """Route message text through structured LLM extraction helper or offline fallback."""
        if not text:
            return OptOutExtraction(is_opt_out=False, confidence_score=0.0, extracted_target="", target_type="phone")
            
        self._initialize_sdk()
        
        if self._initialized and self._genai:
            try:
                # Call Gemini Generative Model with Structured Output JSON schema
                model = self._genai.GenerativeModel(settings.GEMINI_MODEL)
                prompt = (
                    "You are a TCPA/FCC compliance auditor. Analyze the following inbound text message, email body, "
                    "or voice transcript for opt-out, unsubscribe, or consent revocation intent (e.g. STOP, unsubscribe, "
                    "remove me, don't call, take me off list, etc.).\n"
                    "Extract the target (phone number or email) if mentioned in the text. If not mentioned, you can leave it empty.\n\n"
                    f"Text content:\n\"\"\"\n{text}\n\"\"\""
                )
                
                response = model.generate_content(
                    prompt,
                    generation_config=self._genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=OptOutExtraction
                    )
                )
                
                # Response is guaranteed to follow the schema structure
                result_json = response.text
                parsed = OptOutExtraction.model_validate_json(result_json)
                
                # Post-process and normalize targets if extracted
                if parsed.extracted_target:
                    if parsed.target_type == "email" or "@" in parsed.extracted_target:
                        parsed.extracted_target = normalize_email(parsed.extracted_target) or parsed.extracted_target
                        parsed.target_type = "email"
                    else:
                        parsed.extracted_target = normalize_phone(parsed.extracted_target) or parsed.extracted_target
                        parsed.target_type = "phone"
                        
                logger.info(f"AI intent extraction result: is_opt_out={parsed.is_opt_out}, confidence={parsed.confidence_score}")
                return parsed
            except Exception as e:
                logger.error(f"Gemini API execution failed: {e}. Executing rule-based fallback parser.")
                
        return self._rule_based_fallback(text)

    def _rule_based_fallback(self, text: str) -> OptOutExtraction:
        """Deterministic keyword parser when Gemini API is unconfigured or offline."""
        text_lower = text.lower().strip()
        
        # Keyword triggers matching the spec requirements
        keywords = [
            "stop", "unsubscribe", "remove", "don't call", "dont call",
            "take me off", "take off", "off list", "cancel", "quit", "end",
            "opt out", "opt-out"
        ]
        
        is_opt_out = any(kw in text_lower for kw in keywords) or \
                     ("take" in text_lower and "off" in text_lower) or \
                     "off your list" in text_lower or \
                     "off the list" in text_lower
        confidence_score = 0.95 if is_opt_out else 0.0
        
        # Regex search for targets
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        phone_match = re.search(r"\+?[1-9]\d{1,14}(?:x\d+)?|\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        
        extracted_target = ""
        target_type = "phone"
        
        if email_match:
            extracted_target = normalize_email(email_match.group(0)) or ""
            target_type = "email"
        elif phone_match:
            extracted_target = normalize_phone(phone_match.group(0)) or ""
            target_type = "phone"
            
        return OptOutExtraction(
            is_opt_out=is_opt_out,
            confidence_score=confidence_score,
            extracted_target=extracted_target,
            target_type=target_type
        )

extraction_service = ExtractionService()
