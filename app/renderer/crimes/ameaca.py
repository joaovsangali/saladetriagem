from app.renderer.common import clean, format_date_br, format_declarant_id


def render_ameaca(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    declarant = format_declarant_id(submission)
    data_fato = clean(answers.get("data_fato"))
    meio_ameaca = clean(answers.get("meio_ameaca"))
    conteudo_ameaca = clean(answers.get("conteudo_ameaca"))
    relacao_autor = clean(answers.get("relacao_autor"))
    contexto = clean(answers.get("contexto"))
    autores = answers.get("autores") or []
    testemunhas = answers.get("testemunhas") or []

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

    autores_txt = _format_autores(autores)
    testemunhas_txt = _format_testemunhas(testemunhas)

    texto = f"Comparece nesta delegacia de polícia, {declarant} para noticiar crime de ameaça."

    corpo = f"{nome}, declarante, informa"
    complemento = []

    if data_fato:
        complemento.append(f"no dia {format_date_br(data_fato)}")
    if meio_ameaca:
        complemento.append(f"foi vítima de ameaça realizada {meio_ameaca.lower()}")

    if complemento:
        corpo += " que " + ", ".join(complemento)
    corpo += "."

    if autores_txt:
        corpo += f" Que a ameaça foi realizada por {autores_txt}"
        if relacao_autor:
            corpo += f", que é seu(sua) {relacao_autor}"
        if contexto:
            corpo += f" por causa de {contexto}"
        corpo += "."

    elif relacao_autor or contexto:
        corpo += " Que"
        if relacao_autor:
            corpo += f" o autor é seu(sua) {relacao_autor}"
        if contexto:
            if relacao_autor:
                corpo += f" e agiu por causa de {contexto}"
            else:
                corpo += f" a ameaça ocorreu por causa de {contexto}"
        corpo += "."

    if conteudo_ameaca:
        corpo += f" Que o conteúdo da ameaça era: {conteudo_ameaca}."

    if testemunhas_txt:
        corpo += f" Que o crime foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"