from app.renderer.common import clean, format_date_br


def render_adulteracao_sinal_identificador(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    data_fato = clean(answers.get("data_fato"))
    local_fato = clean(answers.get("local_fato"))
    placa = clean(answers.get("placa"))
    marca_modelo = clean(answers.get("marca_modelo"))
    cor = clean(answers.get("cor"))
    sinais = clean(answers.get("sinais"))
    autores = answers.get("Autor") or []
    documentos = answers.get("documentos")
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

    texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar possível adulteração de sinal identificador de veículo automotor."

    corpo = f"{nome}, declarante, informa"

    contexto_inicial = []
    if data_fato:
        contexto_inicial.append(f"no dia {format_date_br(data_fato)}")
    if local_fato:
        contexto_inicial.append(f"no local {local_fato}")

    if contexto_inicial:
        corpo += " que " + ", ".join(contexto_inicial)
    corpo += ", tomou conhecimento de possível adulteração de sinal identificador de veículo."

    dados_veiculo = []
    if placa:
        dados_veiculo.append(f"placa {placa}")
    if marca_modelo:
        dados_veiculo.append(f"marca/modelo {marca_modelo}")
    if cor:
        dados_veiculo.append(f"cor {cor}")

    if dados_veiculo:
        corpo += f" Que o veículo envolvido possui os seguintes dados: {', '.join(dados_veiculo)}."

    if sinais:
        corpo += f" Que os sinais aparentes de adulteração observados são: {sinais}."

    if autores_txt:
        corpo += f" Que foram informados como envolvidos/autores: {autores_txt}."

    if documentos is True:
        corpo += " Que foram apresentados documentos do veículo."
    elif documentos is False:
        corpo += " Que não foram apresentados documentos do veículo."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"