#!/bin/bash

# Garante que o script rode na pasta onde ele está localizado
cd "$(dirname "$(readlink -f "$0")")"

# Mata instâncias antigas para não travar a porta 8080 nem o túnel
pkill -f "python3 app.py"
pkill -f "cloudflared"

# Instala cloudflared se não estiver disponível
if ! command -v cloudflared &>/dev/null && [ ! -f ./cloudflared ]; then
    echo "Instalando cloudflared..."
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o ./cloudflared
    chmod +x ./cloudflared
fi

CLOUDFLARED=./cloudflared
command -v cloudflared &>/dev/null && CLOUDFLARED=cloudflared

echo "============================================"
echo "      INICIANDO SERVIDOR DMC-DB             "
echo "============================================"

# 1. Inicia o servidor Python
echo "[1/2] Ligando Servidor Python..."
./venv/bin/python3 app.py > server.log 2>&1 &

sleep 15

# 2. Abre túnel gratuito (link temporário, sem domínio)
echo "[2/2] Abrindo Túnel Gratuito..."
$CLOUDFLARED tunnel --url http://localhost:8080 > tunnel.log 2>&1 &

# Aguarda o link aparecer no log
sleep 5

LINK=$(grep -o 'https://[a-zA-Z0-9.-]*\.trycloudflare\.com' tunnel.log | head -1)

clear
echo "============================================"
echo "         SISTEMA DMC ONLINE                 "
echo "============================================"
echo " Acesse: ${LINK:-'aguarde... veja tunnel.log'}"
echo "============================================"
echo " Mantenha este terminal aberto."
echo "============================================"
tail -f tunnel.log
