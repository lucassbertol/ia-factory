import json
import unittest
from agente import verificacao as v

BASE = 'Quem sobrescreve o factory method é o ConcreteCreator (nunca o ConcreteProduct).'
TEXTO = 'O ConcreteProduct sobrescreve o factory method.'
PERGUNTA = 'Explique os participantes e uma vantagem do Factory Method.'


def erro(autor='tutor'):
    return dict(autor=autor, tipo='erro', trecho=TEXTO,
                referencia=BASE, correcao='Atribua a sobrescrita ao ConcreteCreator.')


def veredito(status, problemas=None):
    return json.dumps(dict(veredito=status, problemas=problemas or []), ensure_ascii=False)


class DecisaoGuardiaoTest(unittest.TestCase):
    def avaliar(self, bruto):
        return v.avaliar_revisao(bruto, {'tutor': TEXTO}, PERGUNTA, BASE)

    def test_aprovacao_estrita(self):
        self.assertEqual(self.avaliar(veredito('APROVADO'))['veredito'], 'APROVADO')
        for bruto in ('VEREDITO: APROVADO', '{\"veredito\":\"REPROVADO\",\"veredito\":\"APROVADO\",\"problemas\":[]}', '{}', '[]', '{',
                      veredito('APROVADO', [erro()]),
                      '{"veredito":"APROVADO"}', veredito('ILEGIVEL')):
            with self.subTest(bruto=bruto):
                self.assertEqual(self.avaliar(bruto)['veredito'], 'INCONCLUSIVO')

    def test_erro_exige_evidencias_reais_e_autor_existente(self):
        self.assertEqual(self.avaliar(veredito('REPROVADO', [erro()]))['veredito'], 'REPROVADO')
        for campo, valor in [('trecho', 'trecho que nunca foi escrito'),
                              ('referencia', 'referência que não existe'),
                              ('autor', 'exemplificador'), ('correcao', '')]:
            problema = erro()
            problema[campo] = valor
            with self.subTest(campo=campo):
                self.assertEqual(self.avaliar(veredito('REPROVADO', [problema]))['veredito'], 'INCONCLUSIVO')
        self.assertEqual(self.avaliar(veredito('REPROVADO'))['veredito'], 'INCONCLUSIVO')

    def test_incompletude_cita_pedido_original(self):
        problema = dict(autor='tutor', tipo='incompleto', pedido='uma vantagem',
                        correcao='Explique uma vantagem do Factory Method.')
        self.assertEqual(self.avaliar(veredito('REPROVADO', [problema]))['veredito'], 'REPROVADO')
        problema['pedido'] = 'um exemplo em Python'
        self.assertEqual(self.avaliar(veredito('REPROVADO', [problema]))['veredito'], 'INCONCLUSIVO')

    def test_problemas_malformados_ou_excessivos_nao_liberam(self):
        for problemas in ([None], 'erro', [erro()] * 4):
            bruto = json.dumps(dict(veredito='REPROVADO', problemas=problemas))
            self.assertEqual(self.avaliar(bruto)['veredito'], 'INCONCLUSIVO')

    def test_cerca_json_completa_e_texto_adicional(self):
        bruto = veredito('APROVADO')
        self.assertEqual(self.avaliar('```json\n' + bruto + '\n```')['veredito'], 'APROVADO')
        self.assertEqual(self.avaliar(bruto + '\nTalvez tenha erros')['veredito'], 'INCONCLUSIVO')
