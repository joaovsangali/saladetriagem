"""Validation helpers for custom intake schemas."""

import re

# v1 (legacy) field types — kept for backward compatibility
_V1_FIELD_TYPES = {"text", "email", "textarea", "select", "number", "date"}

# v2 extended field types
_V2_FIELD_TYPES = {
    "text", "email", "textarea", "number", "date",
    "select", "radio", "checkbox",
    "scale",
    "section_header",
    "image_display",
}

ALLOWED_FIELD_TYPES = _V2_FIELD_TYPES

# Types that carry options (list of choices)
_OPTIONS_REQUIRED_TYPES = {"select", "radio", "checkbox"}

# Types that do not carry user-submittable data (structural / display only)
_DISPLAY_ONLY_TYPES = {"section_header", "image_display"}


def _has_html(text: str) -> bool:
    return bool(re.search(r'<[^>]{0,200}>', text))


def validate_custom_intake_schema(schema):
    """Validate custom intake schema structure and content.

    Supports both v1 schemas (text/email/textarea/select/number/date) and
    v2 schemas that add radio, checkbox, scale, section_header, image_display.

    Returns (valid: bool, error_message: str | None).
    """
    if not isinstance(schema, dict):
        return False, "Schema deve ser um objeto JSON"

    if "fields" not in schema or not isinstance(schema["fields"], list):
        return False, "Schema deve conter array 'fields'"

    # Count only non-structural fields for the minimum-2 requirement
    submittable = [
        f for f in schema["fields"]
        if isinstance(f, dict) and f.get("type") not in _DISPLAY_ONLY_TYPES
    ]
    if len(submittable) < 2:
        return False, "Mínimo de 2 campos (nome e email)"

    seen_ids: set = set()

    for field in schema["fields"]:
        if not isinstance(field, dict):
            return False, "Cada campo deve ser um objeto"

        if "id" not in field or "label" not in field or "type" not in field:
            return False, "Campos devem ter id, label e type"

        ftype = field["type"]
        if ftype not in ALLOWED_FIELD_TYPES:
            return False, f"Tipo '{ftype}' não permitido"

        if _has_html(str(field["label"])):
            return False, "Labels não podem conter HTML"

        # Unique IDs
        fid = field["id"]
        if fid in seen_ids:
            return False, f"ID de campo duplicado: '{fid}'"
        seen_ids.add(fid)

        # Fields that require options
        if ftype in _OPTIONS_REQUIRED_TYPES:
            options = field.get("options", [])
            if not isinstance(options, list) or len(options) < 1:
                return False, f"Campo '{ftype}' '{fid}' deve ter ao menos uma opção"
            for opt in options:
                # Options can be plain strings or dicts with {label, value[, image_url]}
                if isinstance(opt, dict):
                    if "label" not in opt:
                        return False, f"Opção de '{fid}' deve ter chave 'label'"
                    if _has_html(str(opt["label"])):
                        return False, "Labels de opções não podem conter HTML"
                elif isinstance(opt, str):
                    if _has_html(opt):
                        return False, "Labels de opções não podem conter HTML"
                else:
                    return False, f"Opções de '{fid}' devem ser strings ou objetos"

        # Scale field: optional min/max/step, must be numbers if present
        if ftype == "scale":
            for key in ("min", "max", "step"):
                val = field.get(key)
                if val is not None and not isinstance(val, (int, float)):
                    return False, f"Campo scale '{fid}': '{key}' deve ser numérico"

        # Conditional logic validation
        condition = field.get("condition")
        if condition is not None:
            if not isinstance(condition, dict):
                return False, f"Campo '{fid}': 'condition' deve ser um objeto"
            if "field_id" not in condition or "value" not in condition:
                return False, f"Campo '{fid}': 'condition' deve ter 'field_id' e 'value'"

    return True, None
