#!/bin/bash

DIRETORIO="/media/niltonjr/Novo volume/BACKUP DMC"

cd "$DIRETORIO"

source "$DIRETORIO/venv/bin/activate"

# Instala cloudflared se não estiver disponível
if ! command -v cloudflared &>/dev/null; then
    echo "cloudflared não encontrado. Instalando..."
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
    chmod +x /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    echo "cloudflared instalado."
fi

# Inicia o servidor em background
python3 app.py &
APP_PID=$!

# Aguarda a app subir antes de abrir o túnel
sleep 3

# Abre o túnel Cloudflare (link gratuito, sem cadastro)
cloudflared tunnel --url http://localhost:8080

# Quando o túnel fechar, encerra o servidor
kill $APP_PID 2>/dev/null

read -p "Pressione Enter para fechar..."
