from app.renderer.common import clean, format_date_br, format_declarant_id


def render_trafico_drogas(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    declarant = format_declarant_id(submission)
    data_fato = clean(answers.get("data_fato"))
    hora_fato = clean(answers.get("hora_fato"))
    local_fato = clean(answers.get("local_fato"))
    autores = answers.get("autores") or []
    drogas = answers.get("drogas") or []
    testemunhas = answers.get("testemunhas") or []
    cameras = answers.get("cameras")

    def _format_autores(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            nome_autor = clean(item.get("nome"))
            contato_autor = clean(item.get("contato"))

            dados = []
            if nome_autor:
                dados.append(nome_autor)
            if contato_autor:
                dados.append(f"contato {contato_autor}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    def _format_drogas(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            tipo_droga = clean(item.get("tipo_droga"))
            quantidade_unidades = clean(item.get("quantidade_unidades"))
            peso = clean(item.get("peso"))

            dados = []
            if tipo_droga:
                dados.append(f"tipo {tipo_droga}")
            if quantidade_unidades:
                dados.append(f"quantidade {quantidade_unidades}")
            if peso:
                dados.append(f"peso {peso}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    def _format_testemunhas(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            nome_test = clean(item.get("nome"))
            contato_test = clean(item.get("contato"))

            dados = []
            if nome_test:
                dados.append(nome_test)
            if contato_test:
                dados.append(f"telefone {contato_test}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    autores_txt = _format_autores(autores)
    drogas_txt = _format_drogas(drogas)
    testemunhas_txt = _format_testemunhas(testemunhas)

    texto = f"Comparece nesta delegacia de polícia, {declarant} para noticiar fato relacionado a tráfico de drogas."

    corpo = f"{nome}, declarante, informa"

    contexto = []
    if data_fato:
        contexto.append(f"no dia {format_date_br(data_fato)}")
    if hora_fato:
        contexto.append(f"por volta de {hora_fato}")
    if local_fato:
        contexto.append(f"no local {local_fato}")

    if contexto:
        corpo += " que " + ", ".join(contexto)
    corpo += ", ocorreu fato relacionado a tráfico de drogas."

    if autores_txt:
        corpo += f" Que o(s) autor(es)/envolvido(s) informado(s) é(são): {autores_txt}."

    if drogas_txt:
        corpo += f" Que as substâncias/porções informadas são as seguintes: {drogas_txt}."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if cameras is True:
        corpo += " Que há câmeras de segurança no local."
    elif cameras is False:
        corpo += " Que não há câmeras de segurança no local."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"