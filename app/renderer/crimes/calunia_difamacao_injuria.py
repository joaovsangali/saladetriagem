from app.renderer.common import clean, format_date_br


def render_calunia_difamacao_injuria(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    data_fato = clean(answers.get("data_fato"))
    meio = clean(answers.get("meio"))
    conteudo = clean(answers.get("conteudo"))
    onde_ocorreu = clean(answers.get("onde_ocorreu"))
    autores = answers.get("autores") or []
    testemunhas = answers.get("testemunhas") or []

    def _format_autores(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            nome_autor = clean(item.get("nome"))
            contato_autor = clean(item.get("contato"))
            rg_autor = clean(item.get("rg"))
            endereco_autor = clean(item.get("endereco"))

            dados = []
            if nome_autor:
                dados.append(nome_autor)
            if contato_autor:
                dados.append(f"contato {contato_autor}")
            if rg_autor:
                dados.append(f"RG/documento {rg_autor}")
            if endereco_autor:
                dados.append(f"endereço {endereco_autor}")

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

    texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar fato relacionado a calúnia, difamação ou injúria."

    corpo = f"{nome}, declarante, informa"

    contexto_inicial = []
    if data_fato:
        contexto_inicial.append(f"no dia {format_date_br(data_fato)}")
    if meio:
        contexto_inicial.append(f"que a ofensa foi praticada por meio de {meio}")

    if contexto_inicial:
        corpo += " que " + ", ".join(contexto_inicial)
    corpo += "."

    if autores_txt:
        corpo += f" Que os fatos teriam sido praticados por {autores_txt}."

    if conteudo:
        corpo += f" Que o conteúdo da ofensa/alegação foi: {conteudo}."

    if onde_ocorreu:
        corpo += f" Que o fato ocorreu/foi publicado em: {onde_ocorreu}."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"