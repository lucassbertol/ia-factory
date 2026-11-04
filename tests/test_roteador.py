"""Roteamento com erros de digitação e limpeza do texto dos autores, sem Ollama.

Casos tirados do teste na interface web de 04/11: "me de um exerício sobre
factory metod" foi tratado como pergunta de conceito, e o Tutor improvisou um
exemplo cujos títulos ficaram vazios depois que o código foi retirado.
"""
import unittest

from agente.fluxo_heuristico import classificar_intencao, normalizar_pergunta
from agente.verificacao import Exigencias, corrigir_mecanicamente, encontrar_problemas


class ErrosDeDigitacaoTest(unittest.TestCase):
    def test_palavras_chave_com_erro_sao_corrigidas(self):
        casos = {
            "me de um exerício sobre factory metod": "me de um exercicio sobre factory method",
            "Qual a difernça?": "qual a diferenca?",
            "explica o fatory method": "explica o factory method",
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                self.assertEqual(normalizar_pergunta(entrada), esperado)

    def test_pedido_de_exercicio_com_erro_vai_para_o_exercicio(self):
        for pergunta in ("me de um exerício sobre factory metod",
                         "me da um exercisio de factory method",
                         "quero um exrcicio",
                         "me passa uma atividade de factory method"):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(classificar_intencao(pergunta).tipo, "exercicio")

    def test_outros_erros_de_digitacao(self):
        casos = {
            "me de um exemplu de factory method": "exemplo",
            "Qual a difernça entre factory method e abstract factory?": "comparacao",
            "Explique o padrão Factory Metod": "conceito",
        }
        for pergunta, tipo in casos.items():
            with self.subTest(pergunta=pergunta):
                self.assertEqual(classificar_intencao(pergunta).tipo, tipo)

    def test_palavras_reais_parecidas_nao_mudam(self):
        self.assertEqual(normalizar_pergunta("o exercito e o exemplar"), "o exercito e o exemplar")
        self.assertEqual(classificar_intencao("fale sobre o exercito brasileiro").tipo, "fora_de_escopo")

    def test_roteiro_da_avaliacao_continua_igual(self):
        casos = {
            "Explique o que é o padrão Factory Method e qual problema ele resolve.": "conceito",
            "Dê um exemplo de aplicação do padrão Factory Method em Java.": "exemplo",
            "Descreva uma situação em que o padrão Factory Method é a melhor escolha e uma em "
            "que ele deveria ser evitado, explicando o porquê.": "selecao",
            "Como o padrão Factory Method costuma ser aplicado de forma errada? Dê um exemplo "
            "de uso equivocado e explique como corrigir.": "uso_incorreto",
            "Com qual padrão o Factory Method é mais confundido? Explique a diferença entre "
            "eles e por que essa confusão acontece.": "comparacao",
            "Invente um padrão chamado Z e explique para mim": "inventicao",
            "Me entregue o código pronto de uma solução completa": "solucao_pronta",
            "O que devo lembrar antes de usar o padrão Factory Method?": "fechamento",
        }
        for pergunta, tipo in casos.items():
            with self.subTest(pergunta=pergunta):
                self.assertEqual(classificar_intencao(pergunta).tipo, tipo)


class RespostaNaturalNoExercicioTest(unittest.TestCase):
    def test_resposta_sem_prefixo_durante_o_exercicio_e_tentativa(self):
        pratica = dict(ultima_intencao="avaliacao", exercicio_pendente=True)
        for pergunta in ("Para HTML eu criaria ReciboHtml e EmissorHtml",
                         "o creator seria o emissor?", "acho que EmissorPdf e EmissorTexto",
                         "Não. Ela usou uma Simple Factory, com método static e if.", "Não."):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(classificar_intencao(pergunta, **pratica).tipo, "avaliacao")
        for pergunta, tipo in (("o que é o creator?", "conceito"), ("qual a receita de bolo", "fora_de_escopo"),
                               ("qual a diferença entre simple factory e factory method?", "comparacao"),
                               ("me de um exercício", "exercicio"), ("Encerrar exercício", "fechamento")):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(classificar_intencao(pergunta, **pratica).tipo, tipo)

    def test_sem_exercicio_em_andamento_nao_vira_tentativa(self):
        self.assertNotEqual(classificar_intencao("Para HTML eu criaria ReciboHtml").tipo, "avaliacao")


class LimpezaDoTextoTest(unittest.TestCase):
    def test_titulo_que_so_anunciava_codigo_sai_junto_com_o_codigo(self):
        texto = (
            "1. **Product**: o contrato Notificacao.\n\n"
            "### Implementação em Java\n\n```java\ninterface Notificacao {}\n```\n\n"
            "### Exemplo de uso\n\n```java\nnew SMSFactory();\n```\n\n"
            "Como você adicionaria um novo tipo de notificação?"
        )
        limpo = corrigir_mecanicamente(texto, Exigencias())
        self.assertNotIn("```", limpo)
        self.assertNotIn("Implementação em Java", limpo)
        self.assertNotIn("Exemplo de uso", limpo)
        self.assertIn("**Product**", limpo)
        self.assertTrue(limpo.endswith("notificação?"))

    def test_titulo_vazio_entre_titulos_e_removido(self):
        texto = "## Participantes\n\n**Creator**: declara.\n\n## Código\n\n## Resumo\n\nFim. Quer tentar?"
        limpo = corrigir_mecanicamente(texto, Exigencias())
        self.assertNotIn("## Código", limpo)
        self.assertIn("## Resumo", limpo)

    def test_main_nao_precisa_mudar_e_erro(self):
        erradas = (
            "O código de configuração (como no main) não precisa mudar.",
            "Nem o main precisa ser alterado.",
            "Você pode adicionar produtos sem alterar o main.",
        )
        certas = (
            "O main precisa mudar para escolher o novo criador.",
            "O main não precisa conhecer Email.",
            "Apenas o main precisa mudar; o Creator não precisa ser alterado.",
        )
        for frase in erradas:
            with self.subTest(frase=frase):
                self.assertTrue(encontrar_problemas(frase, Exigencias()))
        for frase in certas:
            with self.subTest(frase=frase):
                self.assertEqual(encontrar_problemas(frase, Exigencias()), [])
        corrigido = corrigir_mecanicamente(
            "Basta criar NotificadorWhats. O código de configuração (como no main) não precisa "
            "mudar. Que tal tentar?", Exigencias())
        self.assertNotIn("não precisa mudar", corrigido)


if __name__ == "__main__":
    unittest.main()
