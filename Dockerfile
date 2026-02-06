# Use uma imagem leve do Python
FROM python:3.10-slim

# Evita arquivos .pyc e buffer de output (logs aparecem na hora)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho no container
WORKDIR /app

# Instalar dependências do sistema necessárias
# git e curl são úteis para ferramentas que a Aurora possa usar
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas o requirements primeiro para cachear a instalação
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
# NOTA: Com docker-compose e volumes, isso é sobrescrito pelo volume local,
# mas é bom ter para builds de produção sem volume.
COPY . .

# Comando padrão: Inicia o Bot do Telegram
CMD ["python", "scripts/telegram_bot.py"]
