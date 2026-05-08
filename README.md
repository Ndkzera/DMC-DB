# DMC Topografia — Sistema de Gestão

Sistema web completo de gestão de arquivos, clientes, obras, agenda de campo e registros de ponto para a DMC Topografia.

---

## Requisitos

- **Python 3.11+**
- **pip**
- Dependências extras para ferramentas de processamento (opcionais):
  - `python-docx` — geração de documentos e relatórios
  - `pyproj` — Norte Magnético / conversão UTM
  - `ezdxf` — exportação de arquivos DXF

---

## Instalação (Linux — servidor)

### 1. Copiar os arquivos

```bash
scp -r ./DB\ DMC usuario@servidor:/opt/dmc
```

Ou clonar diretamente no servidor:

```bash
mkdir -p /opt/dmc && cd /opt/dmc
# copiar arquivos do projeto aqui
```

### 2. Criar o ambiente virtual

```bash
cd /opt/dmc
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
pip install python-docx pyproj ezdxf
```

### 4. Configurar variáveis de ambiente

Crie o arquivo `/opt/dmc/.env` ou exporte as variáveis antes de iniciar:

```bash
export DMC_ROOT="/mnt/backup/Arquivos"
export DMC_CONFIG="/mnt/backup/Configurações"
export DMC_TRASH="/mnt/backup/Lixeira"
export DMC_PORT=8080
export DMC_BASE_URL="http://192.168.1.100:8080"
```

| Variável       | Descrição                                              | Padrão (Linux)                                                |
|----------------|--------------------------------------------------------|---------------------------------------------------------------|
| `DMC_ROOT`     | Pasta raiz dos arquivos do servidor                    | `/media/niltonjr/Novo volume/BACKUP DMC/Arquivos`             |
| `DMC_CONFIG`   | Pasta de configurações (clientes.json, ponto.json…)    | `/media/niltonjr/Novo volume/BACKUP DMC/Arquivos de configuração` |
| `DMC_TRASH`    | Pasta de arquivos deletados (lixeira)                  | `/media/niltonjr/Novo volume/BACKUP DMC/Arquivos deletados`   |
| `DMC_PORT`     | Porta HTTP do servidor                                 | `8080`                                                        |
| `DMC_BASE_URL` | URL pública para links de compartilhamento             | Detectada automaticamente pelo IP local                       |

### 5. Testar a execução

```bash
source .venv/bin/activate
python app.py
```

Acesse: **http://IP_DO_SERVIDOR:8080**

---

## Serviço systemd (auto-inicialização)

Crie o arquivo `/etc/systemd/system/dmc.service`:

```ini
[Unit]
Description=DMC Topografia — Sistema de Gestão
After=network.target

[Service]
Type=simple
User=USUARIO
WorkingDirectory=/opt/dmc
Environment=DMC_ROOT=/mnt/backup/Arquivos
Environment=DMC_CONFIG=/mnt/backup/Configurações
Environment=DMC_TRASH=/mnt/backup/Lixeira
Environment=DMC_PORT=8080
Environment=DMC_BASE_URL=http://SEU_IP:8080
ExecStart=/opt/dmc/.venv/bin/python /opt/dmc/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dmc
sudo systemctl start dmc
sudo systemctl status dmc
```

Verificar logs em tempo real:

```bash
journalctl -u dmc -f
```

---

## Atualização do sistema

```bash
cd /opt/dmc
# copiar novos arquivos por scp ou git pull
sudo systemctl restart dmc
```

---

## Estrutura do projeto

```
app.py                      → Ponto de entrada + rotas FastAPI
config.py                   → Configuração central e variáveis de ambiente
requirements.txt            → Dependências Python

services/
  auth.py                   → Autenticação e controle de sessão
  acesso.py                 → Permissões por perfil de usuário
  files.py                  → Operações de arquivo (listar, deletar, validar)
  clientes.py               → CRUD de clientes (JSON)
  obras.py                  → CRUD de obras
  agenda.py                 → Integração com Google Agenda
  ponto.py                  → Registros de campo (checkin/checkout)
  tecnicos.py               → Cadastro de técnicos
  documentos.py             → Geração de documentos .docx a partir de modelos
  relatorio_campo.py        → Geração de relatórios de campo (.docx)

ui/
  styles.py                 → CSS global, componentes e JavaScript utilitário
  sidebar.py                → Sidebar com menu, filtros e links rápidos
  main_view.py              → Explorador de arquivos (grade/lista/busca)
  dialogs.py                → Cadastro e edição de clientes
  agenda_dialogs.py         → Agenda, eventos e equipe de campo
  campo_dialogs.py          → Checkin/checkout e histórico de campo
  obras_dialogs.py          → Cadastro e gestão de obras
  tecnicos_dialogs.py       → Cadastro de técnicos
  documentos_dialogs.py     → Geração de documentos por cliente
  processamento_dialogs.py  → Norte Magnético, Processamento de Campo, Relatório de Campo

pages/
  main.py                   → Página principal (/)
  login.py                  → Autenticação (/login)
  campo.py                  → Registro de campo — mobile (/campo)
  mobile.py                 → Interface mobile (/mobile)
  cadastro.py               → Cadastro de cliente (/cliente/cadastrar)
  contas.py                 → Gestão de contas (/contas)
  acesso.py                 → Configuração de acesso (/acesso)

modelos/                    → Modelos .docx para geração de documentos
```

---

## Funcionalidades

### Arquivos
- Explorador com visualização em grade ou lista
- Upload por drag-and-drop com barra de progresso
- Filtro por tipo (CAD, PDF, Office, Imagens, GIS, ZIP)
- Busca recursiva por nome
- Compartilhamento via link direto (WhatsApp)
- Lixeira — arquivos deletados são movidos, não excluídos

### Clientes
- Cadastro completo PF e PJ
- Busca automática de endereço por CEP (ViaCEP)
- Consulta automática de dados por CNPJ
- Endereço de obra separado do endereço do cliente
- Geração de documentos `.docx` a partir de modelos com campos destacados

### Obras
- Cadastro e gestão de obras vinculadas a clientes
- Status: Em andamento / Concluída / Suspensa

### Agenda de Campo
- Integração com Google Agenda (OAuth2)
- Criação de eventos com equipe, modificadores (Diária / Meia Diária) e vinculação de obras
- Visualização dos eventos do dia na página de campo

### Registro de Campo
- Checkin e checkout com foto, nome da obra e localização
- Fotos servidas via `/fotos_ponto/` (HTTP estático)
- Histórico por funcionário com filtro por tipo e período
- Relatório de campo em `.docx` por obra ou funcionário, com todos os dias do período

### Processamento
- **Norte Magnético** — conversão UTM → Geográfico, Convergência Meridiana, Fator de Escala, exportação DXF
- **Processamento de Campo** — importação de pontos (TSV/CSV), exportação DXF com símbolos configuráveis
- **Relatório de Campo** — `.docx` mensal com checkin/checkout por obra ou funcionário

### Links Rápidos (sidebar)
- CFT-BR, SIG-RI, Certidão de Confrontantes, Assinatura Gov, ProGrid / IBGE

### Administrativo
- Gestão de contas de usuário com perfis (Desenvolvedor, Administrador, Técnico, Funcionário Campo)
- Configuração de permissões de acesso por módulo
- Cadastro de técnicos responsáveis

---

## Rotas HTTP

| Método | Rota                  | Descrição                                  |
|--------|-----------------------|--------------------------------------------|
| GET    | `/`                   | Página principal                           |
| GET    | `/login`              | Autenticação                               |
| GET    | `/campo`              | Registro de campo (mobile)                 |
| GET    | `/mobile`             | Interface mobile                           |
| GET    | `/contas`             | Gestão de contas                           |
| GET    | `/acesso`             | Configuração de acesso                     |
| GET    | `/files/{path}`       | Arquivos estáticos do servidor             |
| GET    | `/fotos_ponto/{file}` | Fotos de checkin/checkout                  |
| GET    | `/info`               | JSON com base_url e root_dir               |
| POST   | `/upload`             | Upload de arquivo via XHR                  |
| GET    | `/api/cep/{cep}`      | Consulta de endereço por CEP (ViaCEP)      |
| GET    | `/api/cnpj/{cnpj}`    | Consulta de dados por CNPJ (ReceitaWS)     |
