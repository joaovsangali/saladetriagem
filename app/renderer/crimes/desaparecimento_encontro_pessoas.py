from app.renderer.common import clean, format_date_br


def render_desaparecimento_encontro_pessoas(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    tipo = clean(answers.get("tipo"))
    data_desaparecimento = clean(answers.get("data_desaparecimento"))
    hora_desaparecimento = clean(answers.get("hora_desaparecimento"))
    local_desaparecimento = clean(answers.get("local_desaparecimento"))
    data_encontro = clean(answers.get("data_encontro"))
    local_encontro = clean(answers.get("local_encontro"))
    roupas = clean(answers.get("roupas"))
    pessoa = answers.get("pessoa") or []
    contato_familia = answers.get("contato_familia") or []

    def _format_pessoa(items: list) -> str:
        if not items:
            return ""

        item = items[0] if isinstance(items[0], dict) else {}
        nome_pessoa = clean(item.get("nome"))
        rg_pessoa = clean(item.get("rg"))
        contato_pessoa = clean(item.get("contato"))
        endereco_pessoa = clean(item.get("endereco"))

        dados = []
        if nome_pessoa:
            dados.append(nome_pessoa)
        if rg_pessoa:
            dados.append(f"RG/documento {rg_pessoa}")
        if contato_pessoa:
            dados.append(f"contato {contato_pessoa}")
        if endereco_pessoa:
            dados.append(f"endereço {endereco_pessoa}")

        return ", ".join(dados)

    def _format_contatos(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            nome_contato = clean(item.get("nome"))
            contato = clean(item.get("contato"))
            rg = clean(item.get("rg"))
            endereco = clean(item.get("endereco"))

            dados = []
            if nome_contato:
                dados.append(nome_contato)
            if contato:
                dados.append(f"telefone/contato {contato}")
            if rg:
                dados.append(f"RG/documento {rg}")
            if endereco:
                dados.append(f"endereço {endereco}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    pessoa_txt = _format_pessoa(pessoa)
    contatos_txt = _format_contatos(contato_familia)

    if tipo == "Encontro/Localização":
        texto = f"Comparece nesta delegacia de polícia, {nome} para comunicar encontro/localização de pessoa."
        corpo = f"{nome}, declarante, informa"

        contexto = []
        if data_encontro:
            contexto.append(f"no dia {format_date_br(data_encontro)}")
        if local_encontro:
            contexto.append(f"no local {local_encontro}")

        if contexto:
            corpo += " que " + ", ".join(contexto)
        corpo += ", houve o encontro/localização de pessoa."

        if pessoa_txt:
            corpo += f" Que a pessoa localizada foi identificada como: {pessoa_txt}."

        if submission.narrative:
            corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

        return f"{texto}\n\n{corpo}"

    texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar desaparecimento de pessoa."

    corpo = f"{nome}, declarante, informa"

    contexto = []
    if data_desaparecimento:
        contexto.append(f"no dia {format_date_br(data_desaparecimento)}")
    if hora_desaparecimento:
        contexto.append(f"por volta de {hora_desaparecimento}")
    if local_desaparecimento:
        contexto.append(f"no local {local_desaparecimento}")

    if contexto:
        corpo += " que " + ", ".join(contexto)
    corpo += ", ocorreu o desaparecimento de pessoa."

    if pessoa_txt:
        corpo += f" Que a pessoa desaparecida foi identificada como: {pessoa_txt}."

    if roupas:
        corpo += f" Que, segundo informado, a pessoa foi vista pela última vez usando as seguintes roupas: {roupas}."

    if contatos_txt:
        corpo += f" Que foram indicados como contatos de familiar/responsável: {contatos_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"