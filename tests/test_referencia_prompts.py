"""Integração dos prompts reais do CrewAI, sem fazer chamadas ao modelo."""
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from agente.conhecimento import EXEMPLOS, FATOS_EXEMPLOS, exercicio_por_id
from agente.crew import PlanoTurno, _descricao, montar_crew


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


if __name__ == '__main__':
    unittest.main()
