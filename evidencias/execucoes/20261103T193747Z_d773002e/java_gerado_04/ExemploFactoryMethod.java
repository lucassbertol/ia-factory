// Exemplo para avaliar: ExemploFactoryMethod.java

public class ExemploFactoryMethod {
    public static void main(String[] args) {
        Notificador email = new NotificadorEmail();
        Notificador sms = new NotificadorSms();

        System.out.println(email.avisar("Ana"));
        System.out.println(sms.avisar("Bia"));
    }

    // Interface Notificacao
    interface Notificacao {
        String enviar(String destinatario);
    }

    // Superclasses do Factory Method
    abstract class Notificador {
        protected abstract Notificacao criarNotificacao(); // Factory Method

        public String avisar(String destinatario) {
            Notificacao notificacao = criarNotificacao();
            return notificacao.enviar(destinatario);
        }
    }

    // Concrete Classes
    class NotificadorEmail extends Notificador {
        @Override
        protected Notificacao criarNotificacao() {
            return new Email();
        }
    }

    class NotificadorSms extends Notificador {
        @Override
        protected Notificacao criarNotificacao() {
            return new Sms();
        }
    }

    // Concrete Implementations
    class Email implements Notificacao {
        @Override
        public String enviar(String destinatario) {
            return "Email para " + destinatario;
        }
    }

    class Sms implements Notificacao {
        @Override
        public String enviar(String destinatario) {
            return "SMS para " + destinatario;
        }
    }
}

// Exemplo de utilização correta
public class ExemploFactoryMethod {
    public static void main(String[] args) {
        Notificador email = new NotificadorEmail();
        Notificador sms = new NotificadorSms();

        System.out.println(email.avisar("Ana"));
        System.out.println(sms.avisar("Bia"));
    }
}
