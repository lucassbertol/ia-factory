"""Integração dos prompts reais do CrewAI, sem fazer chamadas ao modelo."""
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from agente.conhecimento import EXEMPLOS, FATOS_EXEMPLOS, exercicio_por_id
from agente.crew import PlanoTurno, _descricao, montar_crew
from agente.agentes import NOMES, carregar_definicao
from agente.avaliacao_exercicio import avaliar_recibos


class PromptsReferenciaTest(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        ambiente = patch.dict("os.environ", {"CREWAI_STORAGE_DIR": pasta.name})
        ambiente.start()
        self.addCleanup(ambiente.stop)

    def test_autor_e_guardiao_recebem_selecao_e_fatos_do_exemplo(self):
        plano = PlanoTurno('Dê um exemplo em Java', 'exemplo', ['exemplificador'])
        plano.material['exemplificador'] = EXEMPLOS['basico'].bloco_markdown()
        plano.fatos['exemplificador'] = FATOS_EXEMPLOS['basico']
        crew = montar_crew(plano)
        autor, guardiao = crew.tasks
        for tarefa in (autor, guardiao):
            self.assertIn('Notificacao é o Product', tarefa.description)
            self.assertIn('public class ExemploFactoryMethod', tarefa.description)
            self.assertIn('## [distincoes]', tarefa.agent.backstory)
            self.assertNotIn('EmissorPdf', tarefa.agent.backstory)
            self.assertNotIn('public class', tarefa.agent.backstory)
            self.assertNotIn('## [comparacao]', tarefa.agent.backstory)

    def test_gabarito_so_na_tarefa_do_inquiridor(self):
        exercicio = exercicio_por_id('recibos')
        plano = PlanoTurno('Minha resposta: Recibo é Product', 'avaliacao', ['inquiridor'],
                           contexto=exercicio.enunciado, gabarito=exercicio.gabarito)
        crew = montar_crew(plano)
        self.assertIn(exercicio.gabarito, crew.tasks[0].description)
        self.assertNotIn(exercicio.gabarito, crew.tasks[1].description)
        self.assertNotIn(exercicio.gabarito, _descricao(plano, 'tutor'))
        for agente in crew.agents:
            self.assertNotIn('EmissorPdf', agente.backstory)

    def test_prompts_completos_e_documentacao_sincronizada(self):
        from pathlib import Path
        docs = (Path(__file__).resolve().parents[1] / 'docs/agentes.md').read_text()
        for nome in NOMES:
            definicao = carregar_definicao(nome)
            self.assertTrue(definicao.role and definicao.goal and definicao.backstory)
            for secao in ('ESCOPO', 'ESTRATÉGIA PEDAGÓGICA', 'EXEMPLOS', 'CASOS DE ERRO',
                          'REGRAS ANTI-ALUCINAÇÃO', 'FORMATO DAS RESPOSTAS'):
                self.assertIn(secao, definicao.instrucoes)
            from agente.prompts import carregar_prompt
            self.assertIn(carregar_prompt(nome).strip(), docs)

    def test_nivel_do_turno_e_exemplificador_sem_desafio(self):
        plano = PlanoTurno('Explique', 'conceito', ['tutor'], nivel='avancado')
        crew = montar_crew(plano)
        self.assertIn('Nível do estudante: avançado', crew.tasks[0].description)
        self.assertNotIn('Use frases curtas e linguagem de iniciante', crew.tasks[0].agent.backstory)
        definicao = carregar_definicao('exemplificador')
        self.assertNotIn('Termine pedindo', definicao.instrucoes)
        self.assertIn('Sem desafio nem pergunta', definicao.instrucoes)

    def test_avaliacao_verificada_redige_sem_receber_gabarito(self):
        exercicio = exercicio_por_id('recibos')
        plano = PlanoTurno('Recibo é Product', 'avaliacao', ['inquiridor'],
                          enunciado=exercicio.enunciado, gabarito=exercicio.gabarito,
                          avaliacao=avaliar_recibos('Recibo é Product'))
        plano.fatos['inquiridor'] = plano.avaliacao.fatos()
        crew = montar_crew(plano)
        self.assertIn('Não reavalie', crew.tasks[0].description)
        self.assertIn('o sistema acrescenta a próxima', crew.tasks[0].description)
        for tarefa in crew.tasks:
            self.assertNotIn(exercicio.gabarito, tarefa.description)


if __name__ == '__main__':
    unittest.main()
