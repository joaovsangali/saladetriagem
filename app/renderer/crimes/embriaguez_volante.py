from app.renderer.common import clean, format_date_br


def render_embriaguez_volante(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    data_fato = clean(answers.get("data_fato"))
    hora_fato = clean(answers.get("hora_fato"))
    local_fato = clean(answers.get("local_fato"))
    veiculos = answers.get("veiculos") or []
    autores = answers.get("autores") or []
    sinais = answers.get("sinais") or []
    teste_etilometro = answers.get("teste_etilometro")
    resultado = clean(answers.get("resultado"))
    testemunhas = answers.get("testemunhas") or []

    def _format_veiculos(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            marca = clean(item.get("marca"))
            modelo = clean(item.get("modelo"))
            cor = clean(item.get("cor"))
            placa = clean(item.get("placa"))

            dados = []
            if marca:
                dados.append(f"marca {marca}")
            if modelo:
                dados.append(f"modelo {modelo}")
            if cor:
                dados.append(f"cor {cor}")
            if placa:
                dados.append(f"placa {placa}")

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

    veiculos_txt = _format_veiculos(veiculos)
    autores_txt = _format_autores(autores)
    testemunhas_txt = _format_testemunhas(testemunhas)
    sinais_txt = ", ".join(str(item) for item in sinais if item)

    texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar fato relacionado a embriaguez ao volante."

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
    corpo += ", ocorreu fato relacionado a condução de veículo sob possível influência de álcool."

    if autores_txt:
        corpo += f" Que o(s) condutor(es)/autor(es) informado(s) são: {autores_txt}."

    if veiculos_txt:
        corpo += f" Que o(s) veículo(s) envolvido(s) possui(em) os seguintes dados: {veiculos_txt}."

    if sinais_txt:
        corpo += f" Que os sinais de embriaguez observados foram: {sinais_txt}."

    if teste_etilometro is True:
        corpo += " Que foi realizado teste do etilômetro."
        if resultado:
            corpo += f" Que o resultado informado foi de {resultado} mg/L."
    elif teste_etilometro is False:
        corpo += " Que não foi realizado teste do etilômetro."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"