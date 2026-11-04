// Exemplo didatico autoral (variacao). Nao grava arquivos reais.
// Mostra que o Creator NAO precisa ser abstrato: ele pode ter uma
// implementacao padrao do factory method, sobrescrita por subclasses.
public class ExemploFactoryMethodPadrao {

    // Product
    interface Exportador {
        String exportar(String conteudo);
    }

    // ConcreteProducts
    static class ExportadorTexto implements Exportador {
        @Override
        public String exportar(String conteudo) {
            return "[TXT] " + conteudo;
        }
    }

    static class ExportadorCsv implements Exportador {
        @Override
        public String exportar(String conteudo) {
            return "[CSV] " + conteudo.replace(" ", ";");
        }
    }

    // Creator concreto: tem uma implementacao padrao do factory method.
    static class Relatorio {
        protected Exportador criarExportador() { // Factory Method (padrao: texto)
            return new ExportadorTexto();
        }

        // Operacao de negocio: depende so do contrato Exportador.
        public String gerar(String dados) {
            Exportador exportador = criarExportador();
            return exportador.exportar("Relatorio de " + dados);
        }
    }

    // ConcreteCreator: muda apenas a criacao, reaproveitando gerar().
    static class RelatorioCsv extends Relatorio {
        @Override
        protected Exportador criarExportador() {
            return new ExportadorCsv();
        }
    }

    public static void main(String[] args) {
        // Configuracao: aqui ainda escolhemos o criador concreto.
        Relatorio padrao = new Relatorio();
        Relatorio csv = new RelatorioCsv();
        System.out.println(padrao.gerar("vendas"));
        System.out.println(csv.gerar("vendas"));
    }
}
