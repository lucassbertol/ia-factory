"""Avaliação de tentativas do exercício, sem Ollama.

Teste web de 04/11: "Minha resposta: o product seria o recibo." foi bloqueada
duas vezes. O texto do Inquiridor passou na validação automática, mas o Guardião
(que não recebe o gabarito) julgou a tentativa do estudante, citou as próprias
instruções como referência e a revisão virou INCONCLUSIVO.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from agente import fluxo
from agente.conhecimento import exercicio_por_id
from agente.avaliacao_exercicio import avaliar_extensao, avaliar_recibos, avaliar_simple_factory
from agente.memoria import MemoriaConversa
from agente.verificacao import (
    Exigencias, corrigir_mecanicamente, encontrar_problemas, frases_atribuidas, nomes_reservados,
    repete_resposta,
)

TENTATIVA = "Minha resposta: o product seria o recibo."
AVALIACAO_BOA = ("Isso mesmo: Recibo é o Product, o contrato comum dos recibos. "
                 "Agora pense em quem cria os recibos. Quem seria o Creator?")
VAZAMENTO = ("Correto. Os ConcreteProducts são ReciboPdf e ReciboTexto. O Creator é Emissor, "
             "com criarRecibo(), e EmissorPdf e EmissorTexto sobrescrevem esse método. "
             "Quem seria o Creator?")
# Crítica real do Guardião no teste web: cita a instrução da tarefa como referência.
CRITICA_INVENTADA = json.dumps({"veredito": "REPROVADO", "problemas": [{
    "autor": "inquiridor", "tipo": "erro",
    "trecho": "Minha resposta está correta ao identificar Recibo como Product.",
    "referencia": "Código e UML verificados serão exibidos pelo sistema; revise o texto gerado.",
    "correcao": "A definição dos ConcreteProducts e do Creator está incorreta.",
}]}, ensure_ascii=False)


def saida(*textos):
    return SimpleNamespace(tasks_output=[SimpleNamespace(raw=t) for t in textos], raw=textos[-1])


class AvaliacaoExercicioTest(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        raiz = Path(pasta.name)
        ctx = patch("agente.memoria.MEMORIA_DIR", raiz / "sessoes")
        ctx.start(); self.addCleanup(ctx.stop)
        ctx = patch.dict("os.environ", {"CREWAI_STORAGE_DIR": str(raiz / "crewai")})
        ctx.start(); self.addCleanup(ctx.stop)
        self.crews = []
        exercicio = fluxo.executar_fluxo("me de um exercício de factory method", "aluno")
        self.assertIn("recibos", exercicio.resposta)

    def responder(self, *saidas, pergunta=TENTATIVA, sessao="aluno"):
        fila = iter(saidas)

        def executar(montar):
            self.crews.append(montar())
            return next(fila)

        with patch("agente.fluxo._executar", side_effect=executar):
            return fluxo.executar_fluxo(pergunta, sessao)

    def test_guardiao_sem_decisao_nao_bloqueia_avaliacao_valida(self):
        revisoes = (CRITICA_INVENTADA, '{"veredito":"INCONCLUSIVO","problemas":[]}', "texto solto")
        for n, revisao in enumerate(revisoes):
            with self.subTest(revisao=revisao[:30]):
                fluxo.executar_fluxo("me de um exercício de factory method", f"aluno{n}")
                resultado = self.responder(saida(AVALIACAO_BOA, revisao), sessao=f"aluno{n}")
                self.assertEqual(resultado.intencao, "avaliacao")
                self.assertEqual(resultado.tipo, "resposta")
                self.assertIn("Recibo é o Product", resultado.resposta)
                self.assertTrue(resultado.revisao["entregue_sem_aprovacao"])
                self.assertFalse(resultado.revisao["bloqueada"])

    def test_exercicio_continua_pendente_depois_da_avaliacao(self):
        self.responder(saida(AVALIACAO_BOA, "texto solto"))
        self.assertTrue(MemoriaConversa("aluno").exercicio_pendente)
        self.assertEqual(MemoriaConversa("aluno").exercicio_atual, "recibos")

    def test_inquiridor_recebe_falas_do_estudante_e_contrato_sem_equivoco_obrigatorio(self):
        self.responder(saida(AVALIACAO_BOA, "texto solto"))
        self.responder(saida(AVALIACAO_BOA, "texto solto"), pergunta="Minha resposta: o Creator seria Emissor.")
        tarefa = self.crews[-1].tasks[0]
        self.assertNotIn("aponte o principal equívoco", tarefa.description)
        self.assertIn("Creator: CORRETO", tarefa.description)
        self.assertNotIn("EmissorPdf", tarefa.description)  # o gabarito não vai mais ao modelo
        validador = tarefa.guardrail.__self__
        self.assertIn("product seria o recibo", validador.exigencias.fala_estudante)
        self.assertIn("Creator seria Emissor", validador.exigencias.fala_estudante)
        self.assertNotIn("Exercício: recibos", validador.exigencias.fala_estudante)

    def test_tentativa_nova_nao_recebe_a_resposta_anterior_para_copiar(self):
        # Teste web de 04/11: a segunda tentativa trouxe as partes que faltavam e o
        # Inquiridor devolveu, palavra por palavra, a resposta anterior.
        anterior = ("Está correto que Recibo seria o Product. Agora, vamos avançar e perguntar "
                    "quem seriam os ConcreteProducts. Você poderia descrever essas classes? "
                    "E depois, qual classe seria o Creator responsável por chamar emitir()?")
        self.responder(saida(anterior, '{"veredito":"APROVADO","problemas":[]}'),
                       pergunta="Minha resposta: product é o recibo")
        completa = ("Minha resposta:\n\nConcreteProducts: ReciboPdf e ReciboTexto.\n\n"
                    "Creator: EmissorRecibo, com emitir() e o factory method criarRecibo().\n\n"
                    "ConcreteCreators: EmissorReciboPdf e EmissorReciboTexto sobrescrevem criarRecibo().")
        self.responder(saida(AVALIACAO_BOA, "texto solto"), pergunta=completa)
        tarefa = self.crews[-1].tasks[0]
        descricao = tarefa.description
        self.assertNotIn("Você poderia descrever essas classes", descricao)
        self.assertIn("Última pergunta feita ao estudante: Quais seriam os ConcreteProducts", descricao)
        self.assertIn("ConcreteCreators: CORRETO", descricao)
        self.assertIn("Não há nenhum equívoco", descricao)
        self.assertLess(descricao.index("Enunciado do exercício"), descricao.index("TENTATIVA ATUAL"))
        self.assertLess(descricao.index("TENTATIVA ATUAL"), descricao.index("Sua tarefa"))
        validador = tarefa.guardrail.__self__
        problemas = encontrar_problemas(anterior, validador.exigencias)
        self.assertTrue(any("repetiu" in p for p in problemas))

    def test_sequencia_do_teste_web(self):
        # 1ª: o modelo copiou o gabarito; 2ª: inventou equívocos numa tentativa certa.
        copia = "Product: Recibo (interface). ConcreteProducts: ReciboPdf e ReciboTexto."
        primeira = self.responder(saida(copia, "texto solto"),
                                  pergunta="Minha resposta: product seria o recibo")
        self.assertNotIn("EmissorPdf", self.crews[-1].tasks[0].description)
        self.assertTrue(primeira.resposta.endswith("Quais seriam os ConcreteProducts, os tipos concretos de recibo?"))
        completa = ("Minha resposta:\n\nConcreteProducts: ReciboPdf e ReciboTexto (implementam a "
                    "formatação específica do PDF e do texto).\n\nCreator: EmissorRecibo (classe base "
                    "que possui o método emitir() e declara o Factory Method abstrato criarRecibo()).\n\n"
                    "ConcreteCreators: EmissorReciboPdf e EmissorReciboTexto (sobrescrevem apenas o "
                    "criarRecibo() para instanciar e retornar ReciboPdf e ReciboTexto, respectivamente).")
        inventada = ("Product seria Recibo. Você acertou ao identificar Recibo como Product. Mas há um "
                     "equívoco no seu entendimento de quem sobrescreve o factory method. Além disso, "
                     "você mencionou que EmissorPdf e EmissorTexto são ConcreteCreators, mas eles "
                     "estão corretamente descrevendo os ConcreteProducts.")
        segunda = self.responder(saida(inventada, "texto solto"), pergunta=completa)
        self.assertNotIn("equívoco", segunda.resposta)
        self.assertIn("o Creator e os ConcreteCreators estão corretos", segunda.resposta)
        self.assertIn("HTML", segunda.resposta)
        self.assertTrue(segunda.revisao["resposta_verificada"])

    def test_texto_bom_do_modelo_recebe_a_pergunta_verificada(self):
        texto = "Muito bem: Recibo é mesmo o Product, o contrato comum. Quer pensar nos concretos?"
        resultado = self.responder(saida(texto, '{"veredito":"APROVADO","problemas":[]}'))
        self.assertTrue(resultado.resposta.startswith("Muito bem: Recibo é mesmo o Product"))
        self.assertNotIn("Quer pensar", resultado.resposta)
        self.assertTrue(resultado.resposta.endswith("os tipos concretos de recibo?"))

    def test_guardiao_recebe_aviso_de_que_a_pergunta_e_a_tentativa(self):
        self.responder(saida(AVALIACAO_BOA, "texto solto"))
        descricao = self.crews[0].tasks[-1].description
        self.assertIn("TENTATIVA do estudante", descricao)
        self.assertNotIn("ReciboPdf", descricao)  # o gabarito continua fora do Guardião

    def test_revelar_o_gabarito_bloqueia_mesmo_sem_decisao_do_guardiao(self):
        resultado = self.responder(saida(VAZAMENTO, "texto solto"))
        self.assertEqual(resultado.tipo, "orientacao")
        self.assertTrue(resultado.revisao["bloqueada"])
        self.assertNotIn("EmissorPdf", resultado.resposta)

    def test_aprovacao_continua_entregando(self):
        resultado = self.responder(saida(AVALIACAO_BOA, '{"veredito":"APROVADO","problemas":[]}'))
        self.assertEqual(resultado.tipo, "resposta")
        self.assertFalse(resultado.revisao["entregue_sem_aprovacao"])

    def test_conceito_inconclusivo_continua_bloqueado(self):
        resultado = self.responder(
            saida("A operação de negócio usa Product sem depender das classes concretas. Quer um exemplo?",
                  '{"veredito":"INCONCLUSIVO","problemas":[]}'),
            pergunta="Explique uma vantagem do Factory Method.")
        self.assertEqual(resultado.tipo, "orientacao")


# Resposta real do Inquiridor no teste web de 04/11 (segunda rodada).
ATRIBUIDA = """**Estudante:** Product seria Recibo.

**Gabarito:** Você acertou ao identificar Recibo como o Product. No entanto, há um equívoco na \
definição dos ConcreteProducts e do Creator. O método `emitir()` não deve ter a escolha de criar PDF \
ou texto dentro dele; isso deveria ser feita pelo factory method que você descreveu.

**Pergunta guia:** Quem seria o Creator?"""


class ErroAtribuidoTest(unittest.TestCase):
    def setUp(self):
        exercicio = exercicio_por_id("recibos")
        self.exigencias = Exigencias(
            reservados=nomes_reservados(exercicio.gabarito, exercicio.enunciado + TENTATIVA),
            fala_estudante=TENTATIVA,
            proibidos=[(r"\bgabarito\b", "Não mencione o gabarito.")],
        )

    def test_resposta_real_e_reprovada_na_primeira_tentativa(self):
        problemas = encontrar_problemas(ATRIBUIDA, self.exigencias)
        self.assertTrue(any("não escreveu" in p for p in problemas))

    def test_correcao_mecanica_tira_rotulos_e_erro_inventado(self):
        limpo = corrigir_mecanicamente(ATRIBUIDA, self.exigencias)
        for trecho in ("Estudante:", "Gabarito", "Pergunta guia", "equívoco", "você descreveu"):
            self.assertNotIn(trecho, limpo)
        self.assertIn("Você acertou ao identificar Recibo como o Product.", limpo)
        self.assertTrue(limpo.endswith("Quem seria o Creator?"))
        self.assertEqual(encontrar_problemas(limpo, self.exigencias), [])

    def test_erro_que_o_estudante_cometeu_pode_ser_apontado(self):
        casos = [
            ("O Creator está errado: Recibo é o Product, não o Creator.", "o creator seria o recibo"),
            ("Você confundiu o Creator com o Product.", "eu acho que o creator seria o recibo"),
            ("Seu if dentro de emitir() é o equívoco principal.", "eu colocaria um if dentro de emitir"),
            ("Um erro comum é colocar um if dentro de emitir(); fique atento.", TENTATIVA),
            ("Não há nenhum equívoco: Recibo é o Product. Quem seria o Creator?", TENTATIVA),
        ]
        for texto, fala in casos:
            with self.subTest(texto=texto):
                self.assertEqual(frases_atribuidas(texto, fala), [])

    def test_erro_sobre_parte_nao_respondida_e_barrado(self):
        for texto in ("Você acertou o Product, mas há um equívoco no Creator.",
                      "Você confundiu o Creator com o ConcreteCreator."):
            with self.subTest(texto=texto):
                self.assertTrue(frases_atribuidas(texto, TENTATIVA))


class PartesEExpressoesTest(unittest.TestCase):
    def test_avaliador_de_recibos(self):
        casos = {
            "o product seria o recibo": ({"Product": True}, []),
            "recibo pdf e recibo texto são os concret products": ({"ConcreteProducts": True}, []),
            "Recibo é o Product e ReciboPdf e ReciboTexto são os ConcreteProducts":
                ({"Product": True, "ConcreteProducts": True}, []),
            "o produto e o recibo e o criador e o emissor": ({"Product": True, "Creator": True}, []),
            "o creator seria o recibo": ({"Creator": False}, []),
            "o product seria o ReciboPdf": ({"Product": False}, []),
            "ConcreteCreators: ReciboPdf e ReciboTexto": ({"ConcreteCreators": False}, []),
            "Creator: EmissorRecibo (classe base que possui emitir() e declara criarRecibo())":
                ({"Creator": True}, []),
            "O Emissor teria um if dentro de emitir()": ({}, ["if"]),
        }
        for fala, (partes, erros) in casos.items():
            with self.subTest(fala=fala):
                av = avaliar_recibos(fala)
                self.assertEqual({p: parte.certo for p, parte in av.partes.items()}, partes)
                self.assertEqual(len(av.erros), len(erros))

    def test_proxima_pergunta_e_conclusao(self):
        self.assertIn("ConcreteProducts", avaliar_recibos("product seria o recibo").pergunta)
        tudo = ("Product: Recibo. ConcreteProducts: ReciboPdf e ReciboTexto. Creator: Emissor. "
                "ConcreteCreators: EmissorPdf e EmissorTexto.")
        self.assertIn("HTML", avaliar_recibos(tudo).pergunta)
        fim = avaliar_recibos(tudo + " Para HTML eu criaria ReciboHtml e EmissorHtml sem mudar emitir().")
        self.assertTrue(fim.concluido)
        self.assertIn("concluído", fim.texto())
        self.assertIn("ajustaria o Creator", avaliar_recibos("o creator seria o recibo").pergunta)

    def test_repeticao_de_resposta(self):
        anterior = ("Está correto que Recibo seria o Product. Agora, vamos avançar e perguntar quem "
                    "seriam os ConcreteProducts. Como elas diferenciam-se do Product base?")
        variacao = "Product é Recibo. " + anterior
        self.assertTrue(repete_resposta(variacao, anterior))
        self.assertFalse(repete_resposta(AVALIACAO_BOA, anterior))
        self.assertFalse(repete_resposta("Quem seria o Creator?", "Muito bem. Quem seria o Creator?"))


class OutrosExerciciosTest(unittest.TestCase):
    def test_simple_factory(self):
        casos = {
            # Resposta real do teste web; o modelo respondeu "Não está correto".
            "Não, não existe nenhuma subclasse sobrescrevendo um método de criação nesse código.":
                {"Sobrescrita": True},
            "Não.": {"Sobrescrita": True},
            "Sim, existe uma subclasse": {"Sobrescrita": False},
            "Ela está certa, é Factory Method": {"Veredito": False},
            "Não é Factory Method, é uma Simple Factory": {"Veredito": True, "Sobrescrita": True},
            "Eu criaria subclasses mas manteria o método static": {"Transformação": False},
            "Eu criaria subclasses de FabricaPagamento": {"Transformação": False},
            "Eu criaria uma classe Caixa com criarPagamento() e subclasses CaixaPix e CaixaCartao "
            "que sobrescrevem esse método.": {"Transformação": True},
        }
        for fala, esperado in casos.items():
            with self.subTest(fala=fala):
                av = avaliar_simple_factory(fala)
                self.assertEqual({p: parte.certo for p, parte in av.partes.items()}, esperado)

    def test_simple_factory_sequencia(self):
        primeira = avaliar_simple_factory("Não, não existe nenhuma subclasse sobrescrevendo um método de criação.")
        self.assertIn("ela está certa", primeira.pergunta)
        self.assertNotIn("Não está correto", primeira.texto())
        segunda = avaliar_simple_factory("Não, não existe nenhuma subclasse sobrescrevendo.\nNão.")
        self.assertIn("transformaria", segunda.pergunta)
        fim = avaliar_simple_factory(
            "Não existe subclasse.\nNão é factory method, é simple factory.\nEu criaria Caixa com "
            "criarPagamento() e subclasses CaixaPix e CaixaCartao que sobrescrevem esse método.")
        self.assertTrue(fim.concluido)

    def test_extensao(self):
        casos = {
            "Criaria uma classe Whatsapp que implementa Notificacao": {"Produto novo": True},
            "NotificadorWhatsapp implementa Notificacao": {"Produto novo": False},
            "NotificadorWhatsapp estende Notificador e sobrescreve criarNotificacao()": {"Criador novo": True},
            "Teria que alterar a interface Notificacao": {"O que muda": False},
            "Não precisa mudar nada, só o main": {"O que muda": True},
        }
        for fala, esperado in casos.items():
            with self.subTest(fala=fala):
                av = avaliar_extensao(fala)
                self.assertEqual({p: parte.certo for p, parte in av.partes.items()}, esperado)
        self.assertTrue(avaliar_extensao("Eu mudaria o avisar() para ter um if").erros)
        fim = avaliar_extensao("Whatsapp implementa Notificacao e NotificadorWhatsapp estende "
                               "Notificador.\nNenhuma classe existente precisa mudar, só o main.")
        self.assertTrue(fim.concluido)
        self.assertIn("concluído", fim.texto())

    def test_fluxo_do_segundo_exercicio(self):
        with TemporaryDirectory() as pasta, patch("agente.memoria.MEMORIA_DIR", Path(pasta)), \
                patch.dict("os.environ", {"CREWAI_STORAGE_DIR": str(Path(pasta) / "crewai")}):
            fluxo.executar_fluxo("Me de um exercício de factory method.", "s")
            outro = fluxo.executar_fluxo("Me de outro exercício", "s")
            self.assertIn("é Factory Method?", outro.resposta)
            errada = "Não está correto. Agora, vamos avançar para entender quem seria o Creator."
            with patch("agente.fluxo._executar", return_value=saida(errada, "texto solto")):
                resultado = fluxo.executar_fluxo(
                    "Não, não existe nenhuma subclasse sobrescrevendo um método de criação nesse código.", "s")
        self.assertEqual(resultado.intencao, "avaliacao")
        self.assertNotIn("Não está correto", resultado.resposta)
        self.assertIn("não há nenhuma subclasse", resultado.resposta)
        self.assertTrue(resultado.resposta.endswith("Que nome tem essa forma de criar objetos?"))


class SemPrefixoTest(unittest.TestCase):
    def test_tres_exercicios_sem_minha_resposta(self):
        # Pedido do usuário (04/11): responder sem "Minha resposta:".
        roteiro = [
            ("me de um exercício", "Product?"),
            ("o product seria o recibo", "os tipos concretos de recibo?"),
            ("ReciboPdf e ReciboTexto são os concrete products", "Qual classe seria o Creator"),
            ("o creator é o Emissor e os concrete creators são EmissorPdf e EmissorTexto", "HTML"),
            ("Eu criaria ReciboHtml e EmissorHtml, sem mexer em emitir()", "outro exercício"),
            ("me de outro exercício", "existe alguma subclasse"),
            ("Não existe", "ela está certa"),
            ("Não, é uma Simple Factory", "Como você transformaria"),
            ("Eu criaria uma classe Caixa e subclasses CaixaPix e CaixaCartao que sobrescrevem "
             "criarPagamento()", "outro exercício"),
            ("me de outro exercício", "produto WhatsApp"),
            ("Uma classe Whatsapp que implementa Notificacao", "qual classe nova cria"),
            ("NotificadorWhatsapp estende Notificador", "precisariam mudar"),
            ("Nenhuma, só o main muda", "outro exercício"),
        ]
        with TemporaryDirectory() as pasta, patch("agente.memoria.MEMORIA_DIR", Path(pasta)), \
                patch.dict("os.environ", {"CREWAI_STORAGE_DIR": str(Path(pasta) / "crewai")}), \
                patch("agente.fluxo._executar", return_value=saida("Muito bem.", "texto solto")):
            for pergunta, esperado in roteiro:
                with self.subTest(pergunta=pergunta):
                    self.assertIn(esperado, fluxo.executar_fluxo(pergunta, "s").resposta)


class ExercicioConcluidoTest(unittest.TestCase):
    def test_exercicio_concluido_encerra_a_pratica(self):
        with TemporaryDirectory() as pasta, patch("agente.memoria.MEMORIA_DIR", Path(pasta)), \
                patch.dict("os.environ", {"CREWAI_STORAGE_DIR": str(Path(pasta) / "crewai")}):
            fluxo.executar_fluxo("Me de um exercício de factory method.", "s")
            tudo = ("Product: Recibo. ConcreteProducts: ReciboPdf e ReciboTexto. Creator: Emissor. "
                    "ConcreteCreators: EmissorPdf e EmissorTexto. Para HTML eu criaria ReciboHtml e "
                    "EmissorHtml sem mudar emitir().")
            with patch("agente.fluxo._executar", return_value=saida("Muito bem, tudo certo.", "texto solto")):
                fim = fluxo.executar_fluxo(tudo, "s")
            self.assertTrue(fim.resposta.endswith("revisar algum ponto do Factory Method?"))
            self.assertEqual(MemoriaConversa("s").exercicio_pendente, "")


class NomesReservadosTest(unittest.TestCase):
    def setUp(self):
        self.exercicio = exercicio_por_id("recibos")
        self.reservados = nomes_reservados(self.exercicio.gabarito, self.exercicio.enunciado + TENTATIVA)

    def test_nomes_do_gabarito_sem_papeis_do_padrao(self):
        self.assertIn("EmissorPdf", self.reservados)
        self.assertIn("criarRecibo", self.reservados)
        self.assertNotIn("ConcreteProducts", self.reservados)
        nomes = nomes_reservados(exercicio_por_id("simple_factory").gabarito, "")
        self.assertNotIn("GoF", nomes)

    def test_nome_citado_pelo_estudante_nao_e_reservado(self):
        nomes = nomes_reservados(self.exercicio.gabarito, "Eu usaria EmissorPdf e ReciboPdf")
        self.assertNotIn("EmissorPdf", nomes)
        self.assertIn("EmissorTexto", nomes)

    def test_dica_curta_passa_e_solucao_inteira_e_problema(self):
        exigencias = Exigencias(reservados=self.reservados)
        self.assertEqual(encontrar_problemas(AVALIACAO_BOA, exigencias), [])
        dica = "Pense em ReciboPdf e ReciboTexto: o que eles têm em comum? Quem seria o Creator?"
        self.assertEqual(encontrar_problemas(dica, exigencias), [])
        self.assertTrue(encontrar_problemas(VAZAMENTO, exigencias))
        corrigido = corrigir_mecanicamente(VAZAMENTO, exigencias)
        self.assertEqual(encontrar_problemas(corrigido, exigencias), [])
        self.assertNotIn("EmissorPdf", corrigido)


if __name__ == "__main__":
    unittest.main()
