from app.renderer.common import (
    clean,
    format_date_br,
    format_declarant_id,
    format_vitimas_text,
    get_pm_info,
)

def render_roubo_furto(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    declarant = format_declarant_id(submission)
    pm_info = get_pm_info(submission)
    is_pm = pm_info.get("policial_militar", False)
    vitimas = pm_info.get("vitimas") or []
    vitimas_text, verbo = format_vitimas_text(vitimas)
    modalidade_raw = answers.get("modalidade")
    if not modalidade_raw:
        # Inferir automaticamente baseado nos campos preenchidos
        if any(key.startswith("roubo_") and answers.get(key) for key in answers.keys()):
            modalidade_raw = "Roubo"
        elif any(key.startswith("furto_") and answers.get(key) for key in answers.keys()):
            modalidade_raw = "Furto"
    modalidade = clean(modalidade_raw)

    # ===== ADICIONE ESTA FUNÇÃO AQUI =====
    def _get_answer(prefix: str, field: str):
        """Try to get answer with prefix first, then without prefix"""
        prefixed_key = f"{prefix}_{field}"
        return answers.get(prefixed_key, answers.get(field))
    # ===== FIM =====

    def _format_people(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            nome_pessoa = clean(item.get("nome"))
            contato = clean(item.get("contato"))
            rg = clean(item.get("rg"))
            endereco = clean(item.get("endereco"))
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
            if rg:
                dados.append(f"RG/documento {rg}")
            if endereco:
                dados.append(f"endereço {endereco}")
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
            rg_test = clean(item.get("rg"))
            endereco_test = clean(item.get("endereco"))

            dados = []
            if nome_test:
                dados.append(nome_test)
            if contato_test:
                dados.append(f"telefone {contato_test}")
            if rg_test:
                dados.append(f"RG/documento {rg_test}")
            if endereco_test:
                dados.append(f"endereço {endereco_test}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    if modalidade == "Roubo":
        # Use helper function to get values with or without prefix
        data_fato = clean(_get_answer("roubo", "data_fato"))
        hora_fato = clean(_get_answer("roubo", "hora_fato"))
        local_fato = clean(_get_answer("roubo", "local_fato"))
        autores = _get_answer("roubo", "autores") or []
        meio_utilizado = clean(_get_answer("roubo", "meio_utilizado"))
        meio_utilizado_outro = clean(_get_answer("roubo", "meio_utilizado_outro"))
        cartoes = _get_answer("roubo", "cartoes") or []
        celulares = _get_answer("roubo", "celulares") or []
        joias = _get_answer("roubo", "joias") or []
        veiculos_subtraidos = _get_answer("roubo", "veiculos_subtraidos") or []
        outros_bens = clean(_get_answer("roubo", "outros_bens"))
        valor_estimado = clean(_get_answer("roubo", "valor_estimado"))
        veiculo_fuga = _get_answer("roubo", "veiculo_fuga") or []
        testemunhas = _get_answer("roubo", "testemunhas") or []
        cameras = clean(_get_answer("roubo", "cameras"))
        houve_dinheiro = _get_answer("roubo", "houve_dinheiro")

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

        texto = f"Comparece nesta delegacia de polícia, {declarant} para noticiar crime de roubo."

        corpo = f"{nome}, declarante, informa"

        contexto = []
        if data_fato:
            contexto.append(f"no dia {format_date_br(data_fato)}")
        if hora_fato:
            contexto.append(f"por volta de {hora_fato}")
        if local_fato:
            contexto.append(f"no local {local_fato}")

        if is_pm and vitimas_text:
            contexto_txt = ", ".join(contexto)
            if contexto_txt:
                corpo += f" que {contexto_txt}, {vitimas_text} {verbo} de roubo."
            else:
                corpo += f" que {vitimas_text} {verbo} de roubo."
        else:
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

    if modalidade == "Furto":
        # Use helper function to get values with or without prefix
        data_fato = clean(_get_answer("furto", "data_fato"))
        hora_fato = clean(_get_answer("furto", "hora_fato"))
        local_fato = clean(_get_answer("furto", "local_fato"))
        autores = _get_answer("furto", "autores") or []
        meio_utilizado = _get_answer("furto", "meio_utilizado") or []
        cartoes = _get_answer("furto", "cartoes") or []
        celulares = _get_answer("furto", "celulares") or []
        joias = _get_answer("furto", "joias") or []
        veiculos_subtraidos = _get_answer("furto", "veiculos_subtraidos") or []
        outros_bens = clean(_get_answer("furto", "outros_bens"))
        valor_estimado = clean(_get_answer("furto", "valor_estimado"))
        veiculo_fuga = _get_answer("furto", "veiculo_fuga") or []
        testemunhas = _get_answer("furto", "testemunhas") or []
        cameras = clean(_get_answer("furto", "cameras"))
        houve_dinheiro = _get_answer("furto", "houve_dinheiro")

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

        texto = f"Comparece nesta delegacia de polícia, {declarant} para noticiar crime de furto."

        corpo = f"{nome}, declarante, informa"

        contexto = []
        if data_fato:
            contexto.append(f"no dia {format_date_br(data_fato)}")
        if hora_fato:
            contexto.append(f"por volta de {hora_fato}")
        if local_fato:
            contexto.append(f"no local {local_fato}")

        if is_pm and vitimas_text:
            contexto_txt = ", ".join(contexto)
            if contexto_txt:
                corpo += f" que {contexto_txt}, {vitimas_text} {verbo} de furto."
            else:
                corpo += f" que {vitimas_text} {verbo} de furto."
        else:
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

    texto = f"Comparece nesta delegacia de polícia, {declarant} para noticiar fato relacionado a roubo/furto."

    corpo = (
        f"{nome}, declarante, informa que relatou fato classificado no formulário como roubo/furto, "
        "porém a modalidade específica não foi identificada corretamente no processamento."
    )

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"