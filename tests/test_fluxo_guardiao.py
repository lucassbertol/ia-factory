"""Testa decisão e persistência com crews reais e saídas controladas, sem Ollama."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from agente import fluxo
from agente.crew import PlanoTurno
from agente.erro import ErroModeloIndisponivel
from agente.memoria import MemoriaConversa

PERGUNTA = 'Explique uma vantagem do Factory Method.'
RUIM = 'O Creator apaga todos os objetos depois do uso. Quer um exemplo?'
BOM = 'A operação de negócio usa Product sem depender das classes concretas. Quer um exemplo?'
REFERENCIA = 'declara o factory method, que retorna Product.'


def revisao(status, autor='tutor', trecho=RUIM):
    problemas = []
    if status == 'REPROVADO':
        problemas = [dict(autor=autor, tipo='erro', trecho=trecho, referencia=REFERENCIA,
                          correcao='Explique que o Creator declara o factory method.')]
    return json.dumps(dict(veredito=status, problemas=problemas), ensure_ascii=False)


def saida(*textos):
    return SimpleNamespace(tasks_output=[SimpleNamespace(raw=t) for t in textos], raw=textos[-1])


class FluxoGuardiaoTest(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.raiz = Path(pasta.name)
        for alvo, valor in [('agente.memoria.MEMORIA_DIR', self.raiz / 'sessoes')]:
            ctx = patch(alvo, valor); ctx.start(); self.addCleanup(ctx.stop)
        ctx = patch.dict('os.environ', {'CREWAI_STORAGE_DIR': str(self.raiz / 'crewai')})
        ctx.start(); self.addCleanup(ctx.stop)
        self.crews = []

    def rodar(self, *saidas, pergunta=PERGUNTA):
        fila = iter(saidas)
        def executar(montar):
            self.crews.append(montar())
            item = next(fila)
            if isinstance(item, Exception):
                raise item
            return item
        with patch('agente.fluxo._executar', side_effect=executar):
            return fluxo.executar_fluxo(pergunta, 'teste')

    def assert_bloqueada(self, resultado):
        self.assertEqual(resultado.tipo, 'orientacao')
        self.assertIn('Não consegui validar', resultado.resposta)
        self.assertNotIn('apaga todos', resultado.resposta)
        self.assertTrue(resultado.revisao['bloqueada'])
        salvo = MemoriaConversa('teste').historico[-1]
        self.assertEqual(salvo['resposta'], resultado.resposta)
        self.assertNotIn(RUIM, MemoriaConversa('teste').contexto_texto())

    def test_aprovada_exibida(self):
        resultado = self.rodar(saida(BOM, revisao('APROVADO')))
        self.assertIn(BOM, resultado.resposta)
        self.assertFalse(resultado.revisao['bloqueada'])
        self.assertEqual(len(self.crews), 1)

    def test_reescrita_so_exibida_depois_da_segunda_aprovacao(self):
        resultado = self.rodar(saida(RUIM, revisao('REPROVADO')), saida(BOM),
                              saida(revisao('APROVADO')))
        self.assertIn(BOM, resultado.resposta)
        self.assertNotIn(RUIM, resultado.resposta)
        self.assertTrue(resultado.revisao['reescrito'])
        self.assertEqual(len(resultado.revisao['tentativas']), 2)
        self.assertEqual(len(self.crews), 3)
        segunda_revisao = self.crews[-1].tasks[0].description
        self.assertIn(BOM, segunda_revisao)
        self.assertNotIn(RUIM, segunda_revisao)
        self.assertEqual(self.crews[1].tasks[0].guardrail_max_retries, 0)

    def test_segunda_reprovacao_bloqueia_sem_terceira_tentativa(self):
        resultado = self.rodar(saida(RUIM, revisao('REPROVADO')), saida(RUIM),
                              saida(revisao('REPROVADO')))
        self.assert_bloqueada(resultado)
        self.assertEqual(len(self.crews), 3)

    def test_inconclusiva_invalida_e_critica_inventada_nao_reescrevem(self):
        for bruto in (revisao('INCONCLUSIVO'), 'VEREDITO: APROVADO',
                      revisao('REPROVADO', trecho='Trecho inventado pelo revisor')):
            with self.subTest(bruto=bruto):
                self.crews = []
                self.assert_bloqueada(self.rodar(saida(RUIM, bruto)))
                self.assertEqual(len(self.crews), 1)

    def test_falha_na_segunda_revisao_nao_entrega_rascunho(self):
        resultado = self.rodar(saida(RUIM, revisao('REPROVADO')), saida(BOM),
                              ErroModeloIndisponivel('timeout'))
        self.assert_bloqueada(resultado)

    def test_validacao_deterministica_impede_aprovacao_de_texto_vazio(self):
        self.assert_bloqueada(self.rodar(saida('', revisao('APROVADO'))))

    def test_segunda_revisao_inconclusiva_ou_invalida_bloqueia(self):
        for bruto in (revisao('INCONCLUSIVO'), '{json truncado'):
            with self.subTest(bruto=bruto):
                self.assert_bloqueada(self.rodar(saida(RUIM, revisao('REPROVADO')),
                                                 saida(BOM), saida(bruto)))

    def test_correcao_vazia_e_falha_tecnica_nao_sao_exibidas(self):
        for nova in (saida(''), ErroModeloIndisponivel('falha ao corrigir')):
            with self.subTest(nova=nova):
                self.crews = []
                self.assert_bloqueada(self.rodar(saida(RUIM, revisao('REPROVADO')), nova))
                self.assertEqual(len(self.crews), 2)

    def test_erro_conhecido_bloqueia_mesmo_com_aprovacao(self):
        texto = 'O Creator precisa ser abstrato. Quer saber mais?'
        self.assert_bloqueada(self.rodar(saida(texto, revisao('APROVADO'))))

    def test_limite_zero_bloqueia_sem_reescrever(self):
        with patch('agente.fluxo.MAX_REESCRITAS_GUARDIAO', 0):
            self.assert_bloqueada(self.rodar(saida(RUIM, revisao('REPROVADO'))))
        self.assertEqual(len(self.crews), 1)

    def test_corrige_autor_citado_e_revisa_conjunto(self):
        plano = PlanoTurno(PERGUNTA, 'conceito', ['tutor', 'exemplificador'])
        with patch('agente.fluxo._planejar', return_value=(plano, '')):
            resultado = self.rodar(saida(RUIM, BOM, revisao('REPROVADO')), saida(BOM),
                                  saida(revisao('APROVADO')))
        self.assertNotIn(RUIM, resultado.resposta)
        self.assertIn('Tutor', self.crews[1].tasks[0].agent.role)
        self.assertIn('exemplificador', self.crews[-1].tasks[0].description)

    def test_exercicio_e_recusa_continuam_sem_modelo(self):
        with patch('agente.fluxo._executar', side_effect=AssertionError('Não deve chamar IA')):
            exercicio = fluxo.executar_fluxo('Proponha um exercício de Factory Method', 'pratica')
            recusa = fluxo.executar_fluxo('Invente um padrão Z', 'recusa')
        self.assertIn('recibos', exercicio.resposta)
        self.assertEqual(recusa.tipo, 'orientacao')

    def test_bloqueio_nao_conta_como_conteudo_estudado(self):
        self.assert_bloqueada(self.rodar(saida(BOM, revisao('INCONCLUSIVO'))))
        self.assertEqual(MemoriaConversa('teste').topicos_estudados, [])

    def test_fechamento_bloqueado_preserva_exercicio_pendente(self):
        exercicio = fluxo.executar_fluxo('Proponha um exercício de Factory Method', 'teste')
        self.assert_bloqueada(self.rodar(saida(BOM, revisao('INCONCLUSIVO')),
                                        pergunta='Faça um resumo final do Factory Method'))
        self.assertEqual(MemoriaConversa('teste').exercicio_pendente, exercicio.resposta)
