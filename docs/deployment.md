# Guia de Deploy e Uso (VPS)

A Aurora foi projetada para rodar silenciosamente em servidor (VPS) usando Docker e permitir interação via **Telegram**.

## 1. Acesso e Interação
Quando você roda a aplicação na VPS via Docker, ela **não** fica com um terminal aberto para você digitar. Ela roda em "background".

**Como conversar com ela então?**
A configuração padrão do Docker (`Dockerfile`) está pronta para rodar o **Bot do Telegram** (`scripts/telegram_bot.py`).
Isso significa que sua interface será o seu aplicativo do Telegram no celular ou computador.

## 2. Configurando o Telegram

### Passo 1: Criar o Bot
1. Abra o Telegram e procure por `@BotFather`.
2. Envie `/newbot`.
3. Escolha um nome e um username para o bot.
4. Ele vai te dar um **TOKEN** (ex: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`).
5. Copie esse token.

### Passo 2: Descobrir seu ID
Para que só **você** possa falar com o bot (segurança), descubra seu Chat ID:
1. Mande uma mensagem para `@userinfobot`.
2. Copie o número "Id" (ex: `123456789`).

### Passo 3: Configurar na VPS
No arquivo `.env` da sua VPS, certifique-se de ter:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui_sem_aspas
TELEGRAM_DEFAULT_CHAT_ID=seu_id_aqui
```

## 3. Subindo na VPS

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/ZarabaDev/aurora-agent.git
   cd aurora-agent
   ```
2. **Crie o .env:**
   ```bash
   cp .env.example .env
   nano .env  # Cole suas chaves API e do Telegram
   ```
3. **Suba com Docker:**
   ```bash
   docker-compose up --build -d
   ```

A partir de agora, o bot deve te mandar uma mensagem no Telegram (se configurado) ou responder quando você mandar "Oi".

## 4. Manutenção

*   **Ver logs** (para ver o que ela está pensando ou erros):
    ```bash
    docker-compose logs -f aurora
    ```
*   **Reiniciar**:
    ```bash
    docker-compose restart
    ```
*   **Parar**:
    ```bash
    docker-compose down
    ```
