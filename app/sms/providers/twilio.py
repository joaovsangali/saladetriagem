"""Twilio SMS provider integration."""

import logging
from app.sms import SMSProvider

logger = logging.getLogger(__name__)


class TwilioSMSProvider(SMSProvider):
    """Sends SMS via Twilio REST API."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send(self, to: str, message: str) -> bool:
        try:
            from twilio.rest import Client  # type: ignore[import]
            client = Client(self.account_sid, self.auth_token)
            client.messages.create(body=message, from_=self.from_number, to=to)
            logger.info("SMS sent via Twilio to %s", to)
            return True
        except ImportError:
            logger.error("twilio package not installed. Run: pip install twilio")
            return False
        except Exception as exc:
            logger.error("Twilio SMS send failed to %s: %s", to, exc)
            return False
