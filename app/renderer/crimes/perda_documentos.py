from app.renderer.common import clean, format_date_br, format_declarant_id


def render_perda_documentos(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    declarant = format_declarant_id(submission)
    data = clean(answers.get("data"))
    local = clean(answers.get("local"))
    documentos = answers.get("documentos") or []
    suspeita_furto = answers.get("suspeita_furto")
    observacoes = clean(answers.get("observacoes"))

    def _format_documentos(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            tipo_documento = clean(item.get("tipo_documento"))
            numero_documento = clean(item.get("numero_documento"))

            dados = []
            if tipo_documento:
                dados.append(tipo_documento)
            if numero_documento:
                dados.append(f"número {numero_documento}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    documentos_txt = _format_documentos(documentos)

    texto = f"Comparece nesta delegacia de polícia, {declarant} para comunicar perda de documentos."

    corpo = f"{nome}, declarante, informa"

    contexto = []
    if data:
        contexto.append(f"na data/período aproximado de {format_date_br(data)}")
    if local:
        contexto.append(f"no local {local}")

    if contexto:
        corpo += " que " + ", ".join(contexto)
    corpo += ", percebeu a perda de documentos."

    if documentos_txt:
        corpo += f" Que os documentos informados como perdidos são: {documentos_txt}."

    if suspeita_furto is True:
        corpo += " Que há suspeita de furto/roubo relacionado ao desaparecimento dos documentos."
    elif suspeita_furto is False:
        corpo += " Que não há suspeita de furto/roubo relacionado ao desaparecimento dos documentos."

    if observacoes:
        corpo += f" Que as observações relevantes informadas são: {observacoes}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"