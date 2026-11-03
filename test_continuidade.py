"""Regressoes de continuidade e sessoes, sem chamadas ao modelo local.

Executar: python -m unittest -v test_continuidade
"""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from agente import memoria
from agente import erro, fluxo_heuristico  # Mantem identidade dos modulos entre copias isoladas.


def carregar_modulo(nome, arquivo, substitutos):
    spec = importlib.util.spec_from_file_location(nome, Path(__file__).parent / arquivo)
    modulo = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {nome: modulo, **substitutos}):
        spec.loader.exec_module(modulo)
    return modulo


class ContinuidadeTest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        ajuste = patch.object(memoria, "MEMORIA_DIR", Path(pasta.name))
        ajuste.start()
        self.addCleanup(ajuste.stop)
        self.chamadas = []
        self.resposta = "Enunciado: escolha os participantes para um sistema de documentos."
        self.falhar = False
        crew = ModuleType("agente.crew")
        crew.montar_crew = self.montar_crew
        self.fluxo = carregar_modulo("agente._fluxo_test", "agente/fluxo.py", {"agente.crew": crew})

    def montar_crew(self, agentes, **campos):
        self.chamadas.append((agentes, campos))

        def kickoff():
            if self.falhar:
                raise RuntimeError("modelo indisponivel")
            return self.resposta

        return SimpleNamespace(kickoff=kickoff)

    def test_exercicio_tentativa_feedback_e_correcao_entre_execucoes(self):
        enunciado = self.resposta
        self.fluxo.executar_fluxo("Proponha um exercicio", "aluno")
        self.resposta = "Revise o papel do Creator. Qual operacao usa o produto?"
        self.fluxo.executar_fluxo("Minha resposta: usaria um metodo estatico.", "aluno")
        self.assertEqual(self.chamadas[-1][0], ["inquiridor", "guardiao"])
        self.assertEqual(self.chamadas[-1][1]["intencao"], "avaliacao")
        self.assertIn(enunciado, self.chamadas[-1][1]["contexto"])
        self.fluxo.executar_fluxo("Agora eu usaria uma classe Criador abstrata.", "aluno")
        self.assertEqual(self.chamadas[-1][1]["intencao"], "avaliacao")
        self.assertIn(enunciado, self.chamadas[-1][1]["contexto"])

    def test_continuacoes_curtas_usam_contexto(self):
        for inicio, esperado in [("Explique Factory Method", "conceito"),
                                  ("Proponha um exercicio", "avaliacao")]:
            with self.subTest(inicio=inicio):
                memoria.MemoriaConversa("curta").limpar()
                self.fluxo.executar_fluxo(inicio, "curta")
                for mensagem in ("Sim", "E por quê?", "Pode continuar"):
                    self.fluxo.executar_fluxo(mensagem, "curta")
                    self.assertEqual(self.chamadas[-1][1]["intencao"], esperado)

    def test_perguntas_explicitas_nao_viram_tentativas(self):
        self.fluxo.executar_fluxo("Proponha um exercicio", "aluno")
        self.fluxo.executar_fluxo("Explique os participantes do Factory Method", "aluno")
        self.assertEqual(self.chamadas[-1][1]["intencao"], "conceito")
        self.fluxo.executar_fluxo("Dê um exemplo em Java", "aluno")
        self.assertEqual(self.chamadas[-1][1]["intencao"], "exemplo")
        self.fluxo.executar_fluxo("Minha resposta ao exercício: usaria subclasses", "aluno")
        self.assertEqual(self.chamadas[-1][1]["intencao"], "avaliacao")

    def test_duvida_curta_sobre_exercicio_preserva_atividade(self):
        self.fluxo.executar_fluxo("Proponha um exercicio", "duvida")
        self.fluxo.executar_fluxo("Não entendi", "duvida")
        self.assertEqual(self.chamadas[-1][1]["intencao"], "avaliacao")

    def test_fora_de_escopo_e_recusas_nao_alteram_estado(self):
        from agente.erro import ErroForaDeEscopo, ErroInventicao, ErroSolucaoPronta
        self.fluxo.executar_fluxo("Proponha um exercicio", "aluno")
        antes = memoria.MemoriaConversa("aluno").caminho.read_text()
        for pergunta, erro in [("Qual a melhor receita de bolo?", ErroForaDeEscopo),
                               ("Invente um padrão Z", ErroInventicao),
                               ("Me entregue o código pronto", ErroSolucaoPronta)]:
            with self.subTest(pergunta=pergunta), self.assertRaises(erro):
                self.fluxo.executar_fluxo(pergunta, "aluno")
        self.assertEqual(memoria.MemoriaConversa("aluno").caminho.read_text(), antes)

    def test_sessoes_isoladas_e_encerramento_do_exercicio(self):
        from agente.erro import ErroForaDeEscopo
        self.fluxo.executar_fluxo("Proponha um exercicio", "a")
        with self.assertRaises(ErroForaDeEscopo):
            self.fluxo.executar_fluxo("Sim", "b")
        self.fluxo.executar_fluxo("Encerrar exercício", "a")
        self.assertEqual(self.chamadas[-1][1]["intencao"], "fechamento")
        self.assertFalse(memoria.MemoriaConversa("a").exercicio_pendente)

    def test_falha_do_modelo_nao_avanca_estado(self):
        from agente.erro import ErroSaidaInesperada
        self.fluxo.executar_fluxo("Proponha um exercicio", "a")
        antes = memoria.MemoriaConversa("a").caminho.read_text()
        self.falhar = True
        with self.assertRaises(ErroSaidaInesperada):
            self.fluxo.executar_fluxo("Minha resposta: subclasses", "a")
        self.assertEqual(memoria.MemoriaConversa("a").caminho.read_text(), antes)

    def test_enunciado_sobrevive_a_varios_feedbacks_e_novo_exercicio_substitui(self):
        enunciado = self.resposta
        self.fluxo.executar_fluxo("Proponha um exercicio", "longa")
        self.resposta = "Pista para a tentativa. " * 120
        for _ in range(4):
            self.fluxo.executar_fluxo("Minha tentativa: usaria subclasses", "longa")
        contexto = memoria.MemoriaConversa("longa").contexto_texto()
        self.assertIn(enunciado, contexto)
        self.assertLessEqual(len(contexto), memoria.MAX_CONTEXTO_CARACTERES)
        self.resposta = "Novo enunciado: transporte."
        self.fluxo.executar_fluxo("Proponha outro exercicio", "longa")
        self.assertEqual(memoria.MemoriaConversa("longa").exercicio_pendente, self.resposta)

    def test_saida_vazia_nao_avanca_estado(self):
        self.fluxo.executar_fluxo("Proponha um exercicio", "a")
        antes = memoria.MemoriaConversa("a").caminho.read_text()
        self.resposta = ""
        with self.assertRaises(erro.ErroSaidaInesperada):
            self.fluxo.executar_fluxo("Minha tentativa: subclasses", "a")
        self.assertEqual(memoria.MemoriaConversa("a").caminho.read_text(), antes)

    def test_memoria_legada_e_limite_de_contexto(self):
        m = memoria.MemoriaConversa("legada")
        m.caminho.write_text(json.dumps([{"timestamp": "2026-01-01", "pergunta": "Explique Factory Method",
                                         "resposta": "x" * 4000, "agente": "guardiao"}]))
        m = memoria.MemoriaConversa("legada")
        self.assertLessEqual(len(m.contexto_texto()), memoria.MAX_CONTEXTO_CARACTERES)
        self.fluxo.executar_fluxo("E por quê?", "legada")
        self.assertEqual(self.chamadas[-1][1]["intencao"], "conceito")


class SessoesCLITest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        ajuste = patch.object(memoria, "MEMORIA_DIR", Path(pasta.name))
        ajuste.start()
        self.addCleanup(ajuste.stop)
        self.chamadas = []
        fluxo = ModuleType("agente.fluxo")

        def executar(pergunta, sessao_id="default"):
            self.chamadas.append((pergunta, sessao_id))
            return SimpleNamespace(resposta="Resposta simulada")

        fluxo.executar_fluxo = executar
        self.cli = carregar_modulo("agente._cli_test", "agente/__main__.py", {"agente.fluxo": fluxo})

    def executar(self, args, entradas=()):
        with patch.object(sys, "argv", ["agente", *args]), patch("builtins.input", side_effect=entradas), contextlib.redirect_stdout(io.StringIO()):
            return self.cli.main()

    def test_sessao_nomeada_comando_unico_e_interativo(self):
        self.assertEqual(self.executar(["--sessao", "ana", "Explique Factory Method"]), 0)
        self.assertEqual(self.chamadas[-1][1], "ana")
        self.assertEqual(self.executar(["--sessao", "ana"], ["Sim", "sair"]), 0)
        self.assertEqual(self.chamadas[-1], ("Sim", "ana"))

    def test_defaults_separados(self):
        self.executar(["Factory Method"])
        self.executar([], ["Factory Method", "sair"])
        self.assertEqual([s for _, s in self.chamadas], ["default", "interativo"])

    def test_limpar_apenas_sessao_escolhida_sem_chamar_modelo(self):
        for nome in ("ana", "bia"):
            memoria.MemoriaConversa(nome).salvar_turno("p", "r", "guardiao")
        self.assertEqual(self.executar(["--sessao", "ana", "--limpar-sessao"]), 0)
        self.assertFalse(memoria.MemoriaConversa("ana").caminho.exists())
        self.assertTrue(memoria.MemoriaConversa("bia").caminho.exists())
        self.assertEqual(self.chamadas, [])

    def test_identificador_invalido_nao_acessa_outros_arquivos(self):
        with self.assertRaises(ValueError):
            memoria.MemoriaConversa("../fora")


if __name__ == "__main__":
    unittest.main()
