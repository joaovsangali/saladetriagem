from app.renderer.common import clean, format_date_br


def render_porte_ilegal_arma_fogo(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    data_fato = clean(answers.get("data_fato"))
    hora_fato = clean(answers.get("hora_fato"))
    local_fato = clean(answers.get("local_fato"))
    armas = answers.get("armas") or []
    municoes = answers.get("municoes") or []
    autores = answers.get("autores") or []
    documentacao = answers.get("documentacao")
    testemunhas = answers.get("testemunhas") or []

    def _format_armas(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            tipo = clean(item.get("tipo"))
            marca = clean(item.get("marca"))
            calibre = clean(item.get("calibre"))
            numeracao = clean(item.get("numeracao"))

            dados = []
            if tipo:
                dados.append(f"tipo {tipo}")
            if marca:
                dados.append(f"marca {marca}")
            if calibre:
                dados.append(f"calibre {calibre}")
            if numeracao:
                dados.append(f"numeração {numeracao}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    def _format_municoes(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            calibre = clean(item.get("calibre"))
            quantidade = clean(item.get("quantidade"))

            dados = []
            if calibre:
                dados.append(f"calibre {calibre}")
            if quantidade:
                dados.append(f"quantidade {quantidade}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    def _format_autores(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            nome_autor = clean(item.get("nome"))
            contato_autor = clean(item.get("contato"))
            rg_autor = clean(item.get("rg"))
            endereco_autor = clean(item.get("endereco"))

            dados = []
            if nome_autor:
                dados.append(nome_autor)
            if contato_autor:
                dados.append(f"contato {contato_autor}")
            if rg_autor:
                dados.append(f"RG/documento {rg_autor}")
            if endereco_autor:
                dados.append(f"endereço {endereco_autor}")

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

    armas_txt = _format_armas(armas)
    municoes_txt = _format_municoes(municoes)
    autores_txt = _format_autores(autores)
    testemunhas_txt = _format_testemunhas(testemunhas)

    texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar fato relacionado a porte ilegal de arma de fogo."

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
    corpo += ", ocorreu fato relacionado a porte ilegal de arma de fogo."

    if autores_txt:
        corpo += f" Que o(s) autor(es)/envolvido(s) informado(s) é(são): {autores_txt}."

    if armas_txt:
        corpo += f" Que a(s) arma(s) informada(s) possui(em) as seguintes características: {armas_txt}."

    if municoes_txt:
        corpo += f" Que a(s) munição(ões) informada(s) possui(em) os seguintes dados: {municoes_txt}."

    if documentacao is True:
        corpo += " Que havia documentação/registro da arma informado."
    elif documentacao is False:
        corpo += " Que não havia documentação/registro da arma informado."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"