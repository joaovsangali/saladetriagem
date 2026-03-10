from app.renderer.common import clean, format_date_br


def render_acidente_transito(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    data_fato = clean(answers.get("data_fato"))
    hora_fato = clean(answers.get("hora_fato"))
    local_fato = clean(answers.get("local_fato"))
    veiculos = answers.get("veiculos") or []
    feridos = answers.get("feridos")
    danos = clean(answers.get("danos"))
    testemunhas = answers.get("testemunhas") or []

    def _format_veiculos(items: list) -> str:
        partes = []

        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue

            descricao = clean(item.get("descricao"))
            placa = clean(item.get("placa"))
            cor = clean(item.get("cor"))
            condutor_nome = clean(item.get("condutor_nome"))
            condutor_rg = clean(item.get("condutor_rg"))
            condutor_contato = clean(item.get("condutor_contato"))
            condutor_endereco = clean(item.get("condutor_endereco"))
            seguro = item.get("seguro")
            seguro_nome = clean(item.get("seguro_nome"))

            dados = [f"veículo {idx}"]
            if descricao:
                dados.append(f"modelo/descrição {descricao}")
            if placa:
                dados.append(f"placa {placa}")
            if cor:
                dados.append(f"cor {cor}")
            if condutor_nome:
                dados.append(f"conduzido por {condutor_nome}")
            if condutor_rg:
                dados.append(f"RG/documento do condutor {condutor_rg}")
            if condutor_contato:
                dados.append(f"contato do condutor {condutor_contato}")
            if condutor_endereco:
                dados.append(f"endereço do condutor {condutor_endereco}")
            if seguro is True:
                if seguro_nome:
                    dados.append(f"com seguro {seguro_nome}")
                else:
                    dados.append("com seguro informado")
            elif seguro is False:
                dados.append("sem seguro informado")

            if len(dados) > 1:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    def _format_testemunhas(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            nome_test = clean(item.get("nome"))
            contato_test = clean(item.get("contato"))
            rg_test = clean(item.get("rg"))

            dados = []
            if nome_test:
                dados.append(nome_test)
            if contato_test:
                dados.append(f"telefone {contato_test}")
            if rg_test:
                dados.append(f"RG/documento {rg_test}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    veiculos_txt = _format_veiculos(veiculos)
    testemunhas_txt = _format_testemunhas(testemunhas)

    texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar acidente de trânsito."

    corpo = f"{nome}, declarante, informa"

    contexto_inicial = []
    if data_fato:
        contexto_inicial.append(f"no dia {format_date_br(data_fato)}")
    if hora_fato:
        contexto_inicial.append(f"por volta de {hora_fato}")
    if local_fato:
        contexto_inicial.append(f"no local {local_fato}")

    if contexto_inicial:
        corpo += " que " + ", ".join(contexto_inicial)
    corpo += ", ocorreu acidente de trânsito."
    
    if veiculos_txt:
        corpo += f" Que os veículos envolvidos são os seguintes: {veiculos_txt}."

    if feridos is True:
        corpo += " Que houve feridos em decorrência do acidente."
    elif feridos is False:
        corpo += " Que não houve feridos em decorrência do acidente."

    if danos:
        corpo += f" Que os danos materiais informados são: {danos}."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"