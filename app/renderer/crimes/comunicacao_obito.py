from app.renderer.common import clean, format_date_br, format_declarant_id


def render_comunicacao_obito(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    declarant = format_declarant_id(submission)
    comunicante = clean(answers.get("comunicante"))
    data_obito = clean(answers.get("data_obito"))
    local_obito = clean(answers.get("local_obito"))
    circunstancias = clean(answers.get("circunstancias"))
    servico_saude = answers.get("servico_saude")
    identificacao = answers.get("identificacao") or []

    def _format_falecido(items: list) -> str:
        if not items:
            return ""

        item = items[0] if isinstance(items[0], dict) else {}
        nome_falecido = clean(item.get("nome"))
        rg_falecido = clean(item.get("rg"))
        cpf_falecido = clean(item.get("cpf"))
        endereco_falecido = clean(item.get("endereco"))

        dados = []
        if nome_falecido:
            dados.append(nome_falecido)
        if endereco_falecido:
            dados.append(f"endereço {endereco_falecido}")

        return ", ".join(dados)

    falecido_txt = _format_falecido(identificacao)

    texto = f"Comparece nesta delegacia de polícia, {declarant} para comunicar ocorrência de óbito."

    corpo = f"{nome}, declarante, informa"

    if comunicante:
        corpo += f" que possui o seguinte vínculo com o(a) falecido(a): {comunicante}."
    else:
        corpo += "."

    if falecido_txt:
        corpo += f" Que a pessoa falecida foi identificada como: {falecido_txt}."

    contexto_obito = []
    if data_obito:
        contexto_obito.append(f"na data de {format_date_br(data_obito)}")
    if local_obito:
        contexto_obito.append(f"no local {local_obito}")

    if contexto_obito:
        corpo += f" Que o óbito ocorreu {' '.join(contexto_obito)}."

    if circunstancias:
        corpo += f" Que as circunstâncias informadas do óbito são: {circunstancias}."

    if servico_saude is True:
        corpo += " Que houve atendimento ou serviço de saúde envolvido."
    elif servico_saude is False:
        corpo += " Que não houve atendimento ou serviço de saúde envolvido."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"