# app/utils/validators.py
"""Utility validators and normalizers for input data."""

import re


def normalize_phone(phone: str) -> str:
    """Remove all non-numeric characters from a phone number."""
    if not phone:
        return ""
    return re.sub(r'\D', '', phone)


def normalize_cpf(cpf: str) -> str:
    """Remove all non-numeric characters from a CPF string."""
    if not cpf:
        return ""
    return re.sub(r'\D', '', cpf)


def validate_time_format(time_str: str):
    """Validate and return a time string in HH:MM format, or None if invalid."""
    if not time_str:
        return None
    if re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time_str.strip()):
        return time_str.strip()
    return None
