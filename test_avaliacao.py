"""Regressoes do registro de evidencias e dos criterios de aprovacao."""

import importlib
import json
from pathlib import Path
import tempfile
import unittest


class AvaliacaoTest(unittest.TestCase):
    def setUp(self):
        self.avaliacao = importlib.import_module("avaliacao")
        self.caso = {
            "id": "conceito", "categoria": "Conceito", "perguntas": ["Explique Factory Method"],
            "rubrica": ["Explica a criacao extensivel por sobrescrita e seu beneficio."],
        }

    def test_texto_com_palavras_chave_nao_aprova_conceito(self):
        registro = self.avaliacao.executar_caso(self.caso, lambda p: {"resposta": "Factory Method Creator Product Java"})
        self.assertEqual(registro["status"], "pendente_revisao")
        self.assertEqual(registro["revisao_humana"][0]["status"], "pendente")

    def test_excecao_qualquer_nao_aprova_entrada_vazia(self):
        caso = {**self.caso, "perguntas": [""], "erro_esperado": "ErroEntradaVazia", "rubrica": []}
        def quebrar(p):
            raise TypeError("falha que nao e rejeicao da entrada")
        registro = self.avaliacao.executar_caso(caso, quebrar)
        self.assertEqual(registro["status"], "reprovado")
        self.assertEqual(registro["turnos"][0]["erro"]["tipo"], "TypeError")

    def test_recusa_exige_tipo_correto_e_mensagem(self):
        caso = {**self.caso, "erro_esperado": "ErroInventicao", "rubrica": []}
        for erro, esperado in [({"tipo": "ErroInventicao", "mensagem": "Nao invento padroes."}, "aprovado"),
                               ({"tipo": "ErroInventicao", "mensagem": ""}, "reprovado"),
                               ({"tipo": "ErroSaidaInesperada", "mensagem": "Falhou."}, "reprovado")]:
            with self.subTest(erro=erro):
                registro = self.avaliacao.executar_caso(caso, lambda p: {"resposta": "", "erro": erro})
                self.assertEqual(registro["status"], esperado)

    def test_multiplos_turnos_sao_salvos_inteiros(self):
        texto = "Conteudo longo.\n" * 1200
        caso = {**self.caso, "perguntas": ["Proponha um exercicio", "Minha tentativa", "Corrigi"]}
        registro = self.avaliacao.executar_caso(caso, lambda p: {"resposta": p + texto, "memoria": [p, texto]})
        with tempfile.TemporaryDirectory() as pasta:
            self.avaliacao.salvar_json(Path(pasta) / "caso.json", registro)
            salvo = json.loads((Path(pasta) / "caso.json").read_text())
        self.assertEqual(len(salvo["turnos"]), 3)
        for pergunta, turno in zip(caso["perguntas"], salvo["turnos"], strict=True):
            self.assertEqual(turno["entrada"], pergunta)
            self.assertEqual(turno["resposta"], pergunta + texto)
            self.assertEqual(turno["memoria"], [pergunta, texto])

    def test_saida_vazia_reprova(self):
        registro = self.avaliacao.executar_caso(self.caso, lambda p: {"resposta": "   "})
        self.assertEqual(registro["status"], "reprovado")

    def test_execucoes_nao_sobrescrevem_evidencias(self):
        with tempfile.TemporaryDirectory() as pasta:
            primeiro = self.avaliacao.nova_execucao(Path(pasta))
            self.avaliacao.salvar_json(primeiro / "marcador.json", {"original": True})
            segundo = self.avaliacao.nova_execucao(Path(pasta))
            self.assertNotEqual(primeiro, segundo)
            self.assertEqual(json.loads((primeiro / "marcador.json").read_text()), {"original": True})

    def test_pendencia_e_bloqueio_nao_retornam_codigo_de_sucesso(self):
        for status, codigo in [("aprovado", 0), ("reprovado", 1), ("bloqueado", 2), ("pendente_revisao", 2)]:
            with self.subTest(status=status):
                self.assertEqual(self.avaliacao.codigo_saida([{"status": status}]), codigo)

    def test_cli_erro_generico_nao_comprova_modelo_indisponivel(self):
        from test_cli import avaliar_saida_cli
        criterios = avaliar_saida_cli({"codigo_saida": 1, "stdout": "[Erro] Saida inesperada.",
                                       "stderr": "", "timeout": False},
                                      1, "Nao foi possivel comunicar com o modelo local")
        self.assertFalse(all(criterios.values()))

    def test_cli_valida_mensagem_de_sessao_invalida_no_stderr(self):
        from test_cli import avaliar_saida_cli
        criterios = avaliar_saida_cli({"codigo_saida": 2, "stdout": "", "stderr": "error: Sessao invalida",
                                       "timeout": False}, 2, "Sessao invalida", canal="stderr")
        self.assertTrue(all(criterios.values()))

    def test_checkpoint_e_gravado_antes_da_chamada_que_pode_travar(self):
        checkpoints = []
        registro = self.avaliacao.executar_caso(
            self.caso, lambda p: {"resposta": "texto", "checkpoint_existia": bool(checkpoints)},
            lambda r: checkpoints.append(r["status"]),
        )
        self.assertTrue(registro["turnos"][0]["checkpoint_existia"])


if __name__ == "__main__":
    unittest.main()
