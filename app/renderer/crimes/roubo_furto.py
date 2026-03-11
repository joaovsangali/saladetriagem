from app.renderer.common import clean, format_date_br


def render_roubo_furto(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    modalidade = clean(answers.get("modalidade"))

    def _format_people(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            nome_pessoa = clean(item.get("nome"))
            contato = clean(item.get("contato"))
            altura = clean(item.get("altura_aproximada"))
            peso = clean(item.get("peso_aproximado"))
            cor_pele = clean(item.get("cor_pele"))
            roupas = clean(item.get("roupas"))
            outras = clean(item.get("outras_caracteristicas"))

            dados = []
            if nome_pessoa:
                dados.append(nome_pessoa)
            if contato:
                dados.append(f"contato {contato}")
            if altura:
                dados.append(f"altura aproximada {altura}")
            if peso:
                dados.append(f"peso aproximado {peso}")
            if cor_pele:
                dados.append(f"cor da pele {cor_pele}")
            if roupas:
                dados.append(f"roupas {roupas}")
            if outras:
                dados.append(f"outras características {outras}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    def _format_simple_group(items: list, field_map: dict) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            dados = []
            for field_id, label in field_map.items():
                value = clean(item.get(field_id))
                if value:
                    dados.append(f"{label} {value}")

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

    if modalidade == "Roubo":
        data_fato = clean(answers.get("roubo_data_fato"))
        hora_fato = clean(answers.get("roubo_hora_fato"))
        local_fato = clean(answers.get("roubo_local_fato"))
        autores = answers.get("roubo_autores") or []
        meio_utilizado = clean(answers.get("roubo_meio_utilizado"))
        meio_utilizado_outro = clean(answers.get("roubo_meio_utilizado_outro"))
        cartoes = answers.get("roubo_cartoes") or []
        celulares = answers.get("roubo_celulares") or []
        joias = answers.get("roubo_joias") or []
        veiculos_subtraidos = answers.get("roubo_veiculos_subtraidos") or []
        outros_bens = clean(answers.get("roubo_outros_bens"))
        valor_estimado = clean(answers.get("roubo_valor_estimado"))
        veiculo_fuga = answers.get("roubo_veiculo_fuga") or []
        testemunhas = answers.get("roubo_testemunhas") or []
        cameras = clean(answers.get("roubo_cameras"))
        houve_dinheiro = answers.get("roubo_houve_dinheiro")

        autores_txt = _format_people(autores)
        testemunhas_txt = _format_testemunhas(testemunhas)
        cartoes_txt = _format_simple_group(
            cartoes,
            {"banco": "banco", "tipo_cartao": "tipo", "numero_cartao": "número"},
        )
        celulares_txt = _format_simple_group(
            celulares,
            {"marca": "marca", "modelo": "modelo", "numero_telefone": "telefone", "imei": "IMEI"},
        )
        joias_txt = _format_simple_group(
            joias,
            {"marca": "marca", "metal_pedra": "metal/pedra"},
        )
        veiculos_txt = _format_simple_group(
            veiculos_subtraidos,
            {"marca": "marca", "tipo": "tipo", "cor": "cor", "modelo": "modelo", "placa": "placa"},
        )
        fuga_txt = _format_simple_group(
            veiculo_fuga,
            {"marca": "marca", "tipo": "tipo", "cor": "cor", "modelo": "modelo", "placa": "placa"},
        )

        meio_final = meio_utilizado_outro if meio_utilizado == "Outros" and meio_utilizado_outro else meio_utilizado

        texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar crime de roubo."

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
        corpo += ", foi vítima de roubo."

        if autores_txt:
            corpo += f" Que o(s) autor(es) informado(s) é(são): {autores_txt}."

        if meio_final:
            corpo += f" Que o meio empregado na prática do roubo foi: {meio_final}."

        if cartoes_txt:
            corpo += f" Que foram subtraídos os seguintes cartões: {cartoes_txt}."

        if celulares_txt:
            corpo += f" Que foram subtraídos os seguintes celulares: {celulares_txt}."

        if houve_dinheiro is True:
            corpo += " Que foi subtraído dinheiro."
        elif houve_dinheiro is False:
            corpo += " Que não foi subtraído dinheiro."

        if joias_txt:
            corpo += f" Que foram subtraídas as seguintes joias: {joias_txt}."

        if veiculos_txt:
            corpo += f" Que foram subtraídos os seguintes veículos: {veiculos_txt}."

        if outros_bens:
            corpo += f" Que também foram subtraídos outros bens, assim descritos: {outros_bens}."

        if valor_estimado:
            corpo += f" Que o valor estimado dos bens subtraídos é de R$ {valor_estimado}."

        if fuga_txt:
            corpo += f" Que foi informado o seguinte veículo de fuga: {fuga_txt}."

        if cameras:
            corpo += f" Que, quanto à existência de câmeras de segurança no local, a parte informou: {cameras.lower()}."

        if testemunhas_txt:
            corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

        if submission.narrative:
            corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

        return f"{texto}\n\n{corpo}"

    data_fato = clean(answers.get("furto_data_fato"))
    hora_fato = clean(answers.get("furto_hora_fato"))
    local_fato = clean(answers.get("furto_local_fato"))
    autores = answers.get("furto_autores") or []
    meio_utilizado = answers.get("furto_meio_utilizado") or []
    cartoes = answers.get("furto_cartoes") or []
    celulares = answers.get("furto_celulares") or []
    joias = answers.get("furto_joias") or []
    veiculos_subtraidos = answers.get("furto_veiculos_subtraidos") or []
    outros_bens = clean(answers.get("furto_outros_bens"))
    valor_estimado = clean(answers.get("furto_valor_estimado"))
    veiculo_fuga = answers.get("furto_veiculo_fuga") or []
    testemunhas = answers.get("furto_testemunhas") or []
    cameras = clean(answers.get("furto_cameras"))
    houve_dinheiro = answers.get("furto_houve_dinheiro")

    autores_txt = _format_people(autores)
    testemunhas_txt = _format_testemunhas(testemunhas)
    meio_txt = ", ".join(str(item) for item in meio_utilizado if item)
    cartoes_txt = _format_simple_group(
        cartoes,
        {"banco": "banco", "tipo_cartao": "tipo", "numero_cartao": "número"},
    )
    celulares_txt = _format_simple_group(
        celulares,
        {"marca": "marca", "modelo": "modelo", "numero_telefone": "telefone", "imei": "IMEI"},
    )
    joias_txt = _format_simple_group(
        joias,
        {"marca": "marca", "metal_pedra": "metal/pedra"},
    )
    veiculos_txt = _format_simple_group(
        veiculos_subtraidos,
        {"marca": "marca", "tipo": "tipo", "cor": "cor", "modelo": "modelo", "placa": "placa"},
    )
    fuga_txt = _format_simple_group(
        veiculo_fuga,
        {"marca": "marca", "tipo": "tipo", "cor": "cor", "modelo": "modelo", "placa": "placa"},
    )

    texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar crime de furto."

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
    corpo += ", foi vítima de furto."

    if autores_txt:
        corpo += f" Que o(s) autor(es) informado(s) é(são): {autores_txt}."

    if meio_txt:
        corpo += f" Que o meio empregado na prática do furto foi: {meio_txt}."

    if cartoes_txt:
        corpo += f" Que foram subtraídos os seguintes cartões: {cartoes_txt}."

    if celulares_txt:
        corpo += f" Que foram subtraídos os seguintes celulares: {celulares_txt}."

    if houve_dinheiro is True:
        corpo += " Que foi subtraído dinheiro."
    elif houve_dinheiro is False:
        corpo += " Que não foi subtraído dinheiro."

    if joias_txt:
        corpo += f" Que foram subtraídas as seguintes joias: {joias_txt}."

    if veiculos_txt:
        corpo += f" Que foram subtraídos os seguintes veículos: {veiculos_txt}."

    if outros_bens:
        corpo += f" Que também foram subtraídos outros bens, assim descritos: {outros_bens}."

    if valor_estimado:
        corpo += f" Que o valor estimado dos bens subtraídos é de R$ {valor_estimado}."

    if fuga_txt:
        corpo += f" Que foi informado o seguinte veículo de fuga: {fuga_txt}."

    if cameras:
        corpo += f" Que, quanto à existência de câmeras de segurança no local, a parte informou: {cameras.lower()}."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"