"""Executa a demonstração local do motor de regras da Sprint 3."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from motor_regras import DadosInvalidosError, analisar_prontuario


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
ENTRADA_PADRAO = RAIZ_PROJETO / "exemplos" / "prontuario_pet.json"


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Demonstração do motor de regras do Clyvo Monitor IoT — Sprint 3."
    )
    parser.add_argument(
        "--entrada",
        type=Path,
        default=ENTRADA_PADRAO,
        help="Prontuário JSON de entrada.",
    )
    parser.add_argument(
        "--data-referencia",
        type=str,
        help="Data usada nas regras, no formato AAAA-MM-DD.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        help="Arquivo JSON opcional para salvar a recomendação.",
    )
    return parser.parse_args()


def executar() -> int:
    args = argumentos()

    try:
        prontuario = json.loads(args.entrada.read_text(encoding="utf-8"))
        referencia = None
        if args.data_referencia:
            referencia = datetime.strptime(args.data_referencia, "%Y-%m-%d").date()

        recomendacao = analisar_prontuario(prontuario, referencia)
        conteudo = json.dumps(recomendacao, ensure_ascii=False, indent=2)

        if args.saida:
            args.saida.parent.mkdir(parents=True, exist_ok=True)
            args.saida.write_text(conteudo + "\n", encoding="utf-8")

        print(conteudo)
        return 0
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: {args.entrada}", file=sys.stderr)
    except json.JSONDecodeError as erro:
        print(f"Erro: o arquivo de entrada não contém JSON válido: {erro}", file=sys.stderr)
    except (DadosInvalidosError, ValueError) as erro:
        print(f"Erro nos dados: {erro}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(executar())
