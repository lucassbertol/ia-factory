// Exemplo didatico de USO INCORRETO do Factory Method (compila, mas tem um defeito de projeto).
// Erro: o Creator declara o factory method, mas a operacao de negocio o ignora
// e instancia um produto concreto com new. A subclasse sobrescreve sem efeito.
public class ExemploUsoIncorreto {

    interface Notificacao {
        String enviar(String destinatario);
    }

    static class Email implements Notificacao {
        @Override
        public String enviar(String destinatario) {
            return "Email para " + destinatario;
        }
    }

    static class Sms implements Notificacao {
        @Override
        public String enviar(String destinatario) {
            return "SMS para " + destinatario;
        }
    }

    abstract static class Notificador {
        protected abstract Notificacao criarNotificacao(); // Factory Method declarado...

        public String avisar(String destinatario) {
            Notificacao notificacao = new Email(); // ERRO: ...mas nao usado aqui
            return notificacao.enviar(destinatario);
        }
    }

    static class NotificadorSms extends Notificador {
        @Override
        protected Notificacao criarNotificacao() {
            return new Sms(); // sobrescrita que nunca e chamada
        }
    }

    public static void main(String[] args) {
        Notificador sms = new NotificadorSms();
        // Esperado: "SMS para Bia". Obtido: "Email para Bia".
        System.out.println(sms.avisar("Bia"));
    }
}
