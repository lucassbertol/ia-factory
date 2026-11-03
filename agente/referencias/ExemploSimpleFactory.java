// Contraste didatico: codigo valido, mas nao demonstra Factory Method GoF.
// Pode ser compilado isoladamente; nao depende do outro exemplo.
public class ExemploSimpleFactory {
    interface Mensagem {
        String enviar();
    }

    static class Email implements Mensagem {
        @Override
        public String enviar() { return "Email simulado"; }
    }

    static class Sms implements Mensagem {
        @Override
        public String enviar() { return "SMS simulado"; }
    }

    // Simple Factory: escolha centralizada, sem Creator sobrescrito.
    static Mensagem criar(String tipo) {
        if ("email".equals(tipo)) { return new Email(); }
        if ("sms".equals(tipo)) { return new Sms(); }
        throw new IllegalArgumentException("Tipo desconhecido: " + tipo);
    }

    public static void main(String[] args) {
        System.out.println(criar("email").enviar());
        System.out.println(criar("sms").enviar());
    }
}
