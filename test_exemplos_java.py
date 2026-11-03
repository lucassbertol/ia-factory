"""Compila e executa os exemplos locais; requer um JDK (Java 8 ou superior)."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REFERENCIAS = Path(__file__).parent / "agente" / "referencias"


@unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "Requer JDK")
class ExemplosJavaTest(unittest.TestCase):
    def test_exemplos_compilam_separadamente_e_produzem_saida_esperada(self):
        for classe, esperado in [
            ("ExemploFactoryMethod", "Email para Ana\nSMS para Bia\n"),
            ("ExemploSimpleFactory", "Email simulado\nSMS simulado\n"),
        ]:
            with self.subTest(classe=classe), tempfile.TemporaryDirectory() as pasta:
                subprocess.run(["javac", "-encoding", "UTF-8", "-d", pasta,
                                str(REFERENCIAS / f"{classe}.java")], check=True, capture_output=True, timeout=30)
                resultado = subprocess.run(["java", "-cp", pasta, classe],
                                           check=True, capture_output=True, text=True, timeout=10)
                self.assertEqual(resultado.stdout, esperado)

    def test_novo_produto_por_subclasse_reutiliza_operacao_do_creator(self):
        with tempfile.TemporaryDirectory() as pasta:
            teste = Path(pasta) / "Extensao.java"
            teste.write_text('''
class NotificadorPush extends Notificador {
    @Override
    protected Notificacao criarNotificacao() {
        return destinatario -> "Push para " + destinatario;
    }
}
public class Extensao {
    public static void main(String[] args) {
        Notificador n = new NotificadorPush();
        System.out.println(n.avisar("Caio"));
    }
}
''', encoding="utf-8")
            subprocess.run(["javac", "-encoding", "UTF-8", "-d", pasta,
                            str(REFERENCIAS / "ExemploFactoryMethod.java"), str(teste)],
                           check=True, capture_output=True, timeout=30)
            resultado = subprocess.run(["java", "-cp", pasta, "Extensao"],
                                       check=True, capture_output=True, text=True, timeout=10)
            self.assertEqual(resultado.stdout, "Push para Caio\n")


if __name__ == "__main__":
    unittest.main()
