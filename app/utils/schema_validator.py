"""Validation helpers for custom intake schemas."""

import re

ALLOWED_FIELD_TYPES = {"text", "email", "textarea", "select", "number", "date"}


def validate_custom_intake_schema(schema):
    """Validate custom intake schema structure and content.

    Returns (valid: bool, error_message: str | None).
    """
    if not isinstance(schema, dict):
        return False, "Schema deve ser um objeto JSON"

    if "fields" not in schema or not isinstance(schema["fields"], list):
        return False, "Schema deve conter array 'fields'"

    if len(schema["fields"]) < 2:
        return False, "Mínimo de 2 campos (nome e email)"

    for field in schema["fields"]:
        if not isinstance(field, dict):
            return False, "Cada campo deve ser um objeto"

        if "id" not in field or "label" not in field or "type" not in field:
            return False, "Campos devem ter id, label e type"

        if field["type"] not in ALLOWED_FIELD_TYPES:
            return False, f"Tipo '{field['type']}' não permitido"

        if re.search(r'<[^>]{0,200}>', str(field["label"])):
            return False, "Labels não podem conter HTML"

        if field["type"] == "select":
            options = field.get("options", [])
            if not isinstance(options, list) or len(options) < 1:
                return False, f"Campo select '{field['id']}' deve ter ao menos uma opção"

    return True, None
