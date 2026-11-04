"""Leitura da referência e isolamento do conteúdo reservado, sem Ollama."""
import unittest
from agente import conhecimento as c


class ReferenciaTest(unittest.TestCase):
    def test_selecao_nao_expoe_exercicios_nem_gabaritos(self):
        for intencao in ('conceito', 'exemplo', 'comparacao', 'avaliacao', 'fechamento'):
            texto = c.carregar_referencia(intencao)
            self.assertIn('ConcreteCreator', texto)
            self.assertNotIn('EmissorPdf', texto)
            self.assertNotIn('Gabarito', texto)
            self.assertNotIn('public class', texto)
        self.assertIn('famílias', c.carregar_referencia('comparacao'))
        self.assertNotIn('## [comparacao]', c.carregar_referencia('exemplo'))

    def test_parser_preserva_titulos_dentro_do_codigo(self):
        secoes = c._ler_secoes('## [teste] Teste\n```text\n## [falso] Dado\n```\n## [fim] Fim\ntexto')
        self.assertEqual(list(secoes), ['teste', 'fim'])
        self.assertIn('## [falso]', secoes['teste'])

    def test_parser_rejeita_secoes_invalidas(self):
        for texto in ('## [x] X\n\n', '## [x] X\na\n## [x] X\nb', '## [x] X\n```java\na'):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                c._ler_secoes(texto)

    def test_campo_ausente_tem_erro_claro(self):
        with self.assertRaisesRegex(ValueError, 'ausente.*exemplo:basico:codigo'):
            c._obter({}, 'exemplo:basico:codigo')

    def test_bloco_invalido_nao_vira_codigo_exibido(self):
        for texto in ('texto sem cerca', '```java\n\n```', '```text\nconteudo\n```'):
            with self.subTest(texto=texto), self.assertRaisesRegex(ValueError, 'Bloco java inválido'):
                c._bloco({'codigo': texto}, 'codigo', 'java')

    def test_material_carregado_do_markdown(self):
        self.assertEqual(c.EXEMPLOS['basico'].saida_esperada, 'Email para Ana\nSMS para Bia')
        self.assertIn('public class ExemploFactoryMethod', c.EXEMPLOS['basico'].codigo)
        self.assertIn('Product: Recibo', c.exercicio_por_id('recibos').gabarito)
        self.assertNotIn('Product: Recibo', c.exercicio_por_id('recibos').enunciado)
        self.assertEqual(c.escolher_exercicio(['recibos']).ident, 'simple_factory')


if __name__ == '__main__':
    unittest.main()
