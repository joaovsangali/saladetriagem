"""SMS provider abstraction for Sala de Triagem."""

import abc
import logging

logger = logging.getLogger(__name__)


class SMSProvider(abc.ABC):
    """Abstract base class for SMS providers."""

    @abc.abstractmethod
    def send(self, to: str, message: str) -> bool:
        """Send an SMS message. Returns True on success, False on failure."""


def get_sms_provider(app=None) -> SMSProvider:
    """Return the configured SMS provider based on app config."""
    from flask import current_app as _app
    cfg = app or _app
    provider_name = cfg.config.get('SMS_PROVIDER', 'dev')

    if provider_name == 'twilio':
        from app.sms.providers.twilio import TwilioSMSProvider
        return TwilioSMSProvider(
            account_sid=cfg.config.get('TWILIO_ACCOUNT_SID', ''),
            auth_token=cfg.config.get('TWILIO_AUTH_TOKEN', ''),
            from_number=cfg.config.get('TWILIO_FROM_NUMBER', ''),
        )

    from app.sms.providers.dev import DevSMSProvider
    return DevSMSProvider()
