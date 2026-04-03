"""
SMS alert endpoint — sends emergency notifications via Twilio.
Falls back to logging when Twilio credentials are not configured.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sms", tags=["sms"])


class SMSAlertRequest(BaseModel):
    groups: list[str]
    message: str
    camera_name: str
    criticality: str
    lat: float | None = None
    lon: float | None = None


class SMSAlertResponse(BaseModel):
    sent: int
    detail: str


RECIPIENT_DIRECTORY: dict[str, list[str]] = {
    "firefighters": [],
    "control_center": [],
    "area_residents": [],
}


def _load_recipients() -> None:
    """Populate recipient directory from env vars (comma-separated phone numbers)."""
    import os

    for key in RECIPIENT_DIRECTORY:
        env_key = f"SMS_RECIPIENTS_{key.upper()}"
        raw = os.getenv(env_key, "")
        if raw.strip():
            RECIPIENT_DIRECTORY[key] = [n.strip() for n in raw.split(",") if n.strip()]


def _send_twilio(phones: list[str], body: str) -> int:
    """Send SMS via Twilio. Returns count of messages queued."""
    from twilio.rest import Client  # type: ignore[import-untyped]

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    sent = 0
    for phone in phones:
        try:
            client.messages.create(
                body=body,
                from_=settings.twilio_from_number,
                to=phone,
            )
            sent += 1
        except Exception as exc:
            logger.error("Twilio send failed for %s: %s", phone, exc)
    return sent


@router.post("/send", response_model=SMSAlertResponse)
async def send_sms_alert(req: SMSAlertRequest):
    _load_recipients()

    all_phones: list[str] = []
    for group in req.groups:
        phones = RECIPIENT_DIRECTORY.get(group, [])
        all_phones.extend(phones)

    all_phones = list(dict.fromkeys(all_phones))

    location = ""
    if req.lat is not None and req.lon is not None:
        location = f" Location: {req.lat:.4f}°N, {req.lon:.4f}°W."

    body = (
        f"[BayHawk ALERT — {req.criticality}] "
        f"{req.message}{location} "
        f"Camera: {req.camera_name}. "
        f"Reply STOP to unsubscribe."
    )

    has_twilio = (
        getattr(settings, "twilio_account_sid", "")
        and getattr(settings, "twilio_auth_token", "")
        and getattr(settings, "twilio_from_number", "")
    )

    if has_twilio and all_phones:
        try:
            sent = _send_twilio(all_phones, body)
            return SMSAlertResponse(
                sent=sent,
                detail=f"Sent {sent}/{len(all_phones)} SMS via Twilio.",
            )
        except Exception as exc:
            logger.exception("Twilio batch send failed")
            raise HTTPException(status_code=502, detail=str(exc))

    logger.info(
        "SMS alert (demo mode — no Twilio or no recipients configured):\n"
        "  Groups: %s\n  Phones: %s\n  Body: %s",
        req.groups,
        all_phones or "(none configured)",
        body,
    )
    return SMSAlertResponse(
        sent=0,
        detail=(
            f"Demo mode: alert logged for {len(req.groups)} group(s). "
            "Configure TWILIO_* env vars and SMS_RECIPIENTS_* to enable real SMS."
        ),
    )
