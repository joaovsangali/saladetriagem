"""Logging filter that masks sensitive personal data before writing to logs."""
import logging
import re


class SanitizingFilter(logging.Filter):
    """Mask RG, CPF, e-mail and other PII in log records."""

    # RG: 7–9 digits — capture prefix/suffix to replace middle with ****
    RG_PATTERN = re.compile(r"\b(\d{2})(\d{3,7})(\d{2})\b")
    # CPF: exactly 11 digits (with or without separators)
    CPF_PATTERN = re.compile(r"\b(\d{3})[.\-]?\d{3}[.\-]?\d{3}[.\-]?(\d{2})\b")
    # E-mail
    EMAIL_PATTERN = re.compile(
        r"\b([A-Za-z0-9._%+\-]{1,2})[A-Za-z0-9._%+\-]*(@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})\b"
    )
    # Street address keywords (Portuguese)
    ADDRESS_PATTERN = re.compile(
        r"(Rua|Av\.|Avenida|Travessa|Alameda|Praça|Estrada)[^\n,;]{5,80}",
        re.IGNORECASE,
    )

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._sanitize(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._sanitize(str(v)) for k, v in record.args.items()
                }
            else:
                record.args = tuple(self._sanitize(str(a)) for a in record.args)
        return True

    def _sanitize(self, text: str) -> str:
        text = self.CPF_PATTERN.sub(r"\1****\2", text)
        text = self.RG_PATTERN.sub(r"\1****\3", text)
        text = self.EMAIL_PATTERN.sub(r"\1***\2", text)
        text = self.ADDRESS_PATTERN.sub("[ENDEREÇO REMOVIDO]", text)
        return text
