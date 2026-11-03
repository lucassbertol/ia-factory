// Exemplo didatico autoral. Nao envia mensagens reais.
// Salve como ExemploFactoryMethod.java; as demais classes nao sao publicas.

// Product
interface Notificacao {
    String enviar(String destinatario);
}

// ConcreteProducts
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

// Creator: a operacao de negocio depende do contrato Product.
abstract class Notificador {
    protected abstract Notificacao criarNotificacao(); // Factory Method

    public String avisar(String destinatario) {
        Notificacao notificacao = criarNotificacao();
        return notificacao.enviar(destinatario);
    }
}

// ConcreteCreators: especializam a criacao por sobrescrita.
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

public class ExemploFactoryMethod {
    public static void main(String[] args) {
        // Configuracao: aqui ainda conhecemos os criadores concretos.
        Notificador email = new NotificadorEmail();
        Notificador sms = new NotificadorSms();
        System.out.println(email.avisar("Ana"));
        System.out.println(sms.avisar("Bia"));
    }
}
