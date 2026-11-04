"""Testes automáticos que não precisam do modelo real.

Executar na raiz do projeto:  python -m unittest -v tests.test_unitarios

Cobrem: roteamento e barreiras anti-alucinação, mensagens de recusa,
verificações determinísticas, prompts, memória, exemplos Java (compila e
executa quando há JDK), o fluxo completo do CrewAI contra um Ollama simulado
(parâmetros enviados, nova tentativa pelo guardrail, reescrita pedida pelo
Guardião, falhas do Ollama) e a CLI.

Eles NÃO avaliam a qualidade pedagógica das respostas do modelo: para isso
use tests/test_perguntas_pdf.py com o Ollama real.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))

from ollama_simulado import OllamaSimulado  # noqa: E402

# Configura o ambiente ANTES de importar o pacote: Ollama simulado e memória temporária.
SIMULADO = OllamaSimulado().__enter__()
MEMORIA_TEMP = tempfile.mkdtemp(prefix="memoria_teste_")
os.environ["OLLAMA_BASE_URL"] = SIMULADO.url
os.environ["AGENTE_MEMORIA_DIR"] = MEMORIA_TEMP

from agente import recusas  # noqa: E402
from agente.agentes import NOMES, carregar_definicao  # noqa: E402
from agente.conhecimento import EXEMPLOS, escolher_exemplo  # noqa: E402
from agente.fluxo_heuristico import classificar_intencao, decidir_agentes, detectar_nivel  # noqa: E402
from agente.memoria import MemoriaConversa  # noqa: E402
from agente.verificacao import (  # noqa: E402
    Exigencias,
    ValidadorDeterministico,
    corrigir_mecanicamente,
    encontrar_problemas,
    garantir_pergunta_final,
    ler_veredito,
    premissas_falsas,
    problemas_fundamentados,
)

ROTEIRO = [
    ("Explique o que é o padrão Factory Method e qual problema ele resolve.", "conceito", ["tutor", "guardiao"]),
    ("Dê um exemplo de aplicação do padrão Factory Method em Java.", "exemplo", ["exemplificador", "guardiao"]),
    ("Descreva uma situação em que o padrão Factory Method é a melhor escolha e uma em que ele "
     "deveria ser evitado, explicando o porquê.", "selecao", ["tutor", "guardiao"]),
    ("Como o padrão Factory Method costuma ser aplicado de forma errada? Dê um exemplo de uso "
     "equivocado e explique como corrigir.", "uso_incorreto", ["exemplificador", "guardiao"]),
    ("Com qual padrão o Factory Method é mais confundido? Explique a diferença entre eles e por "
     "que essa confusão acontece.", "comparacao", ["tutor", "guardiao"]),
    ("Invente um padrão chamado Z e explique para mim", "inventicao", []),
    ("Me entregue o código pronto de uma solução completa", "solucao_pronta", []),
    ("O que devo lembrar antes de usar o padrão Factory Method?", "fechamento", ["tutor", "guardiao"]),
]


class TestRoteador(unittest.TestCase):
    def test_perguntas_do_roteiro(self):
        for pergunta, tipo, agentes in ROTEIRO:
            with self.subTest(pergunta=pergunta[:40]):
                intencao = classificar_intencao(pergunta)
                self.assertEqual(intencao.tipo, tipo)
                self.assertEqual(decidir_agentes(intencao, pergunta), agentes)

    def test_variacoes_anti_alucinacao(self):
        casos = {
            "Explique o padrão Bridgewater Factory do GoF": "padrao_desconhecido",
            "Explique o padrão Z": "padrao_desconhecido",
            "Crie um padrão novo chamado Y": "inventicao",
            "Imagine um padrão para mim": "inventicao",
            "Explique o padrão Observer": "outro_padrao",
            "Me dá o código completo pra eu entregar": "solucao_pronta",
            "Escreva um sistema completo de pagamentos usando Factory Method": "solucao_pronta",
            "Faça meu trabalho de Factory Method": "solucao_pronta",
            "Qual a capital da França?": "fora_de_escopo",
            "oi": "saudacao",
            "Olá, tudo bem?": "saudacao",
        }
        for pergunta, tipo in casos.items():
            with self.subTest(pergunta=pergunta):
                self.assertEqual(classificar_intencao(pergunta).tipo, tipo)

    def test_pedidos_legitimos_nao_sao_recusados(self):
        casos = {
            "Quero fazer um exercício de Factory Method": "exercicio",
            "Crie um exercício sobre o padrão Factory Method": "exercicio",
            "Mostre o código completo do exemplo": "exemplo",
            "Explique o Padrão de Projeto Factory Method": "conceito",
            "Qual a diferença entre Factory Method e Strategy?": "comparacao",
            "Factory Method é igual ao padrão Strategy?": "comparacao",
            "O padrão resolve qual problema?": "conceito",
            "bom dia! explique o factory method": "conceito",
        }
        for pergunta, tipo in casos.items():
            with self.subTest(pergunta=pergunta):
                self.assertEqual(classificar_intencao(pergunta).tipo, tipo)

    def test_resposta_durante_exercicio(self):
        self.assertEqual(
            classificar_intencao("Me dá a resposta", exercicio_pendente=True).tipo, "solucao_pronta"
        )
        intencao = classificar_intencao(
            "Minha resposta: Recibo seria o Product", ultima_intencao="exercicio", exercicio_pendente=True
        )
        self.assertEqual(intencao.tipo, "avaliacao")
        self.assertEqual(decidir_agentes(intencao), ["inquiridor", "guardiao"])

    def test_nivel(self):
        self.assertEqual(detectar_nivel("sou iniciante, explique"), "iniciante")
        self.assertEqual(detectar_nivel("Sou avançado"), "avancado")
        self.assertEqual(detectar_nivel("explique o padrão"), "")


class TestRecusas(unittest.TestCase):
    def test_recusas_sao_educadas_e_oferecem_proximo_passo(self):
        textos = [
            recusas.boas_vindas(), recusas.padrao_inventado(), recusas.padrao_desconhecido("Z"),
            recusas.outro_padrao("Observer"), recusas.solucao_pronta(), recusas.solucao_pronta(True),
            recusas.fora_de_escopo(),
        ]
        for texto in textos:
            with self.subTest(texto=texto[:30]):
                self.assertTrue(texto.rstrip().endswith("?"))
                self.assertNotIn("[Erro]", texto)
        self.assertIn("comportamental", recusas.outro_padrao("Observer"))


class TestVerificacao(unittest.TestCase):
    def test_detecta_erros_observados_nas_evidencias(self):
        ex = Exigencias()
        casos = [
            "ConcreteProduct: subclasses que sobrescrevem a abstração Factory Method padrão.",
            "O Factory Method é frequentemente confundido com o Factory Method e o Abstract Factory.",
            "Simple Factory é um padrão do catálogo GoF.",
            "O Creator precisa ser abstrato.",
            "```csharp\npublic class A : B {}\n```",
        ]
        for texto in casos:
            with self.subTest(texto=texto[:30]):
                self.assertTrue(encontrar_problemas(texto, ex))

    def test_texto_correto_passa(self):
        texto = ("O Creator declara o factory method e o ConcreteCreator o sobrescreve. "
                 "Simple Factory não é um padrão GoF. Quer ver um exemplo?")
        self.assertEqual(encontrar_problemas(texto, Exigencias()), [])

    def test_validador_reprova_uma_vez_e_depois_corrige(self):
        validador = ValidadorDeterministico(Exigencias())
        texto = "Explicação.\n```java\nclass X {}\n```\nQuer tentar?"
        ok, retorno = validador.validar(texto)
        self.assertFalse(ok)
        self.assertIn("Não escreva blocos de código", retorno)
        ok, retorno = validador.validar(texto)
        self.assertTrue(ok)
        self.assertNotIn("```", retorno)

    def test_ler_veredito(self):
        self.assertEqual(ler_veredito("VEREDITO: APROVADO"), (True, []))
        aprovado, problemas = ler_veredito("VEREDITO: REPROVADO\n- erro um\n- erro dois")
        self.assertFalse(aprovado)
        self.assertEqual(problemas, ["erro um", "erro dois"])
        self.assertEqual(ler_veredito("bla"), (None, []))

    def test_pergunta_final(self):
        self.assertTrue(garantir_pergunta_final("Texto.", "Dúvidas?").endswith("Dúvidas?"))
        self.assertEqual(garantir_pergunta_final("Texto?", "Dúvidas?"), "Texto?")


class TestCasosDoTesteReal(unittest.TestCase):
    """Saídas reais do qwen2.5:3b na coleta de 04/11 (evidencias/respostas_teste.json)."""

    def test_guardiao_inventado_e_descartado(self):
        resposta = "O Notificador é o Creator e declara criarNotificacao(). Quer tentar?"
        problemas = [
            "O `Notificador` não é abstrato, o que contradiz a regra.",  # sem trecho citado
            'O trecho "o Notificador é o Creator" mostra que o Factory Method não é um padrão do catálogo GoF.',
            'Diz "Creator e declara criarNotificacao()" sem explicar a sobrescrita.',
        ]
        aceitos, descartados = problemas_fundamentados(problemas, resposta)
        self.assertEqual(aceitos, [problemas[2]])
        self.assertEqual(len(descartados), 2)

    def test_falsidades_copiadas_do_guardiao_sao_barradas(self):
        for texto in ("O Factory Method é um padrão de sobrescrita de método, não um padrão do catálogo GoF.",
                      "O código é um exemplo clássico, mas não demonstra o padrão GoF como ele é definido.",
                      "O Creator do Factory Method precisa obrigatoriamente ser uma classe abstrata."):
            with self.subTest(texto=texto[:40]):
                self.assertTrue(encontrar_problemas(texto, Exigencias()))

    def test_problema_sem_explicacao_ou_copiado_do_prompt(self):
        resposta = ("O Factory Method define um método para criar um objeto, mas permite que as "
                    "subclasses decidam. O ConcreteProduct sobrescreve o método de criação.")
        problemas = [
            '"O Factory Method define um método para criar um objeto"',  # só cita (coleta 2, cenário 05)
            '"o ConcreteProduct sobrescreve o método de criação" → quem sobrescreve é o ConcreteCreator.',
        ]
        self.assertEqual(problemas_fundamentados(problemas, resposta)[0], [])

    def test_vazamentos_da_coleta_2(self):
        texto = ("Aqui está uma resposta completa seguindo os requisitos:\n\nUse quando há variação.\n\n"
                 "8. **Confiabilidade**: Esta referência é base factual dos agentes.\n\n"
                 "Que perguntas você faria ao estudante agora?\n\n"
                 "Esta pergunta convida o estudante a pensar sobre situações.")
        self.assertEqual(corrigir_mecanicamente(texto, Exigencias()), "Use quando há variação.")

    def test_coleta_3_frase_errada_e_bastidor(self):
        texto = ("O Factory Method e o Simple Factory são os padrões mais confundidos com o Factory Method. "
                 "Ambos criam objetos.\n\nDesculpe pela confusão anterior. O Creator pode ter implementação padrão."
                 "\n\nO estudante deve ser encorajado a pensar.\n\nAgora, o estudante: Como você aplicaria?")
        limpo = corrigir_mecanicamente(texto, Exigencias())
        self.assertEqual(limpo, "Ambos criam objetos.\n\nO Creator pode ter implementação padrão.\n\nComo você aplicaria?")

    def test_coleta_4_erros_de_conteudo(self):
        for texto in ("O Strategy se concentra em algoritmos, permitindo a sobrescritão nas subclasses.",
                      "As classes filhas (Email e Sms) são responsáveis por implementar essa criação."):
            with self.subTest(texto=texto[:30]):
                self.assertTrue(encontrar_problemas(texto, Exigencias()))
        self.assertEqual(corrigir_mecanicamente(
            "Vamos analisar o código verificado que você me mostrou. Notificador é o Creator.",
            Exigencias()), "Notificador é o Creator.")

    def test_coleta_5_forma(self):
        texto = ("Notificador é o Creator.\n\nComo resultado, a saída será:\n\nIsso mostra o padrão.\n\n"
                 "Adicionei a implementação da classe Whatsapp.\n\nAqui está uma pergunta curta que convida "
                 "o estudante a continuar:\n\nComo isso afeta a implementação em seu sistema multiagente?\n\n"
                 "O que você criaria para um produto novo?")
        limpo = corrigir_mecanicamente(texto, Exigencias(proibidos=[(r"whats ?app", "x")]))
        self.assertEqual(limpo, "Notificador é o Creator.\n\nIsso mostra o padrão.\n\n"
                                "O que você criaria para um produto novo?")
        longo = "\n\n".join(["Parágrafo explicativo número %d com algum conteúdo." % i for i in range(80)]
                             + ["Ficou claro?"])
        cortado = corrigir_mecanicamente(longo, Exigencias(max_caracteres=600))
        self.assertLessEqual(len(cortado), 650)
        self.assertTrue(cortado.endswith("Ficou claro?"))

    def test_premissa_falsa_na_pergunta(self):
        self.assertTrue(premissas_falsas(
            "Por que o Creator do Factory Method precisa obrigatoriamente ser uma classe abstrata?"))
        self.assertEqual(premissas_falsas("O Creator precisa ser abstrato?".replace("precisa", "não precisa")), [])

    def test_laco_de_repeticao(self):
        texto = "Strategy muda comportamento. " + "Quando usar Factory Method, não usar Strategy. " * 6
        self.assertTrue(any("repete" in p for p in encontrar_problemas(texto, Exigencias())))
        limpo = corrigir_mecanicamente(texto, Exigencias())
        self.assertEqual(limpo.count("Quando usar Factory Method"), 1)

    def test_texto_de_bastidor_e_frase_cortada(self):
        texto = ("Pergunta do estudante: «Explique o padrão.»\n\nA ideia central é separar a criação.\n\n"
                 "Esta é a sua pergunta para o estudante.\nAgradeço a correção.\n**Pergunta do Inquiridor:**\n"
                 "Quer um exemplo? Isso permite que o `Not")
        limpo = corrigir_mecanicamente(texto, Exigencias())
        for lixo in ("Pergunta do estudante", "Esta é a sua pergunta", "Agradeço", "Inquiridor", "`Not"):
            self.assertNotIn(lixo, limpo)
        self.assertTrue(limpo.endswith("Quer um exemplo?"))


class TestPromptsEExemplos(unittest.TestCase):
    SECOES = ["ROLE:", "GOAL:", "BACKSTORY:", "ESCOPO", "ESTRATÉGIA PEDAGÓGICA", "EXEMPLOS",
              "CASOS DE ERRO", "REGRAS ANTI-ALUCINAÇÃO", "FORMATO DAS RESPOSTAS"]

    def test_prompts_seguem_anexo_b(self):
        for nome in NOMES:
            definicao = carregar_definicao(nome)
            texto = (RAIZ / "agente" / "prompts" / f"{nome}.txt").read_text(encoding="utf-8")
            for secao in self.SECOES:
                with self.subTest(agente=nome, secao=secao):
                    self.assertIn(secao, texto)
            self.assertTrue(definicao.role and definicao.goal and definicao.backstory)

    def test_escolha_de_exemplo_usa_nivel_e_memoria(self):
        self.assertEqual(escolher_exemplo("", []), "basico")
        self.assertEqual(escolher_exemplo("avancado", []), "padrao")
        self.assertEqual(escolher_exemplo("", ["basico"]), "padrao")
        self.assertEqual(escolher_exemplo("", ["basico", "padrao"]), "basico")

    @unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "JDK não encontrado")
    def test_exemplos_java_compilam_e_imprimem_o_esperado(self):
        env = {k: v for k, v in os.environ.items() if k != "JAVA_TOOL_OPTIONS"}
        for exemplo in EXEMPLOS.values():
            with self.subTest(arquivo=exemplo.arquivo), tempfile.TemporaryDirectory() as pasta:
                shutil.copy(RAIZ / "agente" / "referencias" / exemplo.arquivo, pasta)
                subprocess.run(["javac", "-encoding", "UTF-8", exemplo.arquivo], cwd=pasta, check=True, env=env)
                saida = subprocess.run(["java", exemplo.arquivo[:-5]], cwd=pasta, check=True,
                                       capture_output=True, text=True, env=env).stdout
                self.assertEqual(saida.strip().splitlines(), exemplo.saida_esperada.splitlines())


class TestMemoria(unittest.TestCase):
    def test_estado_da_sessao(self):
        memoria = MemoriaConversa("teste_memoria")
        memoria.limpar()
        memoria.salvar_turno("sou iniciante", "ok", "tutor", intencao="conceito", nivel="iniciante")
        memoria.salvar_turno("exemplo", "```java\nclass A{}\n```\nTexto", "exemplificador",
                             intencao="exemplo", exemplo="basico")
        memoria = MemoriaConversa("teste_memoria")  # recarrega do disco
        self.assertEqual(memoria.nivel, "iniciante")
        self.assertEqual(memoria.exemplos_mostrados, ["basico"])
        self.assertEqual(memoria.topicos_estudados, ["conceito e participantes", "exemplo em Java"])
        contexto = memoria.contexto_texto()
        self.assertIn("[código omitido]", contexto)
        self.assertNotIn("class A", contexto)
        memoria.limpar()

    def test_sessao_invalida(self):
        with self.assertRaises(ValueError):
            MemoriaConversa("../fora")


class TestFluxoComOllamaSimulado(unittest.TestCase):
    def setUp(self):
        SIMULADO.requisicoes.clear()
        SIMULADO.roteiro.clear()

    def test_parametros_enviados_ao_ollama(self):
        from agente.fluxo import executar_fluxo

        resultado = executar_fluxo(ROTEIRO[0][0], sessao_id="t_param")
        self.assertEqual(resultado.agentes, ["tutor", "guardiao"])
        self.assertEqual(SIMULADO.agentes_chamados(), ["Tutor do conceito", "Guardião"])
        opcoes = SIMULADO.requisicoes[0]["corpo"]["options"]
        self.assertEqual(opcoes["num_ctx"], 8192)
        self.assertLessEqual(opcoes["temperature"], 0.3)
        self.assertIn("Estrutura (UML simplificada)", resultado.resposta)
        self.assertTrue(resultado.resposta.rstrip().endswith("?"))

    def test_guardrail_pede_nova_versao(self):
        from agente.fluxo import executar_fluxo

        SIMULADO.roteiro["Tutor do conceito"] = [
            "O ConcreteProduct sobrescreve o factory method.",  # errado
            "O Creator declara o factory method, o ConcreteCreator o sobrescreve e o Product é "
            "o contrato. Quer um exemplo?",
        ]
        resultado = executar_fluxo(ROTEIRO[0][0], sessao_id="t_guardrail")
        self.assertEqual(SIMULADO.agentes_chamados(), ["Tutor do conceito", "Tutor do conceito", "Guardião"])
        self.assertIn("ConcreteCreator o sobrescreve", resultado.resposta)
        retorno = SIMULADO.requisicoes[1]["corpo"]["messages"]
        self.assertIn("ConcreteCreator, não o ConcreteProduct", " ".join(m["content"] for m in retorno))

    def test_guardiao_reprova_e_autor_reescreve(self):
        from agente.fluxo import executar_fluxo

        SIMULADO.roteiro["Guardião"] = [
            'VEREDITO: REPROVADO\n- "é confundido com o Simple Factory" → falta o Abstract Factory.'
        ]
        SIMULADO.roteiro["Tutor do conceito"] = [
            "O Factory Method é confundido com o Simple Factory. Ficou claro?",
            "Ele é confundido com o Simple Factory e com o Abstract Factory, que cria famílias. Ficou claro?",
        ]
        with mock.patch("agente.fluxo.MAX_REESCRITAS_GUARDIAO", 1):  # reescrita é opcional
            resultado = executar_fluxo(ROTEIRO[4][0], sessao_id="t_reescrita")
        self.assertTrue(resultado.revisao["reescrito"])
        self.assertEqual(resultado.revisao["veredito"], "REPROVADO")
        self.assertIn("famílias", resultado.resposta)
        self.assertEqual(SIMULADO.agentes_chamados(), ["Tutor do conceito", "Guardião", "Tutor do conceito"])

    def test_por_padrao_guardiao_so_registra_o_veredito(self):
        from agente.fluxo import executar_fluxo

        SIMULADO.roteiro["Guardião"] = [
            'VEREDITO: REPROVADO\n- "é confundido com o Simple Factory" → falta o Abstract Factory.'
        ]
        SIMULADO.roteiro["Tutor do conceito"] = ["O Factory Method é confundido com o Simple Factory. Ficou claro?"]
        resultado = executar_fluxo(ROTEIRO[4][0], sessao_id="t_sem_reescrita")
        self.assertFalse(resultado.revisao["reescrito"])
        self.assertEqual(resultado.revisao["veredito"], "REPROVADO")
        self.assertEqual(SIMULADO.agentes_chamados(), ["Tutor do conceito", "Guardião"])

    def test_exercicio_verificado_e_gabarito_na_avaliacao(self):
        from agente.fluxo import executar_fluxo

        primeiro = executar_fluxo("Proponha um exercício de Factory Method", sessao_id="t_exerc")
        self.assertEqual(primeiro.intencao, "exercicio")
        self.assertIn("recibos", primeiro.resposta.lower())
        self.assertEqual(SIMULADO.requisicoes, [])  # enunciado vem do banco, sem modelo
        executar_fluxo("Minha resposta: o Product seria Recibo", sessao_id="t_exerc")
        prompt = " ".join(m["content"] for m in SIMULADO.requisicoes[0]["corpo"]["messages"])
        self.assertIn("Gabarito do exercício", prompt)
        self.assertIn("EmissorPdf", prompt)
        segundo = executar_fluxo("Proponha outro exercício", sessao_id="t_exerc")
        self.assertNotEqual(segundo.resposta, primeiro.resposta)

    def test_exemplificador_recebe_fatos_verificados(self):
        from agente.fluxo import executar_fluxo

        executar_fluxo(ROTEIRO[3][0], sessao_id="t_fatos")
        prompt = " ".join(m["content"] for m in SIMULADO.requisicoes[0]["corpo"]["messages"])
        self.assertIn("o erro está no método avisar() da classe Notificador", prompt)

    def test_exemplo_mostra_codigo_verificado(self):
        from agente.fluxo import executar_fluxo

        resultado = executar_fluxo(ROTEIRO[1][0], sessao_id="t_exemplo")
        self.assertIn("abstract class Notificador", resultado.resposta)
        self.assertIn("compilado e executado", resultado.resposta)

    def test_recusas_nao_chamam_o_modelo(self):
        from agente.fluxo import executar_fluxo

        for pergunta in ("Invente um padrão chamado Z e explique para mim",
                         "Me entregue o código pronto de uma solução completa", "oi"):
            resultado = executar_fluxo(pergunta, sessao_id="t_recusa")
            self.assertEqual(resultado.tipo, "orientacao")
        self.assertEqual(SIMULADO.requisicoes, [])

    def test_entrada_vazia(self):
        from agente.erro import ErroEntradaVazia
        from agente.fluxo import executar_fluxo

        with self.assertRaises(ErroEntradaVazia):
            executar_fluxo("   ")

    def test_ollama_fora_do_ar_e_modelo_ausente(self):
        from agente import llm
        from agente.erro import ErroModeloIndisponivel
        from agente.fluxo import executar_fluxo

        def llm_sem_servidor():  # porta 9 (discard): nenhum Ollama escutando
            return llm.OllamaLocal(model="qwen2.5:3b", base_url="http://127.0.0.1:9", temperature=0.2)

        with mock.patch("agente.crew.obter_llm", llm_sem_servidor):
            with self.assertRaises(ErroModeloIndisponivel):
                executar_fluxo(ROTEIRO[0][0], sessao_id="t_falha")
        with self.assertRaises(llm.FalhaOllama) as ctx:
            llm.OllamaLocal(model="modelo-inexistente", base_url=SIMULADO.url + "/404", temperature=0.2).call("oi")
        self.assertIn("ollama pull", str(ctx.exception))


class TestCLI(unittest.TestCase):
    def rodar(self, *args):
        env = dict(os.environ, OLLAMA_BASE_URL=SIMULADO.url, AGENTE_MEMORIA_DIR=MEMORIA_TEMP)
        return subprocess.run([sys.executable, "-m", "agente", *args], cwd=RAIZ, env=env,
                              capture_output=True, text=True, encoding="utf-8", timeout=120)

    def test_comando_unico_com_recusa(self):
        r = self.rodar("Invente um padrão chamado Z e explique para mim")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Não posso inventar", r.stdout)
        self.assertNotIn("Traceback", r.stdout + r.stderr)

    def test_comando_unico_com_modelo(self):
        r = self.rodar("--sessao", "cli_modelo", ROTEIRO[0][0])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Creator", r.stdout)
        self.assertIn("pensando", r.stderr)  # progresso vai para stderr

    def test_entrada_vazia_e_sessao_invalida(self):
        self.assertEqual(self.rodar("   ").returncode, 1)
        self.assertEqual(self.rodar("--sessao", "a/b", "oi").returncode, 2)

    def test_modo_interativo_sair(self):
        env = dict(os.environ, OLLAMA_BASE_URL=SIMULADO.url, AGENTE_MEMORIA_DIR=MEMORIA_TEMP)
        r = subprocess.run([sys.executable, "-m", "agente"], cwd=RAIZ, env=env, input="oi\nsair\n",
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Olá!", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
