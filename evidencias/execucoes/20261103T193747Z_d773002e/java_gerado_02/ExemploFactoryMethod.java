// ExemploFactoryMethod.java

// Product: O cliente (Consumer) não sabe e nem deve saber qual concreto usa. A responsabilidade de escolha está no criação.
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

class CallToAction implements Notificacao {
    @Override
    public String enviar(String destinatario) {
        return "CallToAction para " + destinatario;
    }
}

// Creator: A operação do negócio depende do contrato do "Produto". O criador pode usar os objetos do produto em sua operação de negócios.
abstract class Notificador {
    // The factory method, where the creating object will be returned.
    protected abstract Notificacao criarNotificacao();

    public String avisar(String destinatario) {
        Notificacao notificacao = criarNotificacao();
        return notificacao.enviar(); // O cliente do Criador ainda não conhece o tipo concreto, apenas o contrato de notificar.
    }
}

// ConcreteCreators: Especializam a criação por sobrescritas.
class NotificadorEmail extends Notificador {
    @Override
    protected Notificacao criarNotificacao() {
        return new Email();
    }
    
    public String enviarNotificacao(CallToAction notificacao) {
        return notificacao.enviar();
    }
}

class NotificadorSms extends Notificador {
    @Override
    protected Notificacao criarNotificacao() {
        return new Sms();
    }
    
    public String enviarNotificacao(CallToAction notificacao) {
        return notificacao.enviar();
    }
}

public class ExemploFactoryMethod {
    public static void main(String[] args) {
        // Configuração: Configuração dos criadores de acordo com a situação da aplicação.
        Notificador email = new NotificadorEmail();
        Notificador sms = new NotificadorSms();

        System.out.println(email.avisar("Ana")); // Exibirá algo como "Email para Ana"
        System.out.println(sms.avisar("Bia")); // Exibirá algo como "SMS para Bia"
        
        // Novo tipo de notificação: CallToAction
        CallToAction callToAction = new CallToAction();
        System.out.println(email.enviarNotificacao(callToAction)); // Exibirá algo como "CallToAction para Ana"
        System.out.println(sms.enviarNotificacao(callToAction)); // Exibirá algo como "CallToAction para Bia"
    }
}
