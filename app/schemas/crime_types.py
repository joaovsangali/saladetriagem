# app/schemas/crime_types.py
#
# Mudanças mínimas:
# 1) Adiciona "domain" e "schema_version" no DEFAULT_FORM_SCHEMA
# 2) Adiciona "crime_labels" no DEFAULT_FORM_SCHEMA
# 3) Substitui/atualiza CRIME_SCHEMAS para refletir a NOVA lista de ocorrências (mantendo o formato atual)
#
# Observação: por enquanto, só estamos definindo labels + questions.
# Templates de texto e validators/regex por tipo virão depois.

CRIME_SCHEMAS = {
    "acidente_transito": {
        "label": "Acidente de Trânsito",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada", "type": "text", "required": False},
            {"id": "local_fato", "label": "Local do fato", "type": "text", "required": False},
            {
                "id": "veiculos",
                "label": "Veículos envolvidos",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar veículo",
                "fields": [
                    {
                        "id": "descricao",
                        "label": "Modelo do veículo",
                        "type": "text",
                        "required": False,
                        "maxlength": 300
                    },
                    {
                        "id": "placa",
                        "label": "Placa",
                        "type": "text",
                        "required": False,
                        "maxlength": 20
                    },
                    {
                        "id": "condutor_nome",
                        "label": "Nome do condutor",
                        "type": "text",
                        "required": False,
                        "maxlength": 200
                    },
                    {
                        "id": "condutor_rg",
                        "label": "RG/Documento do condutor",
                        "type": "text",
                        "required": False,
                        "maxlength": 30
                    },
                    {
                        "id": "condutor_contato",
                        "label": "Telefone do condutor",
                        "type": "text",
                        "required": False,
                        "maxlength": 30
                    },
                    {
                        "id": "condutor_endereco",
                        "label": "Endereço do condutor",
                        "type": "text",
                        "required": False,
                        "maxlength": 400
                    },
                    {
                        "id": "seguro",
                        "label": "Há seguro envolvido neste veículo?",
                        "type": "boolean",
                        "required": False
                    },
                    {
                        "id": "seguro_nome",
                        "label": "Qual seguro?",
                        "type": "text",
                        "required": False,
                        "maxlength": 200,
                        "show_if": {
                            "field": "seguro",
                            "value": "sim"
                        }
                    },
                ],
            },
            {"id": "feridos", "label": "Houve feridos?", "type": "boolean", "required": False},
            {"id": "danos", "label": "Danos materiais (descreva)", "type": "text", "required": False},
            {
            "id": "testemunhas",
            "label": "Testemunhas do acidente",
            "type": "group",
            "max_items": 5,
            "add_label": "Adicionar",
            "fields": [
                {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
            ],
            },
        ],
    },
    "adulteracao_sinal_identificador": {
        "label": "Adulteração de Sinal Identificador de Veículo",
        "questions": [
            {"id": "data_fato", "label": "Data do fato/abordagem", "type": "date", "required": False},
            {"id": "local_fato", "label": "Local", "type": "text", "required": False},
            {"id": "placa", "label": "Placa do veículo", "type": "text", "required": False},
            {"id": "marca_modelo", "label": "Marca/Modelo", "type": "text", "required": False},
            {"id": "cor", "label": "Cor", "type": "text", "required": False},
            {"id": "sinais", "label": "Quais sinais aparentam adulteração? (chassi, motor, placas, etiquetas)", "type": "text", "required": False},
            {
            "id": "Autor",
            "label": "Autor(es)",
            "type": "group",
            "max_items": 5,
            "add_label": "Adicionar",
            "fields": [
                {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
            ],
            },            
            {"id": "documentos", "label": "Apresentou documentos do veículo?", "type": "boolean", "required": False},
            {
            "id": "testemunhas",
            "label": "Testemunhas",
            "type": "group",
            "max_items": 5,
            "add_label": "Adicionar",
            "fields": [
                {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
            ],
            },
        ],
    },
    "ameaca": {
        "label": "Ameaça",
        "questions": [
            {"id": "data_fato", "label": "Data da ameaça", "type": "date", "required": False},
            {"id": "meio_ameaca", "label": "Como a ameaça foi realizada?", "type": "select", "options": ["Pessoalmente", "Por telefone", "Por mensagem/app", "Por terceiros", "Outro"], "required": False},
            {"id": "conteudo_ameaca", "label": "Qual o conteúdo da ameaça?", "type": "text", "required": False},
            {
            "id": "autores",
            "label": "Autor(es) da ameaça",
            "type": "group",
            "max_items": 5,
            "add_label": "Adicionar",
            "fields": [
                {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
            ],
            },
            {"id": "relacao_autor", "label": "Relação com o autor da ameaça", "type": "text", "required": False},
            {"id": "contexto", "label": "Contexto/motivo da ameaça", "type": "text", "required": False},
            {"id": "medida_protetiva", "label": "Já possui medida protetiva?", "type": "boolean", "required": False},
            {
            "id": "testemunhas",
            "label": "Testemunhas da ameaça",
            "type": "group",
            "max_items": 5,
            "add_label": "Adicionar",
            "fields": [
                {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
            ],
            },
        ],
    },
    "calunia_difamacao_injuria": {
        "label": "Calúnia/Difamação/Injúria",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "meio", "label": "Meio utilizado (presencial, rede social, mensagem, etc.)", "type": "text", "required": False},
            {"id": "conteudo", "label": "Conteúdo/ofensa/alegação (descreva)", "type": "text", "required": False},
            {
            "id": "autores",
            "label": "Autor(es)",
            "type": "group",
            "max_items": 5,
            "add_label": "Adicionar",
            "fields": [
                {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
            ],
            },
            {
            "id": "testemunhas",
            "label": "Testemunhas",
            "type": "group",
            "max_items": 5,
            "add_label": "Adicionar",
            "fields": [
                {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
            ],
            },            
            {"id": "onde_ocorreu", "label": "Onde ocorreu/foi publicado? (perfil, grupo, local)", "type": "text", "required": False},
        ],
    },
    "comunicacao_obito": {
        "label": "Comunicação de Óbito",
        "questions": [
            {"id": "comunicante", "label": "Grau de parentesco com falecido(a)", "type": "text", "required": False},
            {"id": "data_obito", "label": "Data do óbito (se souber)", "type": "date", "required": False},
            {"id": "local_obito", "label": "Local do óbito", "type": "text", "required": False},
            {
            "id": "identificacao",
            "label": "Identificação do(a) falecido(a)",
            "type": "group",
            "max_items": 1,
            "add_label": "Adicionar",
            "fields": [
                {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                {"id": "cpf", "label": "CPF", "type": "text", "required": False, "maxlength": 30},
                {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
            ],
            },               
            {"id": "circunstancias", "label": "Circunstâncias (natural/causas aparentes, se souber)", "type": "text", "required": False},
            {"id": "servico_saude", "label": "Houve atendimento/serviço de saúde envolvido?", "type": "boolean", "required": False},
        ],
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
        ],
    },
    "desaparecimento_encontro_pessoas": {
        "label": "Desaparecimento/Encontro de pessoas",
        "questions": [
            {"id": "tipo", "label": "Tipo", "type": "select", "options": ["Desaparecimento", "Encontro/Localização"], "required": False},
            {"id": "data", "label": "Data do desaparecimento/encontro", "type": "date", "required": False},
            {"id": "hora", "label": "Hora aproximada", "type": "text", "required": False},
            {"id": "local", "label": "Local (última vez visto / local do encontro)", "type": "text", "required": False},
            {"id": "pessoa", "label": "Pessoa (nome, idade, características)", "type": "text", "required": False},
            {"id": "roupas", "label": "Roupas/itens quando visto pela última vez", "type": "text", "required": False},
            {"id": "contato_familia", "label": "Contato de familiar/responsável", "type": "text", "required": False},
            {"id": "observacoes", "label": "Observações relevantes", "type": "text", "required": False},
        ],
    },
    "embriaguez_volante": {
        "label": "Embriaguez no Volante",
        "questions": [
            {"id": "data_fato", "label": "Data do fato/abordagem", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada", "type": "text", "required": False},
            {"id": "local_fato", "label": "Local", "type": "text", "required": False},
            {"id": "veiculo", "label": "Veículo (marca/modelo/cor/placa)", "type": "text", "required": False},
            {"id": "condutor", "label": "Condutor (nome/documento, se souber)", "type": "text", "required": False},
            {"id": "sinais", "label": "Sinais de embriaguez observados", "type": "text", "required": False},
            {"id": "teste_etilometro", "label": "Realizou teste do etilômetro?", "type": "boolean", "required": False},
            {"id": "resultado", "label": "Resultado (se houver)", "type": "text", "required": False},
            {"id": "testemunhas", "label": "Testemunhas/contatos", "type": "text", "required": False},
        ],
    },
    "estelionato_golpe": {
        "label": "Estelionato (Golpe)",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "modalidade", "label": "Modalidade do golpe", "type": "select", "options": ["Falso vendedor/produto", "Falso funcionário público", "Golpe do PIX/transferência", "Empréstimo não devolvido", "Cheque sem fundo", "Romance/namoro virtual", "Outro"], "required": False},
            {"id": "descricao_golpe", "label": "Descreva como ocorreu o golpe", "type": "text", "required": False},
            {"id": "valor_prejuizo", "label": "Valor do prejuízo (R$)", "type": "number", "required": False},
            {"id": "meio_contato", "label": "Como o autor entrou em contato?", "type": "text", "required": False},
            {"id": "identificacao_autor", "label": "Como o autor se identificou?", "type": "text", "required": False},
            {"id": "docs_provas", "label": "Possui documentos/prints como prova?", "type": "boolean", "required": False},
            {"id": "conta_bancaria", "label": "Transação bancária (banco e tipo PIX/TED/outro)", "type": "text", "required": False},
        ],
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
        ],
    },
    "maria_da_penha": {
        "label": "Violência Doméstica (Maria da Penha)",
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
        ],
    },
    "perda_documentos": {
        "label": "Perda de Documentos",
        "questions": [
            {"id": "data", "label": "Data/período aproximado", "type": "date", "required": False},
            {"id": "local", "label": "Local provável da perda", "type": "text", "required": False},
            {"id": "documentos", "label": "Quais documentos foram perdidos? (descreva)", "type": "text", "required": False},
            {"id": "suspeita_furto", "label": "Há suspeita de furto/roubo?", "type": "boolean", "required": False},
            {"id": "observacoes", "label": "Observações relevantes", "type": "text", "required": False},
        ],
    },
    "porte_ilegal_arma_fogo": {
        "label": "Porte Ilegal de Arma de Fogo",
        "questions": [
            {"id": "data_fato", "label": "Data do fato/abordagem", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada", "type": "text", "required": False},
            {"id": "local_fato", "label": "Local", "type": "text", "required": False},
            {"id": "arma", "label": "Arma (tipo, marca, calibre, numeração, se souber)", "type": "text", "required": False},
            {"id": "municao", "label": "Munição (quantidade, calibre, se souber)", "type": "text", "required": False},
            {"id": "posse", "label": "Quem portava/possuía (nome/descrição)", "type": "text", "required": False},
            {"id": "documentacao", "label": "Havia documentação/registro da arma?", "type": "boolean", "required": False},
            {"id": "testemunhas", "label": "Testemunhas/contatos", "type": "text", "required": False},
        ],
    },
    "roubo_furto": {
        "label": "Roubo/Furto",
        "questions": [
            {"id": "modalidade", "label": "Foi roubo ou furto?", "type": "select", "options": ["Roubo", "Furto", "Não sei"], "required": False},
            {"id": "data_fato", "label": "Data do fato (ou período estimado)", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada do fato", "type": "text", "required": False},
            {"id": "local_fato", "label": "Local onde ocorreu o fato", "type": "text", "required": False},
            {"id": "autores_desc", "label": "Descrição dos autores (quantidade, aparência, vestimentas)", "type": "text", "required": False},
            {"id": "meio_utilizado", "label": "Meio utilizado (arma, força, etc.)", "type": "select", "options": ["Arma de fogo", "Arma branca", "Sem arma (força física)", "Arrombamento", "Outro"], "required": False},
            {"id": "bens_subtraidos", "label": "Bens subtraídos (descreva)", "type": "text", "required": False},
            {"id": "valor_estimado", "label": "Valor estimado dos bens (R$)", "type": "number", "required": False},
            {"id": "veiculo_fuga", "label": "Houve veículo de fuga? (cor, modelo, placa)", "type": "text", "required": False},
            {"id": "testemunhas", "label": "Testemunhas (nomes/contatos)", "type": "text", "required": False},
            {"id": "cameras", "label": "Há câmeras de segurança no local?", "type": "boolean", "required": False},
            {"id": "observacoes", "label": "Outras informações relevantes", "type": "text", "required": False},
        ],
    },
    "trafico_drogas": {
        "label": "Tráfico de Drogas",
        "questions": [
            {"id": "data_fato", "label": "Data do fato/denúncia/abordagem", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada", "type": "text", "required": False},
            {"id": "local_fato", "label": "Local", "type": "text", "required": False},
            {"id": "descricao", "label": "Descrição do fato (o que foi visto/ocorreu)", "type": "text", "required": False},
            {"id": "suspeitos", "label": "Suspeitos (descrição/nomes, se souber)", "type": "text", "required": False},
            {"id": "drogas", "label": "Substâncias/quantidades (se souber)", "type": "text", "required": False},
            {"id": "testemunhas", "label": "Testemunhas/contatos", "type": "text", "required": False},
            {"id": "cameras", "label": "Há câmeras de segurança?", "type": "boolean", "required": False},
        ],
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
        ],
    },
}

DEFAULT_FORM_SCHEMA = {
    # Campos opcionais "future-proof"
    "domain": "police",
    "schema_version": 1,

    "crime_types": list(CRIME_SCHEMAS.keys()),
    "crime_labels": {k: v.get("label", k) for k, v in CRIME_SCHEMAS.items()},

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