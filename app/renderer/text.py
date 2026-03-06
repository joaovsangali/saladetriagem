import re

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _format_date_br(value: str) -> str:
    """Convert ISO date 'yyyy-mm-dd' to 'dd/mm/yyyy'. Passthrough if not ISO."""
    if value and _ISO_DATE_RE.match(value):
        parts = value.split("-")
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return value


def _pretty_field_name(field_id: str) -> str:
    mapping = {
        "nome": "Nome",
        "rg": "RG",
        "cpf": "CPF",
        "contato": "Contato",
        "endereco": "Endereço",
        "telefone": "Telefone",
    }
    return mapping.get(field_id, field_id.replace("_", " ").capitalize())


def _format_group_items_for_text(items: list) -> list:
    """
    Formata lista de dicts para o texto de cópia.
    Ex:
      1) Nome: Jujuba | RG: 123 | Contato: 119...
    """
    lines = []
    for i, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue

        parts = []
        for k, v in item.items():
            if v is None or str(v).strip() == "":
                continue
            parts.append(f"{_pretty_field_name(k)}: {v}")

        if parts:
            lines.append(f"  {i}) " + " | ".join(parts))

    return lines


def _format_group_items_for_structured(items: list) -> str:
    """
    Formata lista de dicts para aparecer bem em 'Respostas' no dashboard.
    """
    lines = []
    for i, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue

        parts = []
        for k, v in item.items():
            if v is None or str(v).strip() == "":
                continue
            parts.append(f"{_pretty_field_name(k)}: {v}")

        if parts:
            lines.append(f"{i}) " + " | ".join(parts))

    return "\n".join(lines)


class TextRenderer:
    CRIME_LABELS = {
        "roubo": "Roubo",
        "furto": "Furto",
        "estelionato": "Estelionato",
        "lesao_corporal": "Lesão Corporal",
        "maria_da_penha": "Violência Doméstica / Lei Maria da Penha",
        "ameaca": "Ameaça",
        "dano": "Dano ao Patrimônio",
        "outros": "Outros",
    }

    @classmethod
    def render(cls, submission) -> str:
        lines = []
        crime_label = cls.CRIME_LABELS.get(submission.crime_type, submission.crime_type)

        lines.append(f"TIPO DE OCORRÊNCIA: {crime_label}")
        lines.append("")
        lines.append("DADOS INFORMADOS:")
        lines.append(f"  Nome: {submission.guest_name or '—'}")
        if submission.dob:
            lines.append(f"  Data de Nascimento: {_format_date_br(submission.dob)}")
        if submission.rg:
            lines.append(f"  RG: {submission.rg}")
        if submission.cpf:
            lines.append(f"  CPF: {submission.cpf}")
        if submission.phone:
            lines.append(f"  Telefone: {submission.phone}")
        lines.append("")

        if submission.address:
            lines.append(f"ENDEREÇO: {submission.address}")
            lines.append("")

        if submission.answers:
            lines.append("DOS FATOS:")
            for key, val in submission.answers.items():
                if val is None or val == "" or val == []:
                    continue

                # grupos repetíveis
                if isinstance(val, list):
                    lines.append(f"  {key}:")
                    lines.extend(_format_group_items_for_text(val))
                    continue

                display_val = _format_date_br(str(val)) if isinstance(val, str) else val
                lines.append(f"  {key}: {display_val}")
            lines.append("")

        if submission.narrative:
            lines.append("A PARTE RELATA QUE:")
            lines.append(f"  {submission.narrative}")
            lines.append("")

        n_photos = len(submission.photos) if submission.photos else 0
        lines.append(f"ANEXOS: {n_photos} foto(s)")

        return "\n".join(lines)

    @classmethod
    def render_structured(cls, submission, questions: list) -> list:
        """Return list of (label, value) tuples for the structured view."""
        result = []
        q_map = {q["id"]: q["label"] for q in questions}

        for qid, label in q_map.items():
            val = submission.answers.get(qid)
            if val is None or val == "" or val == []:
                continue

            # grupos repetíveis
            if isinstance(val, list):
                pretty = _format_group_items_for_structured(val)
                if pretty:
                    result.append((label, pretty))
                continue

            if isinstance(val, bool):
                val = "Sim" if val else "Não"
            else:
                val = _format_date_br(str(val))

            result.append((label, str(val)))

        return result