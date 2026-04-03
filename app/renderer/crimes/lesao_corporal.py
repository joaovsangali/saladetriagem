from app.renderer.common import clean, format_date_br, format_declarant_id


def render_lesao_corporal(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    declarant = format_declarant_id(submission)
    data_fato = clean(answers.get("data_fato"))
    hora_fato = clean(answers.get("hora_fato"))
    local_fato = clean(answers.get("local_fato"))
    relacao_autor = clean(answers.get("relacao_autor"))
    relacao_autor_outros = clean(answers.get("relacao_autor_outros"))
    autores = answers.get("autores") or []
    tipo_lesao = answers.get("tipo_lesao") or []
    regiao_corpo = clean(answers.get("regiao_corpo"))
    atendimento_medico = answers.get("atendimento_medico")
    local_atendimento_medico = clean(answers.get("local_atendimento_medico"))
    testemunhas = answers.get("testemunhas") or []
    historico_violencia = clean(answers.get("historico_violencia"))

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

    relacao_final = relacao_autor_outros if relacao_autor == "Outros" and relacao_autor_outros else relacao_autor
    autores_txt = _format_autores(autores)
    testemunhas_txt = _format_testemunhas(testemunhas)
    tipo_lesao_txt = ", ".join(str(item) for item in tipo_lesao if item)

    texto = f"Comparece nesta delegacia de polícia, {declarant} para noticiar crime de lesão corporal."

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
    corpo += ", foi vítima de lesão corporal."

    if autores_txt:
        corpo += f" Que o(s) autor(es) informado(s) é(são): {autores_txt}."

    if relacao_final:
        corpo += f" Que a relação da parte com o autor é: {relacao_final}."

    if tipo_lesao_txt:
        corpo += f" Que a agressão/lesão sofrida ocorreu mediante: {tipo_lesao_txt}."

    if regiao_corpo:
        corpo += f" Que a região do corpo afetada foi: {regiao_corpo}."

    if atendimento_medico is True:
        corpo += " Que houve atendimento médico."
        if local_atendimento_medico:
            corpo += f" Que o atendimento ocorreu em: {local_atendimento_medico}."
    elif atendimento_medico is False:
        corpo += " Que não houve atendimento médico."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if historico_violencia:
        corpo += f" Que, quanto ao histórico da situação, a parte informou: {historico_violencia}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"