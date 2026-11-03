"""Testa o contrato de montagem dos agentes sem CrewAI/Ollama instalados.

Somente os construtores externos sao substituidos; a montagem da crew e o
carregamento dos arquivos de prompt executam o codigo real do projeto.
Execute: python -m unittest -v test_prompts
"""

import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import tempfile
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
                self.assertTrue(agente.backstory.startswith(arquivo.read_text(encoding="utf-8")))

    def test_referencia_local_chega_a_todos_os_agentes(self):
        from agente.config import ROOT_DIR
        referencia = ROOT_DIR / "agente" / "referencias" / "factory_method.md"
        self.assertTrue(referencia.exists(), "Falta a referencia conceitual local")
        texto = referencia.read_text(encoding="utf-8")
        for agente in self.crew.montar_crew().agents:
            with self.subTest(agente=agente.role):
                self.assertIn(texto, agente.backstory)

    def test_exemplo_java_fornecido_ao_exemplificador_e_guardiao(self):
        from agente.config import ROOT_DIR
        caminho = ROOT_DIR / "agente" / "referencias" / "ExemploFactoryMethod.java"
        self.assertTrue(caminho.exists(), "Falta o exemplo Java de referencia")
        codigo = caminho.read_text(encoding="utf-8")
        crew = self.crew.montar_crew(["exemplificador", "guardiao"], intencao="exemplo")
        for tarefa in crew.tasks:
            self.assertIn(codigo, tarefa.description)

    def test_exercicio_nao_recebe_codigo_do_exemplo(self):
        crew = self.crew.montar_crew(["inquiridor", "guardiao"], intencao="exercicio")
        for tarefa in crew.tasks:
            self.assertNotIn("public class ExemploFactoryMethod", tarefa.description)

    def test_referencia_vazia_impede_agentes_sem_base_factual(self):
        with tempfile.TemporaryDirectory() as pasta:
            (Path(pasta) / "factory_method.md").write_text(" \n", encoding="utf-8")
            with patch.dict(self.crew.carregar_referencia.__globals__, {"REFERENCIAS_DIR": Path(pasta)}):
                with self.assertRaises(ValueError):
                    self.crew.montar_crew(["tutor", "guardiao"])

    def test_prompt_ausente_interrompe_montagem(self):
        with patch.dict(
            self.crew.carregar_prompt.__globals__,
            {"PROMPTS_DIR": Path("/diretorio-inexistente-prompts")},
        ):
            with self.assertRaises(FileNotFoundError):
                self.crew.montar_crew(["tutor", "guardiao"])


if __name__ == "__main__":
    unittest.main()
