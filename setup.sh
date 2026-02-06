#!/bin/bash

# Cores
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Aurora Docker Manager${NC}"
echo "---------------------"

if [ "$1" == "start" ]; then
    echo "Iniciando Aurora (Background)..."
    docker compose up -d --build
    echo -e "${GREEN}Aurora está online!${NC}"
    echo "Use './setup.sh logs' para ver o terminal."

elif [ "$1" == "stop" ]; then
    echo "Parando Aurora..."
    docker compose down

elif [ "$1" == "restart" ]; then
    echo "Reiniciando..."
    docker compose restart

elif [ "$1" == "logs" ]; then
    docker compose logs -f

elif [ "$1" == "shell" ]; then
    docker compose exec aurora bash

else
    echo "Comandos disponíveis:"
    echo "  ./setup.sh start   - Sobe o container (build force)"
    echo "  ./setup.sh stop    - Para o container"
    echo "  ./setup.sh restart - Reinicia o container"
    echo "  ./setup.sh logs    - Vê logs em tempo real"
    echo "  ./setup.sh shell   - Entra no terminal do container"
fi
