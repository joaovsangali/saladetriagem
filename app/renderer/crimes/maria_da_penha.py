from app.renderer.common import (
    clean,
    format_date_br,
    format_declarant_id,
    format_vitimas_text,
    get_pm_info,
    get_subject_genitive,
    get_subject_nominative,
)


def render_maria_da_penha(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    declarant = format_declarant_id(submission)
    pm_info = get_pm_info(submission)
    is_pm = pm_info.get("policial_militar", False)
    vitimas = pm_info.get("vitimas") or []
    vitimas_text, verbo = format_vitimas_text(vitimas)
    subject_gen = get_subject_genitive(submission)
    subject_nom = get_subject_nominative(submission)
    local_fato = clean(answers.get("local_fato"))
    data_fato = clean(answers.get("data_fato"))
    autores = answers.get("autores") or []
    relacao_agressor = clean(answers.get("relacao_agressor"))
    relacao_agressor_outro = clean(answers.get("relacao_agressor_outro"))
    tipo_violencia = clean(answers.get("tipo_violencia"))
    reside_agressor = answers.get("reside_agressor")
    filhos_envolvidos = answers.get("filhos_envolvidos")
    atendimento_medico = answers.get("atendimento_medico")
    local_atendimento_medico = clean(answers.get("local_atendimento_medico"))
    testemunhas = answers.get("testemunhas") or []
    medida_protetiva = answers.get("medida_protetiva")
    deseja_medida_protetiva = answers.get("deseja_medida_protetiva")

    def _format_autor(items: list) -> str:
        if not items:
            return ""

        item = items[0] if isinstance(items[0], dict) else {}

        nome_autor = clean(item.get("nome"))
        contato_autor = clean(item.get("contato"))

        dados = []
        if nome_autor:
            dados.append(nome_autor)
        if contato_autor:
            dados.append(f"contato {contato_autor}")

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

    autor_txt = _format_autor(autores)
    testemunhas_txt = _format_testemunhas(testemunhas)
    relacao_final = relacao_agressor_outro if relacao_agressor == "Outro" and relacao_agressor_outro else relacao_agressor

    texto = f"Comparece nesta delegacia de polícia, {declarant} para noticiar fato relacionado à violência doméstica e familiar contra a mulher."

    corpo = f"{nome}, declarante, informa"

    contexto = []
    if data_fato:
        contexto.append(f"no dia {format_date_br(data_fato)}")
    if local_fato:
        contexto.append(f"no local {local_fato}")

    if is_pm and vitimas_text:
        contexto_txt = ", ".join(contexto)
        if contexto_txt:
            corpo += f" que {contexto_txt}, {vitimas_text} {verbo} de violência doméstica."
        else:
            corpo += f" que {vitimas_text} {verbo} de violência doméstica."
    else:
        if contexto:
            corpo += " que " + ", ".join(contexto)
        corpo += ", foi vítima de violência doméstica."

    if autor_txt:
        corpo += f" Que o agressor informado é: {autor_txt}."

    if relacao_final:
        corpo += f" Que a relação {subject_gen} com o agressor é: {relacao_final}."

    if tipo_violencia:
        corpo += f" Que o tipo de violência informado é: {tipo_violencia}."

    if reside_agressor is True:
        corpo += f" Que {subject_nom} reside com o agressor."
    elif reside_agressor is False:
        corpo += f" Que {subject_nom} não reside com o agressor."

    if filhos_envolvidos is True:
        corpo += " Que há filhos menores envolvidos."
    elif filhos_envolvidos is False:
        corpo += " Que não há filhos menores envolvidos."

    if atendimento_medico is True:
        corpo += " Que houve necessidade de atendimento médico."
        if local_atendimento_medico:
            corpo += f" Que o atendimento ocorreu em: {local_atendimento_medico}."
    elif atendimento_medico is False:
        corpo += " Que não houve necessidade de atendimento médico."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if medida_protetiva is True:
        corpo += f" Que {subject_nom} informa já possuir medida protetiva."
    elif medida_protetiva is False:
        corpo += f" Que {subject_nom} informa não possuir medida protetiva."
        if deseja_medida_protetiva is True:
            corpo += " Que manifesta interesse em requerer medidas protetivas."
        elif deseja_medida_protetiva is False:
            corpo += " Que não manifesta interesse em requerer medidas protetivas."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"