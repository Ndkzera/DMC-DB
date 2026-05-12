#!/bin/bash

DIRETORIO="/media/niltonjr/Novo volume/BACKUP DMC"

cd "$DIRETORIO"

source "$DIRETORIO/venv/bin/activate"

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
