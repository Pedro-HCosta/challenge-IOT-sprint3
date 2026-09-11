"""Motor de regras demonstrativo da Sprint 3 do Clyvo Monitor IoT.

O módulo recebe um prontuário simulado em formato de dicionário, avalia
condições objetivas e devolve uma recomendação estruturada. Ele não realiza
diagnóstico e não substitui avaliação veterinária.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


NIVEIS = {"baixa": 1, "media": 2, "alta": 3, "critica": 4}


class DadosInvalidosError(ValueError):
    """Indica que o prontuário não possui a estrutura mínima esperada."""


@dataclass(frozen=True)
class RegraAcionada:
    codigo: str
    prioridade: str
    evidencia: str


def _converter_data(valor: str, campo: str) -> date:
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError) as erro:
        raise DadosInvalidosError(
            f"O campo '{campo}' deve usar o formato AAAA-MM-DD."
        ) from erro


def validar_prontuario(prontuario: dict[str, Any]) -> None:
    """Valida somente os campos necessários para a demonstração."""

    campos_obrigatorios = (
        "pet_id",
        "nome",
        "vacinas",
        "ultima_consulta",
        "comportamento",
        "ambiente",
    )
    ausentes = [campo for campo in campos_obrigatorios if campo not in prontuario]
    if ausentes:
        raise DadosInvalidosError(
            "Campos obrigatórios ausentes: " + ", ".join(ausentes)
        )

    if not isinstance(prontuario["vacinas"], list):
        raise DadosInvalidosError("O campo 'vacinas' deve ser uma lista.")

    if not isinstance(prontuario["ultima_consulta"], dict):
        raise DadosInvalidosError("O campo 'ultima_consulta' deve ser um objeto.")

    if not isinstance(prontuario["comportamento"], dict):
        raise DadosInvalidosError("O campo 'comportamento' deve ser um objeto.")

    if not isinstance(prontuario["ambiente"], dict):
        raise DadosInvalidosError("O campo 'ambiente' deve ser um objeto.")


def _avaliar_comportamento(prontuario: dict[str, Any]) -> list[RegraAcionada]:
    comportamento = prontuario["comportamento"]
    classe = comportamento.get("classe")
    dias = int(comportamento.get("dias_persistentes", 0))
    condicoes = prontuario.get("condicoes", [])

    if classe == "baixa_atividade" and dias >= 3 and condicoes:
        return [
            RegraAcionada(
                codigo="COMPORTAMENTO_PERSISTENTE_001",
                prioridade="alta",
                evidencia=f"baixa atividade registrada por {dias} dias",
            )
        ]

    if classe == "baixa_atividade" and dias >= 3:
        return [
            RegraAcionada(
                codigo="COMPORTAMENTO_PERSISTENTE_002",
                prioridade="media",
                evidencia=f"baixa atividade registrada por {dias} dias",
            )
        ]

    if classe == "agitacao" and dias >= 3:
        return [
            RegraAcionada(
                codigo="AGITACAO_PERSISTENTE_001",
                prioridade="media",
                evidencia=f"agitação registrada por {dias} dias",
            )
        ]

    return []


def _avaliar_vacinas(
    prontuario: dict[str, Any], data_referencia: date
) -> list[RegraAcionada]:
    regras: list[RegraAcionada] = []

    for indice, vacina in enumerate(prontuario["vacinas"]):
        if not isinstance(vacina, dict) or "proxima_dose" not in vacina:
            raise DadosInvalidosError(
                f"A vacina de índice {indice} não possui 'proxima_dose'."
            )

        tipo = vacina.get("tipo", "não identificada")
        proxima_dose = _converter_data(
            vacina["proxima_dose"], f"vacinas[{indice}].proxima_dose"
        )
        dias = (proxima_dose - data_referencia).days

        if dias < 0:
            regras.append(
                RegraAcionada(
                    codigo="VACINA_ATRASADA_001",
                    prioridade="alta",
                    evidencia=f"vacina {tipo} atrasada há {abs(dias)} dias",
                )
            )
        elif dias == 0:
            regras.append(
                RegraAcionada(
                    codigo="VACINA_PROXIMA_001",
                    prioridade="alta",
                    evidencia=f"vacina {tipo} com dose prevista para hoje",
                )
            )
        elif dias <= 7:
            regras.append(
                RegraAcionada(
                    codigo="VACINA_PROXIMA_001",
                    prioridade="media",
                    evidencia=f"vacina {tipo} prevista para daqui a {dias} dias",
                )
            )

    return regras


def _avaliar_consulta(
    prontuario: dict[str, Any], data_referencia: date
) -> list[RegraAcionada]:
    valor = prontuario["ultima_consulta"].get("data")
    if not valor:
        raise DadosInvalidosError("A última consulta deve possuir o campo 'data'.")

    ultima_consulta = _converter_data(valor, "ultima_consulta.data")
    dias = (data_referencia - ultima_consulta).days

    if dias >= 365:
        return [
            RegraAcionada(
                codigo="CONSULTA_PREVENTIVA_001",
                prioridade="media",
                evidencia=f"última consulta registrada há {dias} dias",
            )
        ]
    return []


def _avaliar_ambiente(prontuario: dict[str, Any]) -> list[RegraAcionada]:
    ambiente = prontuario["ambiente"]
    regras: list[RegraAcionada] = []

    temperatura = ambiente.get("temperatura_c")
    if temperatura is not None:
        temperatura = float(temperatura)
        if temperatura >= 35:
            regras.append(
                RegraAcionada(
                    codigo="TEMPERATURA_ELEVADA_002",
                    prioridade="alta",
                    evidencia=f"temperatura ambiental de {temperatura:.1f} °C",
                )
            )
        elif temperatura >= 30:
            regras.append(
                RegraAcionada(
                    codigo="TEMPERATURA_ELEVADA_001",
                    prioridade="media",
                    evidencia=f"temperatura ambiental de {temperatura:.1f} °C",
                )
            )

    umidade = ambiente.get("umidade_percentual")
    if umidade is not None:
        umidade = float(umidade)
        if umidade < 30 or umidade > 75:
            regras.append(
                RegraAcionada(
                    codigo="UMIDADE_FORA_FAIXA_001",
                    prioridade="baixa",
                    evidencia=f"umidade ambiental de {umidade:.1f}%",
                )
            )

    return regras


def _acao_para(prioridade: str) -> str:
    return {
        "critica": "procurar atendimento veterinário imediato",
        "alta": "entrar em contato com a clínica",
        "media": "acompanhar o pet e consultar a clínica se a condição persistir",
        "baixa": "manter o acompanhamento preventivo",
    }[prioridade]


def _mensagem_simulada(
    nome: str, prioridade: str, evidencias: list[str], acao: str
) -> str:
    resumo = "; ".join(evidencias)
    return (
        f"{nome}: identificamos os seguintes pontos de atenção: {resumo}. "
        f"A prioridade é {prioridade}. Recomendamos {acao}. "
        "Esta orientação é informativa e não representa um diagnóstico."
    )


def analisar_prontuario(
    prontuario: dict[str, Any], data_referencia: date | None = None
) -> dict[str, Any]:
    """Aplica as regras e devolve a recomendação estruturada."""

    validar_prontuario(prontuario)
    referencia = data_referencia or date.today()

    regras = [
        *_avaliar_comportamento(prontuario),
        *_avaliar_vacinas(prontuario, referencia),
        *_avaliar_consulta(prontuario, referencia),
        *_avaliar_ambiente(prontuario),
    ]

    if not regras:
        regras = [
            RegraAcionada(
                codigo="ACOMPANHAMENTO_ROTINA_001",
                prioridade="baixa",
                evidencia="nenhum ponto de atenção identificado pelas regras atuais",
            )
        ]

    prioridade = max(regras, key=lambda regra: NIVEIS[regra.prioridade]).prioridade
    regra_principal = next(
        regra for regra in regras if regra.prioridade == prioridade
    )
    evidencias = [regra.evidencia for regra in regras]
    acao = _acao_para(prioridade)

    return {
        "pet_id": prontuario["pet_id"],
        "data_referencia": referencia.isoformat(),
        "prioridade": prioridade,
        "codigo_regra": regra_principal.codigo,
        "regras_acionadas": [regra.codigo for regra in regras],
        "evidencias": evidencias,
        "acao_sugerida": acao,
        "mensagem_simulada": _mensagem_simulada(
            prontuario["nome"], prioridade, evidencias, acao
        ),
        "aviso": (
            "A recomendação oferece apoio informativo e não substitui "
            "avaliação veterinária."
        ),
    }
