from app.renderer.common import format_date_br, format_group_generic
from app.renderer.crimes.acidente_transito import render_acidente_transito
from app.renderer.crimes.adulteracao_sinal_identificador import render_adulteracao_sinal_identificador
from app.renderer.crimes.ameaca import render_ameaca
from app.renderer.crimes.calunia_difamacao_injuria import render_calunia_difamacao_injuria
from app.renderer.crimes.comunicacao_obito import render_comunicacao_obito
from app.renderer.crimes.dano import render_dano
from app.renderer.crimes.desaparecimento_encontro_pessoas import render_desaparecimento_encontro_pessoas
from app.renderer.crimes.embriaguez_volante import render_embriaguez_volante
from app.renderer.crimes.estelionato_golpe import render_estelionato_golpe
from app.renderer.crimes.lesao_corporal import render_lesao_corporal
from app.renderer.crimes.maria_da_penha import render_maria_da_penha
from app.renderer.crimes.perda_documentos import render_perda_documentos
from app.renderer.crimes.porte_ilegal_arma_fogo import render_porte_ilegal_arma_fogo
from app.renderer.crimes.roubo_furto import render_roubo_furto
from app.renderer.crimes.trafico_drogas import render_trafico_drogas
from app.renderer.crimes.outros import render_outros
from app.renderer.crimes.violencia_sexual import render_violencia_sexual


class TextRenderer:
    CRIME_LABELS = {
        "acidente_transito": "Acidente de Trânsito",
        "adulteracao_sinal_identificador": "Adulteração de Sinal Identificador de Veículo",
        "ameaca": "Ameaça",
        "calunia_difamacao_injuria": "Calúnia/Difamação/Injúria",
        "comunicacao_obito": "Comunicação de Óbito",
        "dano": "Dano ao Patrimônio",
        "desaparecimento_encontro_pessoas": "Desaparecimento/Encontro de pessoas",
        "embriaguez_volante": "Embriaguez no Volante",
        "estelionato_golpe": "Estelionato (Golpe)",
        "lesao_corporal": "Lesão Corporal",
        "maria_da_penha": "Violência Contra a Mulher (Maria da Penha)",
        "violencia_sexual": "Violência Sexual",
        "perda_documentos": "Perda de Documentos",
        "porte_ilegal_arma_fogo": "Porte Ilegal de Arma de Fogo",
        "roubo_furto": "Roubo/Furto",
        "trafico_drogas": "Tráfico de Drogas",
        "outros": "Outros",
    }

    RENDERERS = {
        "acidente_transito": render_acidente_transito,
        "adulteracao_sinal_identificador": render_adulteracao_sinal_identificador,
        "ameaca": render_ameaca,
        "calunia_difamacao_injuria": render_calunia_difamacao_injuria,
        "comunicacao_obito": render_comunicacao_obito,
        "dano": render_dano,
        "desaparecimento_encontro_pessoas": render_desaparecimento_encontro_pessoas,
        "embriaguez_volante": render_embriaguez_volante,
        "estelionato_golpe": render_estelionato_golpe,
        "lesao_corporal": render_lesao_corporal,
        "maria_da_penha": render_maria_da_penha,
        "perda_documentos": render_perda_documentos,
        "porte_ilegal_arma_fogo": render_porte_ilegal_arma_fogo,
        "roubo_furto": render_roubo_furto,
        "trafico_drogas": render_trafico_drogas,
        "violencia_sexual": render_violencia_sexual,
        "outros": render_outros,
    }

    @classmethod
    def render(cls, submission) -> str:
        crime_label = cls.CRIME_LABELS.get(submission.crime_type, submission.crime_type)
        renderer = cls.RENDERERS.get(submission.crime_type, render_outros)
        return renderer(submission, crime_label)

    @classmethod
    def render_structured(cls, submission, questions: list) -> list:
        result = []
        q_map = {q["id"]: q["label"] for q in questions}

        for qid, label in q_map.items():
            val = submission.answers.get(qid)
            if val is None or val == "" or val == []:
                continue

            if isinstance(val, list):
                if val and all(isinstance(item, dict) for item in val):
                    pretty = format_group_generic(val)
                else:
                    pretty = ", ".join(str(item) for item in val if item)

                if pretty:
                    result.append((label, pretty))
                continue

            if isinstance(val, bool):
                val = "Sim" if val else "Não"
            else:
                val = format_date_br(str(val))

            result.append((label, str(val)))

        return result