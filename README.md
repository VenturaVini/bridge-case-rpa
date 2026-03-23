# Bridge Case RPA

Case tecnico de RPA pra Bridge Consulting — automatiza um fluxo completo de processamento de informacoes: coleta de noticias na web, distribuicao por email, ingestao de PDFs, extracao de dados e consumo de API publica.

O projeto ta dividido em 5 modulos. Quatro rodam em Python e um em UiPath. A comunicacao entre eles e feita pelas queues do UiPath Orchestrator.

## Tecnologias

- **Python 3.14** — modulos A, C, D e E
- **UiPath Studio** — modulo B (newsletter)
- **uv** — gerenciador de dependencias Python
- **Selenium** — scraping do Yahoo News
- **UiPath Orchestrator** — queues e assets
- **Gmail IMAP/SMTP** — leitura e envio de emails
- **CoinGecko API** — dados de criptomoedas (modulo E)

## Estrutura do Projeto

```
bridge-case-rpa/
├── main_root.py                  # orquestrador dos modulos Python
├── .env.example                  # template das variaveis de ambiente
├── pyproject.toml                # dependencias
│
├── modulo_a/main.py              # roda o modulo A
├── modulo_b/                     # projeto UiPath (modulo B)
│   ├── Main.xaml
│   └── utils/
│       ├── EnviarEmailGeral.xaml
│       ├── EnviarEmailTech.xaml
│       └── LogJSON.xaml
├── modulo_c/main.py              # roda o modulo C
├── modulo_d/main.py              # roda o modulo D
│
├── system/
│   ├── core/
│   │   ├── config/               # config.py e logger.py
│   │   ├── services/             # yahoo, gmail, pdf, orchestrator, webdriver
│   │   └── utils/                # csv, normalizacao, validacao cpf/cep, pdf
│   └── data/                     # dados gerados (CSV, XLSX, logs, PDFs)
│
└── bridge-case-rpa-CoinGecko/    # modulo E (repo separado)
```

## Pre-requisitos

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- UiPath Studio (pro modulo B)
- Google Chrome (pro Selenium)
- Conta Gmail com senha de app

## Setup

### 1. Clonar e instalar

```bash
git clone https://github.com/VenturaVini/bridge-case-rpa.git
cd bridge-case-rpa
uv sync
```

### 2. Configurar o .env

```bash
cp .env.example .env
```

Preencha com suas credenciais. As variaveis principais:

| Variavel | Descricao |
|----------|-----------|
| `GMAIL_USUARIO` | email do Gmail (modulo C) |
| `GMAIL_SENHA_APP` | senha de app do Gmail |
| `GMAIL_SERVIDOR` | `imap.gmail.com` |
| `GMAIL_PORTA` | `993` |
| `FILTRO_ASSUNTO` | assunto pra filtrar (ex: `Relatório Diário`) |
| `YAHOO_URL` | URL do Yahoo News |
| `YAHOO_TIMEOUT` | timeout do Selenium em segundos |
| `ORCHESTRATOR_URL` | URL do UiPath Cloud |
| `ORCHESTRATOR_CLIENT_ID` | client ID do app externo |
| `ORCHESTRATOR_CLIENT_SECRET` | secret do app externo |
| `ORCHESTRATOR_FOLDER_ID` | ID da pasta no Orchestrator |

### 3. Configurar UiPath (modulo B)

Abra o `modulo_b/` no UiPath Studio e configure os **Assets** no Orchestrator:

| Asset | Tipo | O que guarda |
|-------|------|-------------|
| `gmail_conta_envio_email` | Credential | usuario/senha do Gmail |
| `lista_email_geral` | Text | emails do grupo geral |
| `lista_email_grupo_tech` | Text | emails do grupo tech |
| `tema_email_tech` | Text | temas que direcionam pro grupo tech |

As **Queues** (`Bridge_Modulo_A`, `B`, `C`, `D`) ja devem existir no Orchestrator.

## Como Rodar

### Modulo A — Coleta do Yahoo News

```bash
uv run python modulo_a/main.py
```

Abre o Chrome, extrai 5 noticias do Yahoo News, normaliza e publica na fila do Orchestrator. Salva CSV em `system/data/`.

### Modulo B — Newsletter (UiPath)

Abre o `modulo_b/Main.xaml` no UiPath Studio e executa. Consome da fila, filtra por tema e envia emails pros grupos.

### Modulo C — Ingestao de Emails

```bash
uv run python modulo_c/main.py
```

Conecta no Gmail via IMAP, busca emails com assunto "Relatório Diário", valida PDFs e salva em `system/data/inbox/valid/YYYY-MM-DD/`.

### Modulo D — Extracao de PDF

```bash
uv run python modulo_d/main.py
```

Le os PDFs do modulo C, extrai CPF e CEP via regex e salva em `system/data/dados_extraidos_DATA.xlsx`.

### Modulo E — CoinGecko (repo separado)

```bash
cd bridge-case-rpa-CoinGecko
uv sync
uv run python system/jobs/CoinGecko/main.py
```

Consome a API do CoinGecko e salva dados das top criptomoedas em CSV e JSON.

## Contas de Email

| Email | Funcao |
|-------|--------|
| `rpageralvini@gmail.com` | Grupo Geral — recebe newsletters gerais (modulo B) |
| `rpatechvini@gmail.com` | Grupo Tech — recebe newsletters de tecnologia (modulo B) |
| `rpa.case.vinicius01@gmail.com` | Conta principal — modulo C le emails dessa conta |

## Logs

Todos os modulos geram logs JSON estruturados em `system/data/logs/app.log`:

```json
{
  "timestamp": "2026-03-22T12:00:00",
  "nivel": "INFO",
  "modulo": "modulo_a",
  "mensagem": "extraiu e publicou 5 noticias"
}
```
