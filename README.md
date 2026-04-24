# 📚 Biblioteca Pessoal

Aplicação web local para catalogar e gerenciar sua coleção de livros. Desenvolvida para uso pessoal, suporta até centenas de livros com upload de capas, busca full-text, filtros, estatísticas e exportação em CSV.

---

## Funcionalidades

- **Cadastro completo** — título, autor, gênero, editora, ano, tipo, páginas, capa, nota e estado
- **Upload de capa** — suporte a JPG e PNG com preview antes de salvar
- **Busca full-text** — pesquisa simultânea em título, autor e editora usando SQLite FTS5
- **Filtros e ordenação** — por estado, tipo (físico/e-book), nota e data de cadastro
- **Páginas separadas** — visão geral, só físicos, só e-books
- **Estatísticas** — gráficos de pizza por estado de leitura, nota e tipo
- **Tema claro/escuro** — alternado pelo botão ☀/🌙 na barra superior; preferência salva automaticamente
- **Exportação CSV** — download de toda a biblioteca em `.csv` compatível com Excel
- **Sem internet necessária** — roda 100% local

---

## Telas

| Página | Descrição |
|--------|-----------|
| **Início** | Grade com os livros mais recentes, busca global e filtros |
| **Físicos** | Exibe somente livros físicos |
| **E-books** | Exibe somente e-books |
| **Estatísticas** | Cards de totais e gráficos por estado, nota e tipo |

---

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3 + Flask + Gunicorn |
| Banco de dados | SQLite 3 (com FTS5 para busca) |
| Frontend | HTML/CSS + JavaScript vanilla |
| Gráficos | Chart.js (via CDN) |
| Fonte | Gill Sans (nativa no sistema) |
| Observabilidade | OpenTelemetry (traces + métricas via OTLP HTTP) |

Sem npm, sem build step, sem banco de dados externo. Um único comando para rodar.

---

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)

---

## Instalação e uso

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/biblioteca-pessoal.git
cd biblioteca-pessoal
```

### 2. Inicie a aplicação

```bash
./start.sh
```

O script cria automaticamente o ambiente virtual, instala as dependências e abre o navegador em `http://localhost:5003`.

### Ou manualmente:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Acesse `http://localhost:5003` no navegador.

---

## Estrutura do projeto

```
biblioteca-pessoal/
├── app.py                  # Servidor Flask — todas as rotas e lógica de upload
├── database.py             # Schema do banco, tabela FTS e triggers de sincronização
├── otel_config.py          # Configuração OpenTelemetry (traces + métricas)
├── requirements.txt        # Dependências Python
├── start.sh                # Script de inicialização rápida
├── logs/                   # Logs do gunicorn (não versionados)
│
├── uploads/
│   └── covers/             # Imagens de capa enviadas pelos usuários
│
├── static/
│   ├── css/
│   │   └── style.css       # Todos os estilos (tema claro/escuro via CSS variables)
│   ├── img/
│   │   └── placeholder.svg # Capa padrão para livros sem imagem
│   └── js/
│       ├── main.js         # Tema, busca com debounce
│       ├── books.js        # Renderização dos cards e paginação
│       ├── modal.js        # Modal de adicionar/editar livro
│       └── stats.js        # Inicialização dos gráficos Chart.js
│
└── templates/
    ├── base.html           # Layout base (sidebar, topbar, modal)
    ├── home.html           # Página inicial
    ├── physical.html       # Livros físicos
    ├── ebooks.html         # E-books
    └── stats.html          # Estatísticas
```

---

## Campos do cadastro

| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| Título | Texto | Sim |
| Autor | Texto | Sim |
| Gênero | Texto | Não |
| Editora | Texto | Não |
| Ano | Número | Não |
| Tipo | Físico / E-book | Sim |
| Páginas | Número | Não |
| Capa | JPG ou PNG | Não |
| Nota | 1 a 5 estrelas | Não |
| Estado | Não lido / Lido / Abandonado / Emprestado | Sim |

---

## API

A aplicação expõe uma API REST simples para quem quiser integrar ou automatizar importações:

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/books` | Lista livros (aceita `?q=`, `?type=`, `?status=`, `?sort=`, `?limit=`, `?offset=`) |
| `POST` | `/api/books` | Cria livro (multipart/form-data) |
| `GET` | `/api/books/<id>` | Retorna um livro |
| `PUT` | `/api/books/<id>` | Atualiza livro |
| `DELETE` | `/api/books/<id>` | Remove livro e arquivo de capa |
| `GET` | `/api/stats` | Totais agrupados por estado, nota e tipo |
| `GET` | `/api/export/csv` | Download de todos os livros em CSV |

### Exemplo — cadastrar um livro via curl

```bash
curl -X POST http://localhost:5003/api/books \
  -F "title=Dom Casmurro" \
  -F "author=Machado de Assis" \
  -F "genre=Romance" \
  -F "publisher=Penguin Companhia" \
  -F "year=1899" \
  -F "type=physical" \
  -F "pages=256" \
  -F "rating=5" \
  -F "status=read"
```

### Exemplo — buscar por autor

```bash
curl "http://localhost:5003/api/books?q=machado"
```

---

## Exportação CSV

Clique em **Exportar CSV** na barra superior para baixar `biblioteca.csv` com todos os livros.

O arquivo usa separador `;` e encoding UTF-8 BOM — abre corretamente no Excel, Google Sheets e LibreOffice Calc sem configuração adicional.

Colunas exportadas: `ID`, `Título`, `Autor`, `Gênero`, `Editora`, `Ano`, `Tipo`, `Páginas`, `Nota`, `Estado`, `Cadastrado em`.

---

## Banco de dados

Os dados ficam em `library.db` (SQLite), criado automaticamente na primeira execução. Faça backup copiando esse arquivo — ele contém toda a biblioteca.

As capas ficam em `uploads/covers/`. Para backup completo, copie também essa pasta.

---

## Observabilidade

A aplicação está instrumentada com OpenTelemetry e envia **traces** e **métricas** via OTLP HTTP.

### Configuração (`otel_config.py`)

| Variável de ambiente | Padrão | Descrição |
|----------------------|--------|-----------|
| `OTEL_SERVICE_NAME` | `library-portal` | Nome do serviço no Jaeger/Prometheus |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | Endpoint do OpenTelemetry Collector |
| `OTEL_ENV` | `local` | Ambiente (`local`, `prod`, etc.) |

### Spans manuais

Além da auto-instrumentação do Flask e SQLite, há spans de negócio em:

| Span | Endpoint | Atributos |
|------|----------|-----------|
| `books.create` | `POST /api/books` | `book.type`, `book.status` |
| `books.export_csv` | `GET /api/export/csv` | — |
| `books.stats` | `GET /api/stats` | — |

### Como usar com collector no Kubernetes

```bash
# Mantenha esse terminal aberto enquanto usa a aplicação
kubectl port-forward svc/otel-collector 4318:4318 -n monitoring-lab
```

Depois navegue em `http://biblioteca.local` e procure pelo serviço **`library-portal`** no Jaeger.

Se o collector não estiver acessível, a aplicação continua funcionando normalmente — os exporters fazem retries silenciosos em background.

---

## Observações

- O banco de dados e as capas **não são versionados** no Git (listados no `.gitignore`). Faça backups manuais periodicamente.
- Em macOS, a porta 5000 é ocupada pelo AirPlay e a porta 5001 pelo Datadog Agent — por isso a aplicação roda na **porta 5003**.
- A busca usa FTS5, disponível no SQLite 3.9+ (incluso no Python 3.8+).
