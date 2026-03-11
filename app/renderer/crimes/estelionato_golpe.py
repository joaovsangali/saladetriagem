from app.renderer.common import clean, format_date_br


def render_estelionato_golpe(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    data_fato = clean(answers.get("data_fato"))
    local_fato = clean(answers.get("local_fato"))
    modalidade = clean(answers.get("modalidade"))
    modalidade_outro = clean(answers.get("modalidade_outro"))
    meio_contato = clean(answers.get("meio_contato"))
    houve_transferencia = answers.get("houve_transferencia")
    transferencias = answers.get("transferencias") or []
    valor_prejuizo = clean(answers.get("valor_prejuizo"))
    autores = answers.get("autores") or []
    testemunhas = answers.get("testemunhas") or []

    detail_key_map = {
        "E-mail": "meio_contato_email",
        "Facebook": "meio_contato_facebook",
        "Instagram": "meio_contato_instagram",
        "Outros": "meio_contato_outros",
        "Presencialmente": "meio_contato_presencialmente",
        "Telegram": "meio_contato_telegram",
        "Telefone": "meio_contato_telefone",
        "Website": "meio_contato_website",
        "WhatsApp": "meio_contato_whatsapp",
    }
    detalhe_meio = clean(answers.get(detail_key_map.get(meio_contato, ""))) if meio_contato else None

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

    def _format_transferencias(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            banco = clean(item.get("banco"))
            conta = clean(item.get("conta"))
            agencia = clean(item.get("agencia"))
            pix = clean(item.get("número pix"))
            beneficiario = clean(item.get("beneficiario"))

            dados = []
            if banco:
                dados.append(f"banco {banco}")
            if agencia:
                dados.append(f"agência {agencia}")
            if conta:
                dados.append(f"conta {conta}")
            if pix:
                dados.append(f"PIX {pix}")
            if beneficiario:
                dados.append(f"beneficiário {beneficiario}")

            if dados:
                partes.append(", ".join(dados))

        return "; ".join(partes)

    modalidade_final = modalidade_outro if modalidade == "Outro" and modalidade_outro else modalidade
    autores_txt = _format_autores(autores)
    testemunhas_txt = _format_testemunhas(testemunhas)
    transferencias_txt = _format_transferencias(transferencias)

    texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar crime de estelionato."

    corpo = f"{nome}, declarante, informa"

    contexto = []
    if data_fato:
        contexto.append(f"no dia {format_date_br(data_fato)}")
    if local_fato:
        contexto.append(f"no local {local_fato}")

    if contexto:
        corpo += " que " + ", ".join(contexto)
    corpo += ", foi vítima de possível golpe/estelionato."

    if modalidade_final:
        corpo += f" Que a modalidade do golpe informada foi: {modalidade_final}."

    if meio_contato:
        corpo += f" Que o contato com o autor ocorreu por meio de {meio_contato.lower()}."
        if detalhe_meio:
            corpo += f" Que o dado de identificação/informação apresentado nesse meio foi: {detalhe_meio}."

    if autores_txt:
        corpo += f" Que o(s) autor(es), conforme informado, é(são): {autores_txt}."

    if houve_transferencia is True:
        corpo += " Que houve transferência bancária, PIX ou pagamento relacionado ao golpe."
        if transferencias_txt:
            corpo += f" Que os dados informados da transferência/pagamento são: {transferencias_txt}."
    elif houve_transferencia is False:
        corpo += " Que não houve transferência bancária, PIX ou pagamento relacionado ao golpe."

    if valor_prejuizo:
        corpo += f" Que o prejuízo informado é de R$ {valor_prejuizo}."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"