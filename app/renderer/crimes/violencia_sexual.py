from app.renderer.common import clean, format_date_br, format_declarant_id


def render_violencia_sexual(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    declarant = format_declarant_id(submission)
    vitima_crianca = answers.get("vitima_crianca")
    nome_responsavel = clean(answers.get("nome_responsavel"))
    data_fato = clean(answers.get("data_fato"))
    local_fato = clean(answers.get("local_fato"))
    autor = answers.get("autor") or []
    relacao_agressor = clean(answers.get("relacao_agressor"))
    relacao_agressor_outro = clean(answers.get("relacao_agressor_outro"))
    reside_agressor = answers.get("reside_agressor")
    atendimento_medico = answers.get("atendimento_medico")
    local_atendimento_medico = clean(answers.get("local_atendimento_medico"))
    testemunhas = answers.get("testemunhas") or []

    def _format_autor(items: list) -> str:
        if not items:
            return ""
        item = items[0] if isinstance(items[0], dict) else {}
        nome_autor = clean(item.get("nome"))
        rg_autor = clean(item.get("rg"))
        contato_autor = clean(item.get("contato"))
        endereco_autor = clean(item.get("endereco"))
        dados = []
        if nome_autor:
            dados.append(nome_autor)
        if rg_autor:
            dados.append(f"RG/documento {rg_autor}")
        if contato_autor:
            dados.append(f"contato {contato_autor}")
        if endereco_autor:
            dados.append(f"endereço {endereco_autor}")
        return ", ".join(dados)

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

    autor_txt = _format_autor(autor)
    testemunhas_txt = _format_testemunhas(testemunhas)
    relacao_final = relacao_agressor_outro if relacao_agressor == "Outros" and relacao_agressor_outro else relacao_agressor

    texto = f"Comparece nesta delegacia de polícia, {declarant} para noticiar fato relacionado a violência sexual."

    corpo = f"{nome}, declarante, informa"

    contexto = []
    if data_fato:
        contexto.append(f"no dia {format_date_br(data_fato)}")
    if local_fato:
        contexto.append(f"no local {local_fato}")

    if contexto:
        corpo += " que " + ", ".join(contexto)
    corpo += ", ocorreu o fato ora comunicado."

    if vitima_crianca is True:
        corpo += " Que a vítima é criança ou adolescente (menor de 18 anos)."
        if nome_responsavel:
            corpo += f" Que o responsável legal informado é: {nome_responsavel}."
    elif vitima_crianca is False:
        corpo += " Que a vítima é maior de idade."

    if autor_txt:
        corpo += f" Que o agressor informado é: {autor_txt}."

    if relacao_final:
        corpo += f" Que a relação da vítima com o agressor é: {relacao_final}."

    if reside_agressor is True:
        corpo += " Que o agressor reside com a vítima."
    elif reside_agressor is False:
        corpo += " Que o agressor não reside com a vítima."

    if atendimento_medico is True:
        corpo += " Que houve necessidade de atendimento médico."
        if local_atendimento_medico:
            corpo += f" Que o atendimento ocorreu em: {local_atendimento_medico}."
    elif atendimento_medico is False:
        corpo += " Que não houve necessidade de atendimento médico."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"
