import re

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def format_date_br(value: str) -> str:
    if value and isinstance(value, str) and _ISO_DATE_RE.match(value):
        y, m, d = value.split("-")
        return f"{d}/{m}/{y}"
    return value


def bool_to_text(value) -> str:
    if value is True:
        return "sim"
    if value is False:
        return "não"
    return ""


def clean(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if isinstance(value, list):
        return value if value else None
    return value


def join_parts(parts, sep=", "):
    return sep.join([p for p in parts if p])


def get_pm_info(submission) -> dict:
    """Return the _pm_info dict if this is a PM submission, else empty dict."""
    return (submission.answers or {}).get("_pm_info") or {}


def format_declarant_id(submission) -> str:
    """Return 'o policial militar [nome], do [batalhão] batalhão e da [companhia] companhia' for PM, else the guest name."""
    pm_info = get_pm_info(submission)
    if pm_info.get("policial_militar"):
        nome = submission.guest_name or "o policial militar"
        companhia = pm_info.get("pm_companhia")
        batalhao = pm_info.get("pm_batalhao")
        ident = f"o policial militar {nome}"
        if companhia and batalhao:
            ident += f", da {companhia} do {batalhao}"
        elif companhia:
            ident += f", da {companhia}"
        elif batalhao:
            ident += f", do {batalhao}"
        return ident
    return submission.guest_name or "a parte declarante"


def format_person_block(submission) -> str:
    parts = []

    pm_info = get_pm_info(submission)
    is_pm = pm_info.get("policial_militar", False)

    if is_pm:
        declarant = format_declarant_id(submission)
        parts.append(f"compareceu {declarant}")
        pm_re = pm_info.get("pm_re")
        if pm_re:
            parts.append(f"RE {pm_re}")
    else:
        if submission.guest_name:
            parts.append(f"compareceu {submission.guest_name}")

    docs = []
    if submission.rg:
        docs.append(f"RG {submission.rg}")
    if submission.cpf:
        docs.append(f"CPF {submission.cpf}")

    if docs:
        parts.append(f"documentos informados: {'; '.join(docs)}")

    if submission.dob:
        parts.append(f"nascido(a) em {format_date_br(submission.dob)}")

    if submission.phone:
        parts.append(f"telefone para contato {submission.phone}")

    if submission.address:
        parts.append(f"residente/endereço informado: {submission.address}")

    if not parts:
        return "Compareceu a parte noticiante."

    result = "Compareceu a parte noticiante, " + "; ".join(parts) + "."

    if is_pm:
        vitimas = pm_info.get("vitimas") or []
        if vitimas:
            vitimas_parts = []
            for v in vitimas:
                vd = []
                if v.get("nome"):
                    vd.append(v["nome"])
                if v.get("data_nascimento"):
                    vd.append(f"nascido(a) em {format_date_br(v['data_nascimento'])}")
                if v.get("rg"):
                    vd.append(f"RG {v['rg']}")
                if v.get("cpf"):
                    vd.append(f"CPF {v['cpf']}")
                if v.get("endereco"):
                    vd.append(f"endereço {v['endereco']}")
                if vd:
                    vitimas_parts.append(", ".join(vd))
            if vitimas_parts:
                result += " Vítimas: " + "; ".join(vitimas_parts) + "."

    return result


def format_group_people(items: list, singular="pessoa", plural="pessoas") -> str:
    if not items:
        return ""

    rendered = []
    for item in items:
        if not isinstance(item, dict):
            continue

        nome = clean(item.get("nome"))
        rg = clean(item.get("rg"))
        contato = clean(item.get("contato"))
        endereco = clean(item.get("endereco"))

        parts = []
        if nome:
            parts.append(nome)
        if rg:
            parts.append(f"RG/documento {rg}")
        if contato:
            parts.append(f"contato {contato}")
        if endereco:
            parts.append(f"endereço {endereco}")

        if parts:
            rendered.append(", ".join(parts))

    if not rendered:
        return ""

    if len(rendered) == 1:
        return f"{singular}: {rendered[0]}"

    return f"{plural}: " + "; ".join(rendered)


def format_group_generic(items: list, field_order=None, field_labels=None) -> str:
    if not items:
        return ""

    field_order = field_order or []
    field_labels = field_labels or {}

    lines = []
    for item in items:
        if not isinstance(item, dict):
            continue

        keys = field_order or list(item.keys())
        parts = []
        for key in keys:
            value = item.get(key)
            value = clean(value)
            if value is None:
                continue

            if isinstance(value, bool):
                value = bool_to_text(value)

            label = field_labels.get(key, key.replace("_", " "))
            parts.append(f"{label}: {value}")

        if parts:
            lines.append(", ".join(parts))

    return "; ".join(lines)


def render_generic_text(submission, crime_label: str) -> str:
    answers = submission.answers or {}
    lines = []

    lines.append(f"Trata-se de atendimento preliminar relacionado a {crime_label.lower()}.")
    lines.append(format_person_block(submission))

    fatos = []

    data_fato = clean(answers.get("data_fato"))
    hora_fato = clean(answers.get("hora_fato"))
    local_fato = clean(answers.get("local_fato"))

    fato_base = join_parts([
        f"data {format_date_br(data_fato)}" if data_fato else "",
        f"hora aproximada {hora_fato}" if hora_fato else "",
        f"local {local_fato}" if local_fato else "",
    ], sep=", ")

    if fato_base:
        fatos.append(f"Segundo informado, o fato ocorreu em {fato_base}.")

    for key, value in answers.items():
        if key in {"data_fato", "hora_fato", "local_fato", "_pm_info", "_email"}:
            continue

        value = clean(value)
        if value is None:
            continue

        if isinstance(value, list):
            if value and all(isinstance(item, dict) for item in value):
                rendered = format_group_generic(value)
            else:
                rendered = ", ".join(str(item) for item in value if item)

            if rendered:
                fatos.append(f"{key.replace('_', ' ').capitalize()}: {rendered}.")
            continue

        if isinstance(value, bool):
            value = bool_to_text(value)

        fatos.append(f"{key.replace('_', ' ').capitalize()}: {value}.")

    if fatos:
        lines.append("Dos fatos:")
        lines.extend(fatos)

    if submission.narrative:
        lines.append(f"Relato livre apresentado pela parte: {submission.narrative}")

    photo_count = len(submission.photos or [])
    if photo_count:
        lines.append(f"Foram apresentados {photo_count} arquivo(s) de imagem.")

    return "\n\n".join(lines)