import re
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, Form, Response, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import verify_twilio_request, verify_api_key
from app.schemas.optout import OptOutCreate
from app.services.optout_service import optout_service
from app.services.extraction import extraction_service
from app.core.normalizer import normalize_phone, normalize_email

logger = logging.getLogger("optout_api")
router = APIRouter()

def resolve_path(data: Any, path: str) -> Any:
    """Helper to resolve nested dictionary values using dot-separated paths."""
    if not path or not data:
        return None
    keys = path.split(".")
    curr = data
    for k in keys:
        if isinstance(curr, dict) and k in curr:
            curr = curr[k]
        else:
            return None
    return curr

@router.post("/twilio")
async def ingest_twilio_sms(
    request: Request,
    From: Optional[str] = Form(None, description="Sender phone number"),
    To: Optional[str] = Form(None, description="Twilio phone number"),
    Body: Optional[str] = Form(None, description="SMS body content"),
    MessageSid: Optional[str] = Form(None, description="Message SID identifier"),
    SmsSid: Optional[str] = Form(None, description="Fallback message SID identifier"),
    db: AsyncSession = Depends(get_db),
    _ = Depends(verify_twilio_request)
):
    """Inbound webhook handler for Twilio SMS. Decodes phone numbers and evaluates intent via AI."""
    message_sid = MessageSid or SmsSid or "unknown_sid"
    
    # If no Body is sent (e.g. standard delivery status callback), log and acknowledge immediately
    if not Body:
        logger.info(f"Received Twilio message status callback or empty message: Sid={message_sid}, From={From}")
        return Response(content="<Response></Response>", media_type="application/xml")
        
    # Evaluate body text using structured AI Intent Classification & Extraction Pipeline
    extraction = await extraction_service.extract_intent(Body)
    
    if not extraction.is_opt_out:
        logger.info(f"Ignored non-optout Twilio message from {From}: '{Body}' (Confidence: {extraction.confidence_score})")
        return Response(content="<Response></Response>", media_type="application/xml")
        
    # Normalize phone target (fallback to From if extraction didn't find one)
    phone_target = extraction.extracted_target if (extraction.is_opt_out and extraction.target_type == "phone" and extraction.extracted_target) else From
    normalized_phone = normalize_phone(phone_target)
    
    if not normalized_phone:
        logger.warning(f"Could not normalize From number: {phone_target}")
        normalized_phone = From
        
    optout_data = OptOutCreate(
        identifier=normalized_phone,
        channel="sms",
        reason=Body.strip()[:255] if Body else "Twilio SMS",
        ip_address=request.client.host if request.client else None,
        raw_payload={
            "From": From,
            "To": To,
            "Body": Body,
            "MessageSid": message_sid,
            "ai_classification": {
                "is_opt_out": extraction.is_opt_out,
                "confidence_score": extraction.confidence_score,
                "extracted_target": extraction.extracted_target,
                "target_type": extraction.target_type
            }
        }
    )
    
    await optout_service.create_optout(db, optout_data)
    
    confirm_twiml = (
        "<Response>"
        "<Message>You have been successfully opted out. You will receive no further messages.</Message>"
        "</Response>"
    )
    return Response(content=confirm_twiml, media_type="application/xml")

@router.post("/email")
@router.post("/sendgrid")
async def ingest_email(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Inbound webhook handler for SendGrid Inbound Parse or IMAP. Validates opt-out intentions via AI."""
    content_type = request.headers.get("content-type", "")
    
    from_header = ""
    subject = ""
    text_content = ""
    timestamp = ""
    to_header = ""
    
    if "application/json" in content_type:
        # JSON Payload (typically IMAP script integrations)
        payload = await request.json()
        from_header = payload.get("from") or payload.get("sender") or ""
        to_header = payload.get("to") or ""
        subject = payload.get("subject") or ""
        text_content = payload.get("text") or payload.get("body") or payload.get("html") or ""
        timestamp = payload.get("timestamp") or payload.get("date") or ""
    else:
        # Form Data / Multipart (typically SendGrid Inbound Parse)
        form = await request.form()
        from_header = form.get("from") or form.get("sender") or ""
        to_header = form.get("to") or ""
        subject = form.get("subject") or ""
        text_content = form.get("text") or form.get("body") or ""
        timestamp = form.get("timestamp") or ""
        
    # Extract email address out of "Name <email@domain.com>" using regex
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", from_header)
    sender_email = email_match.group(0) if email_match else from_header
    sender_email = sender_email.strip()
    
    # Route email details to the AI pipeline
    text_to_evaluate = f"Subject: {subject}\nBody: {text_content}"
    extraction = await extraction_service.extract_intent(text_to_evaluate)
    
    if not extraction.is_opt_out:
        logger.info(f"Skipping neutral email from {sender_email}: '{subject}' (Confidence: {extraction.confidence_score})")
        return {"status": "skipped", "reason": "No opt-out request detected"}
        
    normalized_email = normalize_email(sender_email) or sender_email
    
    optout_data = OptOutCreate(
        identifier=normalized_email,
        channel="email",
        reason=subject.strip()[:255] if subject else "Email Unsubscribe Request",
        ip_address=request.client.host if request.client else None,
        raw_payload={
            "from": from_header,
            "to": to_header,
            "subject": subject,
            "text_snippet": text_content[:500],
            "timestamp": timestamp,
            "ai_classification": {
                "is_opt_out": extraction.is_opt_out,
                "confidence_score": extraction.confidence_score,
                "extracted_target": extraction.extracted_target,
                "target_type": extraction.target_type
            }
        }
    )
    
    obj = await optout_service.create_optout(db, optout_data)
    return {"status": "processed", "identifier": obj.identifier}

@router.post("/generic", dependencies=[Depends(verify_api_key)])
async def ingest_generic(
    request: Request,
    phone_key: Optional[str] = Query("phone", description="Path/key to extract phone number"),
    email_key: Optional[str] = Query("email", description="Path/key to extract email address"),
    text_key: Optional[str] = Query("text", description="Path/key to extract text message body to evaluate"),
    db: AsyncSession = Depends(get_db)
):
    """Secure custom REST webhook for generic JSON integrations, verified by API Key and supporting dynamic path resolution."""
    payload_dict = await request.json()
    
    # Resolve fields using path lookup
    extracted_phone = resolve_path(payload_dict, phone_key)
    extracted_email = resolve_path(payload_dict, email_key)
    extracted_text = resolve_path(payload_dict, text_key)
    
    # Backward compatibility for old direct identifier format
    if not extracted_phone and not extracted_email and "identifier" in payload_dict:
        val = str(payload_dict["identifier"])
        if "@" in val:
            extracted_email = val
        else:
            extracted_phone = val
            
    # Check if this is a direct/pre-verified opt-out (has target but no text to evaluate)
    has_explicit_target = bool(extracted_phone or extracted_email)
    has_text_to_evaluate = bool(extracted_text) or any(k in payload_dict for k in ["text", "body", "message", "content", "msg"])
    
    if has_explicit_target and not has_text_to_evaluate:
        # Pre-verified / direct optout request, skip AI pipeline
        is_opt_out = True
        confidence = 1.0
        extracted_target = extracted_email or extracted_phone
        target_type = "email" if extracted_email else "phone"
    else:
        # Resolve text to evaluate
        if not extracted_text:
            for possible_key in ["text", "body", "message", "content", "msg"]:
                if possible_key in payload_dict:
                    extracted_text = payload_dict[possible_key]
                    break
        evaluation_text = str(extracted_text) if extracted_text else str(payload_dict)
        extraction = await extraction_service.extract_intent(evaluation_text)
        is_opt_out = extraction.is_opt_out
        confidence = extraction.confidence_score
        extracted_target = extraction.extracted_target
        target_type = extraction.target_type

    if not is_opt_out:
        logger.info(f"Skipping generic webhook request; no opt-out intent detected. (Confidence: {confidence})")
        return {"status": "skipped", "reason": "No opt-out request detected"}
        
    # Determine final identifier, prioritize explicit parameters
    final_identifier = None
    if extracted_email:
        final_identifier = normalize_email(str(extracted_email))
    elif extracted_phone:
        final_identifier = normalize_phone(str(extracted_phone))
    elif extracted_target:
        if target_type == "email":
            final_identifier = normalize_email(extracted_target)
        else:
            final_identifier = normalize_phone(extracted_target)
            
    if not final_identifier:
        final_identifier = extracted_target
        
    if not final_identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract a valid phone number or email address from the payload."
        )
        
    optout_data = OptOutCreate(
        identifier=final_identifier,
        channel=payload_dict.get("channel") or "api",
        reason=payload_dict.get("reason") or (str(extracted_text)[:255] if extracted_text else "Generic API Webhook"),
        ip_address=request.client.host if request.client else None,
        raw_payload={
            "original_payload": payload_dict,
            "mapping": {
                "phone_key": phone_key,
                "email_key": email_key,
                "text_key": text_key
            },
            "ai_classification": {
                "is_opt_out": is_opt_out,
                "confidence_score": confidence,
                "extracted_target": extracted_target,
                "target_type": target_type
            }
        }
    )
    
    obj = await optout_service.create_optout(db, optout_data)
    return {
        "status": "processed",
        "id": obj.id,
        "identifier": obj.identifier,
        "channel": obj.channel
    }
