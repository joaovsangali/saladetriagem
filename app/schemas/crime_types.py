CRIME_SCHEMAS = {
    "roubo": {
        "label": "Roubo",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada do fato", "type": "text", "required": False},
            {"id": "local_fato", "label": "Local onde ocorreu o fato", "type": "text", "required": False},
            {"id": "autores_desc", "label": "Descrição dos autores (quantidade, vestimentas, aparência)", "type": "text", "required": False},
            {"id": "meio_utilizado", "label": "Meio utilizado (arma de fogo, faca, outro)", "type": "select", "options": ["Arma de fogo", "Arma branca (faca/canivete)", "Sem arma (força física)", "Outro"], "required": False},
            {"id": "bens_subtraidos", "label": "Bens subtraídos (descreva)", "type": "text", "required": False},
            {"id": "valor_estimado", "label": "Valor estimado dos bens (R$)", "type": "number", "required": False},
            {"id": "veiculo_fuga", "label": "Houve veículo de fuga? Descreva (cor, modelo, placa)", "type": "text", "required": False},
            {"id": "lesoes", "label": "Houve lesões corporais?", "type": "boolean", "required": False},
            {"id": "testemunhas", "label": "Há testemunhas? Nomes/contatos", "type": "text", "required": False},
        ]
    },
    "furto": {
        "label": "Furto",
        "questions": [
            {"id": "data_fato", "label": "Data do fato (ou período estimado)", "type": "date", "required": False},
            {"id": "local_fato", "label": "Local onde ocorreu o fato", "type": "text", "required": False},
            {"id": "bens_subtraidos", "label": "Bens subtraídos (descreva)", "type": "text", "required": False},
            {"id": "valor_estimado", "label": "Valor estimado dos bens (R$)", "type": "number", "required": False},
            {"id": "forma_acesso", "label": "Como o autor teve acesso? (arrombamento, chave falsa, etc.)", "type": "text", "required": False},
            {"id": "suspeitos", "label": "Há suspeitos? Descreva", "type": "text", "required": False},
            {"id": "testemunhas", "label": "Há testemunhas?", "type": "text", "required": False},
            {"id": "cameras", "label": "Há câmeras de segurança no local?", "type": "boolean", "required": False},
        ]
    },
    "estelionato": {
        "label": "Estelionato",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "modalidade", "label": "Modalidade do estelionato", "type": "select", "options": ["Falso vendedor/produto", "Falso funcionário público", "Golpe do PIX/transferência", "Empréstimo não devolvido", "Cheque sem fundo", "Romance/namoro virtual", "Outro"], "required": False},
            {"id": "descricao_golpe", "label": "Descreva como ocorreu o golpe", "type": "text", "required": False},
            {"id": "valor_prejuizo", "label": "Valor do prejuízo (R$)", "type": "number", "required": False},
            {"id": "meio_contato", "label": "Como o autor entrou em contato? (telefone, internet, pessoalmente)", "type": "text", "required": False},
            {"id": "identificacao_autor", "label": "Como o autor se identificou?", "type": "text", "required": False},
            {"id": "docs_provas", "label": "Possui documentos ou prints como prova?", "type": "boolean", "required": False},
            {"id": "conta_bancaria", "label": "Houve transação bancária? Informe banco e tipo (PIX/TED/outro)", "type": "text", "required": False},
        ]
    },
    "lesao_corporal": {
        "label": "Lesão Corporal",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada", "type": "text", "required": False},
            {"id": "local_fato", "label": "Local do fato", "type": "text", "required": False},
            {"id": "relacao_autor", "label": "Qual a relação com o autor? (desconhecido, familiar, colega)", "type": "text", "required": False},
            {"id": "desc_autor", "label": "Descrição do autor (nome, se conhecido)", "type": "text", "required": False},
            {"id": "tipo_lesao", "label": "Tipo de lesão sofrida", "type": "select", "options": ["Socos/tapas", "Chutes", "Objeto contundente", "Arma branca", "Arma de fogo", "Outro"], "required": False},
            {"id": "regiao_corpo", "label": "Região do corpo afetada", "type": "text", "required": False},
            {"id": "atendimento_medico", "label": "Houve atendimento médico?", "type": "boolean", "required": False},
            {"id": "testemunhas", "label": "Há testemunhas?", "type": "text", "required": False},
            {"id": "historico_violencia", "label": "É a primeira ocorrência ou há histórico?", "type": "select", "options": ["Primeira vez", "Episódio repetido", "Há medida protetiva anterior"], "required": False},
        ]
    },
    "maria_da_penha": {
        "label": "Maria da Penha / Violência Doméstica",
        "questions": [
            {"id": "data_fato", "label": "Data do último episódio", "type": "date", "required": False},
            {"id": "tipo_violencia", "label": "Tipo de violência sofrida", "type": "select", "options": ["Física", "Psicológica", "Moral", "Sexual", "Patrimonial", "Múltiplos tipos"], "required": False},
            {"id": "relacao_agressor", "label": "Relação com o agressor", "type": "select", "options": ["Cônjuge/companheiro(a)", "Ex-cônjuge/ex-companheiro(a)", "Namorado(a)/ex-namorado(a)", "Familiar (pai, irmão, filho)", "Outro"], "required": False},
            {"id": "filhos_envolvidos", "label": "Há filhos menores envolvidos?", "type": "boolean", "required": False},
            {"id": "medida_protetiva", "label": "Já possui medida protetiva?", "type": "boolean", "required": False},
            {"id": "descricao_episodio", "label": "Descreva o último episódio", "type": "text", "required": False},
            {"id": "historico", "label": "Há quanto tempo sofre violência? Descreva histórico", "type": "text", "required": False},
            {"id": "reside_agressor", "label": "Reside com o agressor?", "type": "boolean", "required": False},
            {"id": "atendimento_medico", "label": "Houve necessidade de atendimento médico?", "type": "boolean", "required": False},
            {"id": "testemunhas", "label": "Há testemunhas dos episódios?", "type": "text", "required": False},
        ]
    },
    "ameaca": {
        "label": "Ameaça",
        "questions": [
            {"id": "data_fato", "label": "Data da ameaça", "type": "date", "required": False},
            {"id": "meio_ameaca", "label": "Como a ameaça foi realizada?", "type": "select", "options": ["Pessoalmente", "Por telefone", "Por mensagem/app", "Por terceiros", "Outro"], "required": False},
            {"id": "conteudo_ameaca", "label": "Qual o conteúdo da ameaça?", "type": "text", "required": False},
            {"id": "relacao_autor", "label": "Relação com o autor da ameaça", "type": "text", "required": False},
            {"id": "contexto", "label": "Contexto/motivo da ameaça", "type": "text", "required": False},
            {"id": "provas", "label": "Há provas (prints, gravações)?", "type": "boolean", "required": False},
            {"id": "medida_protetiva", "label": "Já possui medida protetiva?", "type": "boolean", "required": False},
            {"id": "testemunhas", "label": "Há testemunhas?", "type": "text", "required": False},
        ]
    },
    "dano": {
        "label": "Dano ao Patrimônio",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "bem_danificado", "label": "Bem danificado (descreva)", "type": "text", "required": False},
            {"id": "local_fato", "label": "Local onde estava o bem", "type": "text", "required": False},
            {"id": "forma_dano", "label": "Como o dano foi causado?", "type": "text", "required": False},
            {"id": "valor_prejuizo", "label": "Valor estimado do prejuízo (R$)", "type": "number", "required": False},
            {"id": "suspeitos", "label": "Há suspeitos? Descreva", "type": "text", "required": False},
            {"id": "motivacao", "label": "Motivação provável", "type": "text", "required": False},
            {"id": "cameras", "label": "Há câmeras de segurança?", "type": "boolean", "required": False},
        ]
    },
    "outros": {
        "label": "Outros",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "local_fato", "label": "Local do fato", "type": "text", "required": False},
            {"id": "descricao", "label": "Descreva o fato ocorrido", "type": "text", "required": False},
            {"id": "partes_envolvidas", "label": "Partes envolvidas", "type": "text", "required": False},
            {"id": "prejuizo", "label": "Houve prejuízo material? Valor estimado (R$)", "type": "number", "required": False},
            {"id": "testemunhas", "label": "Há testemunhas?", "type": "text", "required": False},
        ]
    },
}

DEFAULT_FORM_SCHEMA = {
    "crime_types": list(CRIME_SCHEMAS.keys()),
    "enabled_fields": {
        "nome": True,
        "nascimento": True,
        "rg": True,
        "cpf": True,
        "endereco": True,
        "relato": True,
        "fotos": True,
    },
    "limits": {
        "max_photos": 3,
        "max_photo_size_mb": 3,
    },
    "questions_by_crime": {k: v["questions"] for k, v in CRIME_SCHEMAS.items()},
}
