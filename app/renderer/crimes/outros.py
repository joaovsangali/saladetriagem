
from app.renderer.common import clean, format_date_br


def render_outros(submission, crime_label: str) -> str:
    answers = submission.answers or {}

    nome = submission.guest_name or "a parte declarante"
    data_fato = clean(answers.get("data_fato"))
    local_fato = clean(answers.get("local_fato"))
    descricao = clean(answers.get("descricao"))
    partes_envolvidas = answers.get("partes_envolvidas") or []
    testemunhas = answers.get("testemunhas") or []

    def _format_partes(items: list) -> str:
        partes = []

        for item in items:
            if not isinstance(item, dict):
                continue

            nome_parte = clean(item.get("nome"))
            contato_parte = clean(item.get("contato"))
            rg_parte = clean(item.get("rg"))
            endereco_parte = clean(item.get("endereco"))

            dados = []
            if nome_parte:
                dados.append(nome_parte)
            if contato_parte:
                dados.append(f"contato {contato_parte}")
            if rg_parte:
                dados.append(f"RG/documento {rg_parte}")
            if endereco_parte:
                dados.append(f"endereço {endereco_parte}")

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

    partes_txt = _format_partes(partes_envolvidas)
    testemunhas_txt = _format_testemunhas(testemunhas)

    texto = f"Comparece nesta delegacia de polícia, {nome} para noticiar fato diverso."

    corpo = f"{nome}, declarante, informa"

    contexto = []
    if data_fato:
        contexto.append(f"no dia {format_date_br(data_fato)}")
    if local_fato:
        contexto.append(f"no local {local_fato}")

    if contexto:
        corpo += " que " + ", ".join(contexto)
    corpo += ", ocorreu o fato ora comunicado."

    if descricao:
        corpo += f" Que o fato foi assim descrito: {descricao}."

    if partes_txt:
        corpo += f" Que as partes envolvidas informadas são: {partes_txt}."

    if testemunhas_txt:
        corpo += f" Que o fato foi testemunhado por: {testemunhas_txt}."

    if submission.narrative:
        corpo += f" Que, ademais, o(a) declarante disse que: {submission.narrative}."

    return f"{texto}\n\n{corpo}"