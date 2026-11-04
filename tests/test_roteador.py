"""Roteamento com erros de digitação e limpeza do texto dos autores, sem Ollama.

Casos tirados do teste na interface web de 04/11: "me de um exerício sobre
factory metod" foi tratado como pergunta de conceito, e o Tutor improvisou um
exemplo cujos títulos ficaram vazios depois que o código foi retirado.
"""
import unittest

from agente.fluxo_heuristico import classificar_intencao, normalizar_pergunta
from agente import fluxo, recusas
from agente.crew import PlanoTurno, _exigencias
from agente.verificacao import (
    Exigencias, ValidadorDeterministico, corrigir_mecanicamente, encontrar_problemas,
)


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
                         "Não. Ela usou uma Simple Factory, com método static e if.", "Não.",
                         # Sem "Minha resposta:" e sem vocabulário técnico (pedido do usuário, 04/11).
                         "Recibo", "Não existe", "Ela está errada", "Acho que é o Emissor", "Sim."):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(classificar_intencao(pergunta, **pratica).tipo, "avaliacao")
        for pergunta, tipo in (("o que é o creator?", "conceito"), ("qual a receita de bolo", "fora_de_escopo"),
                               ("qual a diferença entre simple factory e factory method?", "comparacao"),
                               ("Como o padrão costuma ser aplicado de forma errada?", "uso_incorreto"),
                               ("me de um exemplo em java", "exemplo"), ("Faça um resumo final", "fechamento"),
                               ("não entendi", "esclarecimento"), ("Qual seria o Creator?", "esclarecimento"),
                               ("Invente um padrão Z", "inventicao"),
                               ("me de um exercício", "exercicio"), ("Encerrar exercício", "fechamento")):
            with self.subTest(pergunta=pergunta):
                self.assertEqual(classificar_intencao(pergunta, **pratica).tipo, tipo)

    def test_vale_mesmo_depois_de_uma_pergunta_de_conceito(self):
        # Antes era preciso que o turno anterior fosse do exercício.
        self.assertEqual(classificar_intencao("Ela está errada", ultima_intencao="conceito",
                                              exercicio_pendente=True).tipo, "avaliacao")

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


# Resposta real (teste web de 04/11) ao "O que devo lembrar antes de usar o padrão?"
FECHAMENTO = """Antes de usar o Factory Method, lembre-se dos seguintes pontos:

1. **Intenção**: Separar quem usa um objeto de quem decide qual objeto criar.

Evitar:
- Se não houver variação no tipo de objeto, pois isso pode resultar em uma hierarquia desnecessária.

O Factory Method é um padrão que combina o conceito de fábrica com sobrescritas de métodos.

Qual outro padrão você consideraria usar em vez do Factory Method?"""


class SemPerguntaFinalTest(unittest.TestCase):
    """Pedido do usuário (04/11): sem perguntas ao final, exceto nos exercícios."""

    def validar(self, intencao, texto, autor="tutor"):
        plano = PlanoTurno("pergunta", intencao, [autor])
        return ValidadorDeterministico(_exigencias(plano, autor)).validar(texto)

    def test_fechamento_real_perde_a_pergunta(self):
        ok, texto = self.validar("fechamento", FECHAMENTO)
        self.assertTrue(texto.endswith("sobrescritas de métodos."))
        self.assertNotIn("?", texto[-200:])

    def test_exemplo_perde_o_desafio(self):
        texto = ("O Creator Notificador declara criarNotificacao() e avisar() usa o produto pela "
                 "interface.\n\nQue tal tentar: como isso poderia ser aplicado usando o Factory Method?")
        ok, limpo = self.validar("exemplo", texto, "exemplificador")
        self.assertTrue(limpo.endswith("pela interface."))

    def test_avaliacao_mantem_a_pergunta(self):
        texto = "Certo, Recibo é o Product. Quem seria o Creator?"
        ok, limpo = self.validar("avaliacao", texto, "inquiridor")
        self.assertTrue(limpo.endswith("Quem seria o Creator?"))

    def test_resposta_montada_sem_pergunta_padrao(self):
        plano = PlanoTurno("O que devo lembrar?", "fechamento", ["tutor"])
        self.assertEqual(fluxo._montar_resposta(plano, {"tutor": "Ponto um. Ponto dois."}, ""),
                         "Ponto um. Ponto dois.")
        plano = PlanoTurno("Minha resposta", "avaliacao", ["inquiridor"])
        self.assertTrue(fluxo._montar_resposta(plano, {"inquiridor": "Certo."}, "").endswith("?"))

    def test_recusas_sem_pergunta_final(self):
        for texto in (recusas.boas_vindas(), recusas.padrao_inventado(), recusas.padrao_desconhecido("Z"),
                      recusas.outro_padrao("Strategy"), recusas.solucao_pronta(), recusas.fora_de_escopo(),
                      recusas.resposta_nao_validada()):
            with self.subTest(texto=texto[:40]):
                self.assertFalse(texto.rstrip().endswith("?"))


if __name__ == "__main__":
    unittest.main()
