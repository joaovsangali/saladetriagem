from app.renderer.common import (
    clean,
    format_date_br,
    format_declarant_id,
    format_vitimas_text,
    get_pm_info,
)


def render_dano(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    declarant = format_declarant_id(submission)
    pm_info = get_pm_info(submission)
    is_pm = pm_info.get("policial_militar", False)
    vitimas = pm_info.get("vitimas") or []
    vitimas_text, verbo = format_vitimas_text(vitimas)
    data_fato = clean(answers.get("data_fato"))
    local_fato = clean(answers.get("local_fato"))
    tipo_patrimonio = clean(answers.get("tipo_patrimonio"))
    bens_danificados = answers.get("bens_danificados") or []
    forma_dano = clean(answers.get("forma_dano"))
    valor_prejuizo = clean(answers.get("valor_prejuizo"))
    autor = answers.get("autor") or []
    motivacao = clean(answers.get("motivacao"))
    cameras = clean(answers.get("cameras"))
    testemunhas = answers.get("testemunhas") or []

    def _format_bens(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            descricao = clean(item.get("descricao"))
            if descricao:
                partes.append(descricao)

        return "; ".join(partes)

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

    bens_txt = _format_bens(bens_danificados)
    autores_txt = _format_autores(autor)
    testemunhas_txt = _format_testemunhas(testemunhas)

    texto = f"Comparece nesta delegacia de polícia, {declarant} para noticiar crime de dano."

    corpo = f"{nome}, declarante, informa"

    contexto_inicial = []
    if data_fato:
        contexto_inicial.append(f"no dia {format_date_br(data_fato)}")
    if local_fato:
        contexto_inicial.append(f"no local {local_fato}")

    if is_pm and vitimas_text:
        contexto_txt = ", ".join(contexto_inicial)
        if contexto_txt:
            corpo += f" que {contexto_txt}, {vitimas_text} {verbo} de dano."
        else:
            corpo += f" que {vitimas_text} {verbo} de dano."
    else:
        if contexto_inicial:
            corpo += " que " + ", ".join(contexto_inicial)
        corpo += ", ocorreu o crime de dano."

    if tipo_patrimonio:
        corpo += f" Que o patrimônio atingido é classificado como {tipo_patrimonio.lower()}."

    if bens_txt:
        corpo += f" Que os bens danificados são os seguintes: {bens_txt}."

    if forma_dano:
        corpo += f" Que o dano foi causado da seguinte forma: {forma_dano}."

    if autores_txt:
        corpo += f" Que o fato teria sido praticado por: {autores_txt}."

    if motivacao:
        corpo += f" Que a motivação provável informada é: {motivacao}."

    if valor_prejuizo:
        corpo += f" Que o prejuízo estimado é de R$ {valor_prejuizo}."

    if cameras:
        corpo += f" Que quanto à existência de câmeras de segurança no local, a parte informou: {cameras.lower()}."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"