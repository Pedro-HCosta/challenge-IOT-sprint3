"""Testes do protótipo demonstrativo da Sprint 3."""

from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROJETO / "src"))

from motor_regras import DadosInvalidosError, analisar_prontuario  # noqa: E402


class MotorRegrasTest(unittest.TestCase):
    def setUp(self) -> None:
        caminho = RAIZ_PROJETO / "exemplos" / "prontuario_pet.json"
        self.prontuario = json.loads(caminho.read_text(encoding="utf-8"))

    def test_exemplo_gera_prioridade_alta(self) -> None:
        resultado = analisar_prontuario(
            self.prontuario, data_referencia=date(2026, 9, 11)
        )

        self.assertEqual(resultado["prioridade"], "alta")
        self.assertEqual(resultado["codigo_regra"], "COMPORTAMENTO_PERSISTENTE_001")
        self.assertIn("VACINA_PROXIMA_001", resultado["regras_acionadas"])
        self.assertIn("TEMPERATURA_ELEVADA_001", resultado["regras_acionadas"])

    def test_campos_obrigatorios_sao_validados(self) -> None:
        del self.prontuario["pet_id"]

        with self.assertRaises(DadosInvalidosError):
            analisar_prontuario(self.prontuario)


if __name__ == "__main__":
    unittest.main()
