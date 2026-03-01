import re
from typing import Dict, Any, Optional

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _format_date_br(value: str) -> str:
    """Convert ISO date 'yyyy-mm-dd' to 'dd/mm/yyyy'. Passthrough if not ISO."""
    if value and _ISO_DATE_RE.match(value):
        parts = value.split("-")
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return value


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
        lines.append("")
        
        if submission.address:
            lines.append(f"ENDEREÇO: {submission.address}")
            lines.append("")
        
        if submission.answers:
            lines.append("DOS FATOS:")
            for key, val in submission.answers.items():
                if val is not None and val != "":
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
            if val is None or val == "":
                continue
            if isinstance(val, bool):
                val = "Sim" if val else "Não"
            else:
                val = _format_date_br(str(val))
            result.append((label, str(val)))
        return result
