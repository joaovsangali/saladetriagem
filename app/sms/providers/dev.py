"""Development SMS provider — logs message to console instead of sending."""

import logging
from app.sms import SMSProvider

logger = logging.getLogger(__name__)


class DevSMSProvider(SMSProvider):
    """Fake SMS provider for development. Logs the message to the console."""

    def send(self, to: str, message: str) -> bool:
        logger.info("[DEV SMS] To: %s | Message: %s", to, message)
        print(f"[DEV SMS] To: {to} | Message: {message}", flush=True)
        return True
