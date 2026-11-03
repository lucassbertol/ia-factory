"""Verifica a compilacao do Java retornado pelo modelo, sem executa-lo."""
import importlib
import shutil
import tempfile
from pathlib import Path
import unittest


@unittest.skipUnless(shutil.which("javac"), "Requer javac")
class JavaGeradoTest(unittest.TestCase):
    def test_java_invalido_reprova_e_preserva_codigo_e_erro_integral(self):
        modulo = importlib.import_module("validar_java_gerado")
        codigo = "public class Exemplo { String enviar(String nome) { return nome; } void testar() { enviar(); } }"
        with tempfile.TemporaryDirectory() as pasta:
            resultado = modulo.compilar_resposta("```java\n" + codigo + "\n```", Path(pasta))
            self.assertEqual(resultado["status"], "reprovado")
            self.assertEqual((Path(pasta) / "Exemplo.java").read_text(), codigo + "\n")
            self.assertTrue(resultado["compilacao"]["stderr"])

    def test_java_valido_aprova_somente_compilacao(self):
        modulo = importlib.import_module("validar_java_gerado")
        with tempfile.TemporaryDirectory() as pasta:
            resultado = modulo.compilar_resposta("```java\npublic class Exemplo {}\n```", Path(pasta))
            self.assertEqual(resultado["status"], "aprovado")
            self.assertFalse(resultado["codigo_executado"])

    def test_classe_publica_duplicada_nao_e_aprovada(self):
        modulo = importlib.import_module("validar_java_gerado")
        with tempfile.TemporaryDirectory() as pasta:
            resultado = modulo.compilar_resposta("```java\npublic class Exemplo {}\npublic class Exemplo {}\n```", Path(pasta))
            self.assertEqual(resultado["status"], "reprovado")


if __name__ == "__main__":
    unittest.main()
