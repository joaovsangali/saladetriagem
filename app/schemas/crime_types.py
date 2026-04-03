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
            {"id": "hora_fato", "label": "Hora aproximada", "type": "time", "required": False},
            {"id": "local_fato", "label": "Local do fato", "type": "text", "required": False},
            {
                "id": "veiculos",
                "label": "Veículos envolvidos",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "fields": [
                    {
                        "id": "tipo_veiculo",
                        "label": "Tipo do veículo",
                        "type": "radio",
                        "required": False,
                        "options": ["Carro", "Moto", "Outros"]
                    },
                    {
                        "id": "descricao",
                        "label": "Marca/Modelo",
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
                        "id": "cor",
                        "label": "Cor",
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
            "max_items": 2,
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
            "max_items": 2,
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
            {"id": "meio_ameaca", "label": "Como a ameaça foi realizada?", "type": "select", "options": ["Pessoalmente", "Por telefone", "Por mensagem/app", "Por rede social", "Por terceiros", "Outro"], "required": False},
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
            {"id": "conteudo_ameaca", "label": "Como o(a) autor(a) lhe ameaçou?", "type": "text", "required": False},
            {"id": "relacao_autor", "label": "Relação com o autor da ameaça", "type": "text", "required": False},
            {"id": "medida_protetiva", "label": "Já possui medida protetiva?", "type": "boolean", "required": False},
            {
            "id": "testemunhas",
            "label": "Testemunhas da ameaça",
            "type": "group",
            "max_items": 2,
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
            {"id": "meio", "label": "Meio utilizado (presencial, rede social, mensagem, etc.)", "type": "select", "options": ["Pessoalmente", "Por telefone", "Por mensagem/app", "Por rede social", "Por terceiros", "Outro"], "required": False},
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
            "max_items": 2,
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
            {"id": "local_fato", "label": "Local do fato", "type": "text", "required": False},
            {
                "id": "tipo_patrimonio",
                "label": "Tipo de patrimônio",
                "type": "select",
                "options": ["Patrimônio Público", "Patrimônio Privado"],
                "required": False
            },
            {
                "id": "bens_danificados",
                "label": "Bens danificados",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "fields": [
                    {
                        "id": "descricao",
                        "label": "Qual bem foi danificado?",
                        "type": "text",
                        "required": False,
                        "maxlength": 300
                    }
                ],
            },
            {"id": "forma_dano", "label": "Como o dano foi causado?", "type": "text", "required": False},
            {"id": "valor_prejuizo", "label": "Valor estimado do prejuízo (R$)", "type": "number", "required": False},
            {
                "id": "autor",
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
            {"id": "motivacao", "label": "Motivação provável", "type": "text", "required": False},
            {
                "id": "cameras",
                "label": "Há câmeras de segurança?",
                "type": "select",
                "options": ["Sim", "Não", "Não sei"],
                "required": False
            },
            {
                "id": "testemunhas",
                "label": "Testemunhas",
                "type": "group",
                "max_items": 2,
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
    "desaparecimento_encontro_pessoas": {
        "label": "Desaparecimento/Encontro de pessoas",
        "questions": [
            {
                "id": "tipo",
                "label": "Tipo",
                "type": "select",
                "options": ["Desaparecimento", "Encontro/Localização"],
                "required": False
            },
            {
                "id": "data_desaparecimento",
                "label": "Data do desaparecimento",
                "type": "date",
                "required": False,
                "show_if": {"field": "tipo", "value": "Desaparecimento"}
            },
            {
                "id": "hora_desaparecimento",
                "label": "Hora aproximada",
                "type": "text",
                "required": False,
                "show_if": {"field": "tipo", "value": "Desaparecimento"}
            },
            {
                "id": "local_desaparecimento",
                "label": "Local (última vez visto(a))",
                "type": "text",
                "required": False,
                "show_if": {"field": "tipo", "value": "Desaparecimento"}
            },
            {
                "id": "data_encontro",
                "label": "Data do encontro",
                "type": "date",
                "required": False,
                "show_if": {"field": "tipo", "value": "Encontro/Localização"}
            },
            {
                "id": "local_encontro",
                "label": "Local do encontro",
                "type": "text",
                "required": False,
                "show_if": {"field": "tipo", "value": "Encontro/Localização"}
            },
            {
                "id": "pessoa",
                "label": "Pessoa",
                "type": "group",
                "max_items": 1,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {
                "id": "roupas",
                "label": "Foi visto por último usando quais roupas:",
                "type": "text",
                "required": False,
                "show_if": {"field": "tipo", "value": "Desaparecimento"}
            },
            {
                "id": "contato_familia",
                "label": "Contato de familiar/responsável",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
                "show_if": {"field": "tipo", "value": "Desaparecimento"}
            },
        ],
    },
        "embriaguez_volante": {
        "label": "Embriaguez no Volante",
        "questions": [
            {"id": "data_fato", "label": "Data do fato/abordagem", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada", "type": "time", "required": False},
            {"id": "local_fato", "label": "Local", "type": "text", "required": False},
            {
                "id": "veiculos",
                "label": "Veículos",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "tipo_veiculo", "label": "Tipo do veículo", "type": "radio", "required": False, "options": ["Carro", "Moto", "Outros"]},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "modelo", "label": "Modelo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "cor", "label": "Cor", "type": "text", "required": False, "maxlength": 50},
                    {"id": "placa", "label": "Placa", "type": "text", "required": False, "maxlength": 20},
                ],
            },
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
                "id": "sinais",
                "label": "Sinais de embriaguez observados",
                "type": "checkbox_group",
                "options": [
                    "Hálito Etílico",
                    "Olhos Vermelhos",
                    "Dificuldades de Movimentação",
                    "Fala Alterada",
                    "Vestes Desordenadas",
                    "Agressividade",
                    "Exaltação ou Arrogância",
                    "Sonolência",
                    "Dispersão",
                    "Desorientação"
                ],
                "required": False
            },            
            {"id": "teste_etilometro", "label": "Realizou teste do etilômetro?", "type": "boolean", "required": False},
            {
                "id": "resultado",
                "label": "Resultado do etilômetro (mg/L)",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "teste_etilometro",
                    "value": "sim"
                }
            },            
            {
                "id": "testemunhas",
                "label": "Testemunhas",
                "type": "group",
                "max_items": 2,
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
    "estelionato_golpe": {
        "label": "Estelionato (Golpe)",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "local_fato", "label": "Local do fato", "type": "text", "required": False},
            {
                "id": "modalidade",
                "label": "Modalidade do golpe",
                "type": "select",
                "options": [
                    "Falso vendedor/produto",
                    "Falso funcionário",
                    "Falso profissional",
                    "Falso familiar/amigo",
                    "Romance/namoro virtual",
                    "Outro"
                ],
                "required": False
            },
            {
                "id": "modalidade_outro",
                "label": "Descreva:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "modalidade",
                    "value": "Outro"
                }
            },
            {
                "id": "meio_contato",
                "label": "Como o autor entrou em contato?",
                "type": "select",
                "options": [
                    "E-mail",
                    "Facebook",
                    "Instagram",
                    "Outros",
                    "Presencialmente",
                    "Telegram",
                    "Telefone",
                    "Website",
                    "WhatsApp"
                ],
                "required": False
            },
            {
                "id": "meio_contato_email",
                "label": "Informe o endereço de e-mail:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "meio_contato",
                    "value": "E-mail"
                }
            },
            {
                "id": "meio_contato_facebook",
                "label": "Informe o link, usuário ou perfil do Facebook:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "meio_contato",
                    "value": "Facebook"
                }
            },
            {
                "id": "meio_contato_instagram",
                "label": "Informe o link, usuário ou perfil do Instagram:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "meio_contato",
                    "value": "Instagram"
                }
            },
            {
                "id": "meio_contato_outros",
                "label": "Descreva o meio de contato e informe o dado pertinente:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "meio_contato",
                    "value": "Outros"
                }
            },
            {
                "id": "meio_contato_presencialmente",
                "label": "Informe onde ocorreu o contato presencial:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "meio_contato",
                    "value": "Presencialmente"
                }
            },
            {
                "id": "meio_contato_telegram",
                "label": "Informe o link, usuário ou número do Telegram:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "meio_contato",
                    "value": "Telegram"
                }
            },
            {
                "id": "meio_contato_telefone",
                "label": "Informe o número de telefone:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "meio_contato",
                    "value": "Telefone"
                }
            },
            {
                "id": "meio_contato_website",
                "label": "Informe o link do website:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "meio_contato",
                    "value": "Website"
                }
            },
            {
                "id": "meio_contato_whatsapp",
                "label": "Informe o número ou link do WhatsApp:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "meio_contato",
                    "value": "WhatsApp"
                }
            },
            {
                "id": "autores",
                "label": "Autor(es) (como o autor se identificou)",
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
                "label": "Testemunha(s)",
                "type": "group",
                "max_items": 2,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {
                "id": "houve_transferencia",
                "label": "Houve transferência bancária, PIX ou pagamento?",
                "type": "boolean",
                "required": False
            },
            {
                "id": "transferencias",
                "label": "Transferências/Pagamentos",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {
                    "field": "houve_transferencia",
                    "value": "sim"
                },
                "fields": [
                    {"id": "banco", "label": "Nome do Banco", "type": "text", "required": False, "maxlength": 100},
                    {"id": "conta", "label": "Conta", "type": "text", "required": False, "maxlength": 50},
                    {"id": "agencia", "label": "Agência", "type": "text", "required": False, "maxlength": 50},
                    {"id": "número pix", "label": "PIX", "type": "text", "required": False, "maxlength": 150},
                    {"id": "beneficiario", "label": "Nome do Beneficiário", "type": "text", "required": False, "maxlength": 200},
                ],
            },
            {
                "id": "valor_prejuizo",
                "label": "Valor do prejuízo total (R$)",
                "type": "number",
                "required": False
            },
        ],
    },
    "lesao_corporal": {
        "label": "Lesão Corporal",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada", "type": "time", "required": False},
            {"id": "local_fato", "label": "Local do fato", "type": "text", "required": False},
            {
                "id": "relacao_autor",
                "label": "Qual a relação com o autor?",
                "type": "select",
                "options": [
                    "Amigo(a)",
                    "Desconhecido",
                    "Ex-relacionamento",
                    "Familiar",
                    "Marido/Esposa",
                    "Namorado(a)",
                    "Vizinho(a)",
                    "Outros"
                ],
                "required": False
            },
            {
                "id": "relacao_autor_outros",
                "label": "Descreva:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "relacao_autor",
                    "value": "Outros"
                }
            },
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
                "id": "tipo_lesao",
                "label": "Tipo de lesão sofrida",
                "type": "checkbox_group",
                "options": [
                    "Arma branca",
                    "Arma de fogo",
                    "Chutes",
                    "Objeto contundente",
                    "Socos",
                    "Tapas",
                    "outros"
                ],
                "required": False
            },
            {"id": "regiao_corpo", "label": "Região do corpo afetada", "type": "text", "required": False},
            {
                "id": "atendimento_medico",
                "label": "Houve atendimento médico?",
                "type": "boolean",
                "required": False
            },
            {
                "id": "local_atendimento_medico",
                "label": "Informe o nome da UBS, PS, UPA, Hospital, Clínica etc.",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "atendimento_medico",
                    "value": "sim"
                }
            },
            {
                "id": "testemunhas",
                "label": "Testemunhas",
                "type": "group",
                "max_items": 2,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {
                "id": "historico_violencia",
                "label": "É a primeira ocorrência ou há histórico?",
                "type": "select",
                "options": [
                    "Primeira vez",
                    "Episódio repetido",
                    "Há medida protetiva anterior"
                ],
                "required": False
            },
        ],
    },
        "maria_da_penha": {
        "label": "Violência Doméstica (Maria da Penha)",
        "questions": [
            {"id": "local_fato", "label": "Local dos fatos", "type": "text", "required": False},
            {"id": "data_fato", "label": "Data dos fatos", "type": "date", "required": False},
            {
                "id": "autores",
                "label": "Autor (agressor)",
                "type": "group",
                "max_items": 1,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {
                "id": "relacao_agressor",
                "label": "Relação com o agressor",
                "type": "select",
                "options": [
                    "Cônjuge/companheiro(a)",
                    "Ex-cônjuge/ex-companheiro(a)",
                    "Namorado(a)/ex-namorado(a)",
                    "Familiar (pai, irmão, filho)",
                    "Outro"
                ],
                "required": False
            },
            {
                "id": "relacao_agressor_outro",
                "label": "Descreva:",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "relacao_agressor",
                    "value": "Outro"
                }
            },
            {
                "id": "tipo_violencia",
                "label": "Tipo de violência sofrida",
                "type": "select",
                "options": [
                    "Física",
                    "Psicológica",
                    "Moral",
                    "Sexual",
                    "Patrimonial",
                    "Múltiplos tipos"
                ],
                "required": False
            },
            {"id": "reside_agressor", "label": "Reside com o agressor?", "type": "boolean", "required": False},
            {"id": "filhos_envolvidos", "label": "Há filhos menores envolvidos?", "type": "boolean", "required": False},
            {
                "id": "atendimento_medico",
                "label": "Houve necessidade de atendimento médico?",
                "type": "boolean",
                "required": False
            },
            {
                "id": "local_atendimento_medico",
                "label": "Informe o nome da UBS, PS, UPA, Hospital, Clínica etc.",
                "type": "text",
                "required": False,
                "show_if": {
                    "field": "atendimento_medico",
                    "value": "sim"
                }
            },
            {
                "id": "testemunhas",
                "label": "Testemunhas",
                "type": "group",
                "max_items": 2,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {"id": "medida_protetiva", "label": "Já possui medida protetiva?", "type": "boolean", "required": False},
            {
                "id": "deseja_medida_protetiva",
                "label": "Deseja pedir medidas protetivas?",
                "type": "boolean",
                "required": False,
                "show_if": {
                    "field": "medida_protetiva",
                    "value": "nao"
                }
            },
        ],
    },
        "violencia_sexual": {
        "label": "Violência Sexual",
        "questions": [
            {
                "id": "vitima_crianca",
                "label": "A vítima é criança ou adolescente (menor de 18 anos)?",
                "type": "boolean",
                "required": False
            },
            {
                "id": "crianca",
                "label": "Criança",
                "type": "group",
                "max_items": 1,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "local_fato", "label": "Local do fato", "type": "text", "required": False},
            {
                "id": "autor",
                "label": "Autor (agressor)",
                "type": "group",
                "max_items": 1,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {
                "id": "relacao_agressor",
                "label": "Relação da vítima com o agressor",
                "type": "select",
                "options": [
                    "Desconhecido",
                    "Cônjuge/companheiro(a)",
                    "Ex-cônjuge/ex-companheiro(a)",
                    "Familiar (pai, irmão, tio, avô)",
                    "Conhecido (vizinho, amigo)",
                    "Outros"
                ],
                "required": False
            },
            {
                "id": "relacao_agressor_outro",
                "label": "Descreva a relação:",
                "type": "text",
                "required": False,
                "maxlength": 200,
                "show_if": {
                    "field": "relacao_agressor",
                    "value": "Outros"
                }
            },
            {"id": "reside_agressor", "label": "O agressor reside com a vítima?", "type": "boolean", "required": False},
            {
                "id": "atendimento_medico",
                "label": "Houve necessidade de atendimento médico?",
                "type": "boolean",
                "required": False
            },
            {
                "id": "local_atendimento_medico",
                "label": "Informe o nome da UBS, PS, UPA, Hospital, Clínica etc.",
                "type": "text",
                "required": False,
                "maxlength": 200,
                "show_if": {
                    "field": "atendimento_medico",
                    "value": "sim"
                }
            },
            {
                "id": "testemunhas",
                "label": "Testemunhas",
                "type": "group",
                "max_items": 2,
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
    "perda_documentos": {
        "label": "Perda de Documentos",
        "questions": [
            {"id": "data", "label": "Data/período aproximado", "type": "date", "required": False},
            {"id": "local", "label": "Local provável da perda", "type": "text", "required": False},
            {
                "id": "documentos",
                "label": "Documentos perdidos",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "fields": [
                    {
                        "id": "tipo_documento",
                        "label": "Tipo de documento",
                        "type": "text",
                        "required": False,
                        "maxlength": 100
                    },
                    {
                        "id": "numero_documento",
                        "label": "Número do documento",
                        "type": "text",
                        "required": False,
                        "maxlength": 50
                    },
                ],
            },
            {"id": "suspeita_furto", "label": "Há suspeita de furto/roubo?", "type": "boolean", "required": False},
            {"id": "observacoes", "label": "Observações relevantes", "type": "text", "required": False},
        ],
    },
    "porte_ilegal_arma_fogo": {
        "label": "Porte Ilegal de Arma de Fogo",
        "questions": [
            {"id": "data_fato", "label": "Data do fato/abordagem", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora do fato/abordagem", "type": "time", "required": False},
            {"id": "local_fato", "label": "Local", "type": "text", "required": False},
            {
                "id": "armas",
                "label": "Armas",
                "type": "group",
                "max_items": 10,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "tipo", "label": "Tipo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "calibre", "label": "Calibre", "type": "text", "required": False, "maxlength": 50},
                    {"id": "numeracao", "label": "Numeração (se souber)", "type": "text", "required": False, "maxlength": 100},
                ],
            },
            {
                "id": "municoes",
                "label": "Munições",
                "type": "group",
                "max_items": 10,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "calibre", "label": "Calibre", "type": "text", "required": False, "maxlength": 50},
                    {"id": "quantidade", "label": "Quantidade", "type": "number", "required": False},
                ],
            },
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
            {"id": "documentacao", "label": "Havia documentação/registro da arma?", "type": "boolean", "required": False},
            {
                "id": "testemunhas",
                "label": "Testemunhas",
                "type": "group",
                "max_items": 2,
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
    "roubo_furto": {
        "label": "Roubo/Furto",
        "questions": [
            {
                "id": "modalidade",
                "label": "Foi roubo ou furto? (Escolha roubo se houve violência ou ameaça)",
                "type": "select",
                "options": ["Roubo", "Furto"],
                "required": False
            },

            # ---------------- ROUBO ----------------
            {
                "id": "roubo_data_fato",
                "label": "Data do fato",
                "type": "date",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_hora_fato",
                "label": "Hora aproximada do fato",
                "type": "text",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_local_fato",
                "label": "Local onde ocorreu o fato",
                "type": "text",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_autores",
                "label": "Autores",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "modalidade", "value": "Roubo"},
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                    {"id": "altura_aproximada", "label": "Altura aproximada", "type": "text", "required": False, "maxlength": 50},
                    {"id": "peso_aproximado", "label": "Peso aproximado", "type": "text", "required": False, "maxlength": 50},
                    {"id": "cor_pele", "label": "Cor da pele", "type": "text", "required": False, "maxlength": 100},
                    {"id": "roupas", "label": "Roupas", "type": "text", "required": False, "maxlength": 300},
                    {"id": "outras_caracteristicas", "label": "Outras características", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {
                "id": "roubo_meio_utilizado",
                "label": "Meio utilizado",
                "type": "select",
                "options": ["Arma branca", "Arma de fogo", "Sem arma (força física)", "Outros"],
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_meio_utilizado_outro",
                "label": "Descreva o meio utilizado:",
                "type": "text",
                "required": False,
                "show_if": {"field": "roubo_meio_utilizado", "value": "Outro"}
            },

            {
                "id": "roubo_houve_cartoes",
                "label": "Foram subtraídos cartões bancários?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_cartoes",
                "label": "Cartões",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "roubo_houve_cartoes", "value": "sim"},
                "fields": [
                    {"id": "banco", "label": "Nome do banco", "type": "text", "required": False, "maxlength": 100},
                    {"id": "tipo_cartao", "label": "Tipo de cartão", "type": "text", "required": False, "maxlength": 100},
                    {"id": "numero_cartao", "label": "Número do cartão", "type": "text", "required": False, "maxlength": 50},
                ],
            },

            {
                "id": "roubo_houve_celular",
                "label": "Foi subtraído celular?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_celulares",
                "label": "Celulares",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "roubo_houve_celular", "value": "sim"},
                "fields": [
                    {"id": "tipo_veiculo", "label": "Tipo do veículo", "type": "radio", "required": False, "options": ["Carro", "Moto", "Outros"]},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "modelo", "label": "Modelo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "numero_telefone", "label": "Número do telefone", "type": "text", "required": False, "maxlength": 30},
                    {"id": "imei", "label": "Número de IMEI", "type": "text", "required": False, "maxlength": 50},
                ],
            },

            {
                "id": "roubo_houve_dinheiro",
                "label": "Foi subtraído dinheiro?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },

            {
                "id": "roubo_houve_joias",
                "label": "Foram subtraídas jóias?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_joias",
                "label": "Jóias",
                "type": "group",
                "max_items": 10,
                "add_label": "Adicionar",
                "show_if": {"field": "roubo_houve_joias", "value": "sim"},
                "fields": [
                    {"id": "tipo_veiculo", "label": "Tipo do veículo", "type": "radio", "required": False, "options": ["Carro", "Moto", "Outros"]},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "metal_pedra", "label": "Metal/pedra preciosa", "type": "text", "required": False, "maxlength": 150},
                ],
            },

            {
                "id": "roubo_houve_veiculo",
                "label": "Foi subtraído veículo?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_veiculos_subtraidos",
                "label": "Veículos subtraídos",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "roubo_houve_veiculo", "value": "sim"},
                "fields": [
                    {"id": "tipo_veiculo", "label": "Tipo do veículo", "type": "radio", "required": False, "options": ["Carro", "Moto", "Outros"]},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "tipo", "label": "Tipo (carro, moto e outros)", "type": "text", "required": False, "maxlength": 100},
                    {"id": "cor", "label": "Cor", "type": "text", "required": False, "maxlength": 50},
                    {"id": "modelo", "label": "Modelo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "placa", "label": "Placa", "type": "text", "required": False, "maxlength": 20},
                ],
            },

            {
                "id": "roubo_houve_outros_bens",
                "label": "Foram subtraídos outros bens?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_outros_bens",
                "label": "Descreva outros bens",
                "type": "text",
                "required": False,
                "show_if": {"field": "roubo_houve_outros_bens", "value": "sim"}
            },

            {
                "id": "roubo_valor_estimado",
                "label": "Valor estimado dos bens (R$)",
                "type": "number",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },
            {
                "id": "roubo_veiculo_fuga",
                "label": "Houve veículo de fuga?",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "modalidade", "value": "Roubo"},
                "fields": [
                    {"id": "tipo_veiculo", "label": "Tipo do veículo", "type": "radio", "required": False, "options": ["Carro", "Moto", "Outros"]},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "tipo", "label": "Tipo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "cor", "label": "Cor", "type": "text", "required": False, "maxlength": 50},
                    {"id": "modelo", "label": "Modelo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "placa", "label": "Placa", "type": "text", "required": False, "maxlength": 20},
                ],
            },
            {
                "id": "roubo_testemunhas",
                "label": "Testemunhas",
                "type": "group",
                "max_items": 2,
                "add_label": "Adicionar",
                "show_if": {"field": "modalidade", "value": "Roubo"},
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {
                "id": "roubo_cameras",
                "label": "Há câmeras de segurança no local?",
                "type": "select",
                "options": ["Sim", "Não", "Não sei"],
                "required": False,
                "show_if": {"field": "modalidade", "value": "Roubo"}
            },

            # ---------------- FURTO ----------------
            {
                "id": "furto_data_fato",
                "label": "Data do fato",
                "type": "date",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
            {
                "id": "furto_hora_fato",
                "label": "Hora aproximada do fato",
                "type": "text",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
            {
                "id": "furto_local_fato",
                "label": "Local onde ocorreu o fato",
                "type": "text",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
            {
                "id": "furto_autores",
                "label": "Autores",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "modalidade", "value": "Furto"},
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                    {"id": "altura_aproximada", "label": "Altura aproximada", "type": "text", "required": False, "maxlength": 50},
                    {"id": "peso_aproximado", "label": "Peso aproximado", "type": "text", "required": False, "maxlength": 50},
                    {"id": "cor_pele", "label": "Cor da pele", "type": "text", "required": False, "maxlength": 100},
                    {"id": "roupas", "label": "Roupas", "type": "text", "required": False, "maxlength": 300},
                    {"id": "outras_caracteristicas", "label": "Outras características", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {
                "id": "furto_meio_utilizado",
                "label": "Meio utilizado",
                "type": "checkbox_group",
                "options": [
                    "Abuso de confiança",
                    "Chave falsa",
                    "Destruição ou rompimento de obstáculo",
                    "Destreza",
                    "Durante repouso noturno",
                    "Escalada",
                    "Fraude",
                    "Uso de chave falsa",
                    "Uso de explosivos"
                ],
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },

            {
                "id": "furto_houve_cartoes",
                "label": "Foram subtraídos cartões?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
            {
                "id": "furto_cartoes",
                "label": "Cartões",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "furto_houve_cartoes", "value": "sim"},
                "fields": [
                    {"id": "banco", "label": "Nome do banco", "type": "text", "required": False, "maxlength": 100},
                    {"id": "tipo_cartao", "label": "Tipo de cartão", "type": "text", "required": False, "maxlength": 100},
                    {"id": "numero_cartao", "label": "Número do cartão", "type": "text", "required": False, "maxlength": 50},
                ],
            },

            {
                "id": "furto_houve_celular",
                "label": "Foi subtraído celular?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
            {
                "id": "furto_celulares",
                "label": "Celulares",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "furto_houve_celular", "value": "sim"},
                "fields": [
                    {"id": "tipo_veiculo", "label": "Tipo do veículo", "type": "radio", "required": False, "options": ["Carro", "Moto", "Outros"]},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "modelo", "label": "Modelo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "numero_telefone", "label": "Número do telefone", "type": "text", "required": False, "maxlength": 30},
                    {"id": "imei", "label": "Número de IMEI", "type": "text", "required": False, "maxlength": 50},
                ],
            },

            {
                "id": "furto_houve_dinheiro",
                "label": "Foi subtraído dinheiro?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },

            {
                "id": "furto_houve_joias",
                "label": "Foram subtraídas jóias?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
            {
                "id": "furto_joias",
                "label": "Jóias",
                "type": "group",
                "max_items": 10,
                "add_label": "Adicionar",
                "show_if": {"field": "furto_houve_joias", "value": "sim"},
                "fields": [
                    {"id": "tipo_veiculo", "label": "Tipo do veículo", "type": "radio", "required": False, "options": ["Carro", "Moto", "Outros"]},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "metal_pedra", "label": "Metal/pedra preciosa", "type": "text", "required": False, "maxlength": 150},
                ],
            },

            {
                "id": "furto_houve_veiculo",
                "label": "Foi subtraído veículo?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
            {
                "id": "furto_veiculos_subtraidos",
                "label": "Veículos subtraídos",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "furto_houve_veiculo", "value": "sim"},
                "fields": [
                    {"id": "tipo_veiculo", "label": "Tipo do veículo", "type": "radio", "required": False, "options": ["Carro", "Moto", "Outros"]},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "tipo", "label": "Tipo (carro, moto e outros)", "type": "text", "required": False, "maxlength": 100},
                    {"id": "cor", "label": "Cor", "type": "text", "required": False, "maxlength": 50},
                    {"id": "modelo", "label": "Modelo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "placa", "label": "Placa", "type": "text", "required": False, "maxlength": 20},
                ],
            },

            {
                "id": "furto_houve_outros_bens",
                "label": "Foram subtraídos outros bens?",
                "type": "boolean",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
            {
                "id": "furto_outros_bens",
                "label": "Descreva outros bens",
                "type": "text",
                "required": False,
                "show_if": {"field": "furto_houve_outros_bens", "value": "sim"}
            },

            {
                "id": "furto_valor_estimado",
                "label": "Valor estimado dos bens (R$)",
                "type": "number",
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
            {
                "id": "furto_veiculo_fuga",
                "label": "Houve veículo de fuga?",
                "type": "group",
                "max_items": 5,
                "add_label": "Adicionar",
                "show_if": {"field": "modalidade", "value": "Furto"},
                "fields": [
                    {"id": "tipo_veiculo", "label": "Tipo do veículo", "type": "radio", "required": False, "options": ["Carro", "Moto", "Outros"]},
                    {"id": "marca", "label": "Marca", "type": "text", "required": False, "maxlength": 100},
                    {"id": "tipo", "label": "Tipo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "cor", "label": "Cor", "type": "text", "required": False, "maxlength": 50},
                    {"id": "modelo", "label": "Modelo", "type": "text", "required": False, "maxlength": 100},
                    {"id": "placa", "label": "Placa", "type": "text", "required": False, "maxlength": 20},
                ],
            },
            {
                "id": "furto_testemunhas",
                "label": "Testemunhas",
                "type": "group",
                "max_items": 2,
                "add_label": "Adicionar",
                "show_if": {"field": "modalidade", "value": "Furto"},
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {
                "id": "furto_cameras",
                "label": "Há câmeras de segurança no local?",
                "type": "select",
                "options": ["Sim", "Não", "Não sei"],
                "required": False,
                "show_if": {"field": "modalidade", "value": "Furto"}
            },
        ],
    },
    "trafico_drogas": {
        "label": "Tráfico de Drogas",
        "questions": [
            {"id": "data_fato", "label": "Data do fato/denúncia/abordagem", "type": "date", "required": False},
            {"id": "hora_fato", "label": "Hora aproximada", "type": "time", "required": False},
            {"id": "local_fato", "label": "Local", "type": "text", "required": False},
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
                "id": "drogas",
                "label": "Substâncias/quantidades",
                "type": "group",
                "max_items": 10,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "tipo_droga", "label": "Tipo de droga", "type": "text", "required": False, "maxlength": 100},
                    {"id": "quantidade_unidades", "label": "Quantidade (unidades)", "type": "number", "required": False},
                    {"id": "peso", "label": "Peso", "type": "text", "required": False, "maxlength": 50},
                ],
            },
            {
                "id": "testemunhas",
                "label": "Testemunhas",
                "type": "group",
                "max_items": 2,
                "add_label": "Adicionar",
                "fields": [
                    {"id": "nome", "label": "Nome", "type": "text", "required": False, "maxlength": 200},
                    {"id": "rg", "label": "RG/Documento", "type": "text", "required": False, "maxlength": 30},
                    {"id": "contato", "label": "Contato (telefone)", "type": "text", "required": False, "maxlength": 30},
                    {"id": "endereco", "label": "Endereço", "type": "text", "required": False, "maxlength": 400},
                ],
            },
            {"id": "cameras", "label": "Há câmeras de segurança?", "type": "boolean", "required": False},
        ],
    },
    "outros": {
        "label": "Outros",
        "questions": [
            {"id": "data_fato", "label": "Data do fato", "type": "date", "required": False},
            {"id": "local_fato", "label": "Local do fato", "type": "text", "required": False},
            {"id": "descricao", "label": "Descreva o fato ocorrido", "type": "text", "required": False},
            {
                "id": "partes_envolvidas",
                "label": "Partes envolvidas",
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
                "max_items": 2,
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