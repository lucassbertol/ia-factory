"""Testa o contrato de montagem dos agentes sem CrewAI/Ollama instalados.

Somente os construtores externos sao substituidos; a montagem da crew e o
carregamento dos arquivos de prompt executam o codigo real do projeto.
Execute: python -m unittest -v test_prompts
"""

import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest
from unittest.mock import patch


class PromptsDosAgentesTest(unittest.TestCase):
    def setUp(self):
        crewai = ModuleType("crewai")
        for nome in ("Agent", "Crew", "Task"):
            setattr(crewai, nome, lambda **campos: SimpleNamespace(**campos))
        crewai.Process = SimpleNamespace(sequential="sequential")
        llm = ModuleType("agente.llm")
        llm.obter_llm = lambda: object()
        # Carrega uma copia isolada para nao substituir modulos usados por
        # outros testes nem exigir bibliotecas ou chamadas de rede.
        caminho = Path(__file__).parent / "agente" / "crew.py"
        spec = importlib.util.spec_from_file_location("agente._crew_test", caminho)
        self.crew = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"crewai": crewai, "agente.llm": llm}):
            spec.loader.exec_module(self.crew)

    def test_cada_agente_recebe_seu_prompt_integral(self):
        nomes = ("tutor", "exemplificador", "inquiridor", "guardiao")
        crew = self.crew.montar_crew()
        for nome, agente in zip(nomes, crew.agents, strict=True):
            with self.subTest(agente=nome):
                arquivo = Path(__file__).parent / "agente" / "prompts" / f"{nome}.txt"
                self.assertEqual(agente.backstory, arquivo.read_text(encoding="utf-8"))

    def test_prompt_ausente_interrompe_montagem(self):
        with patch.dict(
            self.crew.carregar_prompt.__globals__,
            {"PROMPTS_DIR": Path("/diretorio-inexistente-prompts")},
        ):
            with self.assertRaises(FileNotFoundError):
                self.crew.montar_crew(["tutor", "guardiao"])


if __name__ == "__main__":
    unittest.main()
