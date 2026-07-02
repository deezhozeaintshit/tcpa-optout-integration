import re
from typing import Optional

def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone numbers to E.164 format."""
    if not phone:
        return None
    # Remove all non-digit and non-plus characters
    cleaned = re.sub(r"[^\d+]", "", phone)
    if not cleaned:
        return None
    
    # If already starts with '+', keep it
    if cleaned.startswith("+"):
        if 11 <= len(cleaned) <= 16:
            return cleaned
        return cleaned
    
    # If 10 digits (US/Canada local format), prepend +1
    if len(cleaned) == 10:
        return f"+1{cleaned}"
    
    # If 11 digits and starts with 1, prepend +
    if len(cleaned) == 11 and cleaned.startswith("1"):
        return f"+{cleaned}"
    
    # Default fallback
    return f"+{cleaned}"

def normalize_email(email: str) -> Optional[str]:
    """Normalize email addresses to standard lowercase, stripped."""
    if not email:
        return None
    return email.strip().lower()
