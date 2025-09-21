# FeedScraper LangChain

# FeedScraper LangChain

Projeto Django com integração LangChain para processamento de texto e agendamento de jobs, desenvolvido com base no template PRP (Product Requirement Prompt).

## 🚀 Características

- **Django 5.2+** com arquitetura limpa
- **LangChain** para processamento de texto e IA
- **APScheduler** para agendamento de jobs
- **PostgreSQL/SQLite** suporte para bancos de dados
- **Padrão Repository** para acesso a dados
- **Arquitetura em camadas** (Service Layer)
- **Logging estruturado**
- **Configurações por ambiente**

## 📁 Estrutura do Projeto

```
feedscraper_langchain/
├── config/                     # Configurações Django
│   ├── settings/               # Settings por ambiente
│   │   ├── base.py            # Configurações base
│   │   ├── development.py     # Configurações de desenvolvimento
│   │   └── production.py      # Configurações de produção
│   ├── urls.py                # URLs principais
│   └── wsgi.py                # WSGI config
├── core/                      # Módulos centrais
│   ├── models/                # Modelos base
│   │   └── base.py           # BaseModel e BaseRepository
│   ├── middleware/            # Middlewares customizados
│   └── utils/                 # Utilitários
├── apps/                      # Aplicações Django
│   ├── jobs/                  # Sistema de jobs
│   │   ├── models.py         # Modelos de job
│   │   ├── schedulers.py     # Scheduler service
│   │   └── tasks.py          # Definições de tasks
│   └── langchain_integration/ # Integração LangChain
│       ├── models.py         # Modelos LangChain
│       └── services/         # Services LangChain
├── requirements/              # Dependências
│   ├── base.txt              # Dependências base
│   ├── development.txt       # Dependências dev
│   └── production.txt        # Dependências prod
├── static/                    # Arquivos estáticos
├── logs/                      # Logs da aplicação
├── .env.example              # Exemplo de variáveis
├── manage.py                 # Django management
├── exemplo_uso.py            # Exemplos de uso
└── README.md                 # Este arquivo
```

## 🛠️ Configuração do Ambiente

### 1. Pré-requisitos

- Python 3.12+
- pip (gerenciador de pacotes Python)
- Git

### 2. Clonagem e Setup Inicial

```bash
# Navegar para o diretório do projeto
cd feedscraper_langchain

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Instalar dependências
pip install -r requirements/development.txt
```

### 3. Configuração de Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar o arquivo .env com suas configurações
nano .env
```

Exemplo de `.env`:

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite para desenvolvimento)
DATABASE_URL=sqlite:///db.sqlite3

# LangChain / OpenAI
OPENAI_API_KEY=sua-api-key-openai
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=sua-api-key-langchain
LANGCHAIN_PROJECT=feedscraper

# APScheduler
SCHEDULER_JOBSTORE_URL=sqlite:///scheduler.sqlite3
SCHEDULER_EXECUTORS_DEFAULT_MAX_WORKERS=10

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

### 4. Executar Migrações

```bash
# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate
```

### 5. Criar Superusuário (Opcional)

```bash
python manage.py createsuperuser
```

## 🚀 Executando o Projeto

### Servidor de Desenvolvimento

```bash
python manage.py runserver
```

### Exemplos de Uso

```bash
# Executar exemplos
python exemplo_uso.py
```

## 🔧 Uso dos Services

### 1. Processamento de Texto com LangChain

```python
from apps.langchain_integration.services.text_processor import TextProcessorService

# Inicializar service
service = TextProcessorService(
    template="Analise o seguinte texto: {text}"
)

# Processar texto
resultado = service.process({
    'text': 'Seu texto aqui...'
})

if resultado['success']:
    print(f"Resultado: {resultado['result']}")
else:
    print(f"Erro: {resultado['error']}")
```

### 2. Sumarização de Texto

```python
from apps.langchain_integration.services.text_processor import TextSummarizerService

# Inicializar service
service = TextSummarizerService(max_length=100)

# Sumarizar texto
resultado = service.process({
    'text': 'Texto longo para sumarizar...'
})
```

### 3. Agendamento de Jobs

```python
from apps.jobs.schedulers import JobSchedulerService
from apps.jobs.tasks import process_text_job

# Iniciar scheduler
JobSchedulerService.start()

# Agendar job
JobSchedulerService.add_job(
    func=lambda: process_text_job("texto", "template"),
    trigger='interval',
    job_id='meu_job',
    minutes=5
)

# Listar jobs
jobs = JobSchedulerService.list_jobs()
```

## 🧪 Testes

```bash
# Executar testes
python manage.py test

# Executar testes com coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Modelos de Dados

### Core Models

- **BaseModel**: Modelo abstrato com UUID, timestamps e soft delete
- **BaseRepository**: Padrão repository para operações CRUD

### Jobs Models

- **JobExecutionLog**: Log de execuções de jobs
- **ScheduledJob**: Configuração de jobs agendados

## 🔍 Logs e Monitoramento

Os logs são salvos em `logs/` e incluem:

- `django.log`: Logs gerais do Django
- `jobs.log`: Logs específicos de jobs
- `langchain.log`: Logs de operações LangChain

## 🛡️ Segurança

- Variáveis de ambiente para dados sensíveis
- Validação de entrada nos services
- Logging de operações sensíveis
- Tratamento de exceções

## 📚 Documentação Adicional

### Services LangChain

- `BaseLangChainService`: Classe base para services LangChain
- `TextProcessorService`: Processamento genérico de texto
- `TextSummarizerService`: Sumarização especializada

### Sistema de Jobs

- `JobSchedulerService`: Gerenciamento de scheduler
- Tasks predefinidas para processamento e sumarização

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🆘 Suporte

Se você encontrar problemas ou tiver dúvidas:

1. Verifique os logs em `logs/`
2. Confirme as configurações no `.env`
3. Execute `python manage.py check` para verificar problemas
4. Consulte a documentação do Django e LangChain

## 🔄 Changelog

### v1.0.0 (Atual)
- Projeto inicial baseado no template PRP
- Integração Django + LangChain
- Sistema de jobs com APScheduler
- Arquitetura limpa com padrão Repository
- Configurações por ambiente
- Logging estruturado

## 🚀 Tecnologias

- **Django 5.2+** - Framework web Python
- **LangChain** - Framework para aplicações de IA
- **django-apscheduler** - Sistema de jobs agendados
- **PostgreSQL** - Banco de dados (produção)
- **Redis** - Cache e job store (produção)

## 📁 Estrutura do Projeto

```
feedscraper_langchain/
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/
│   ├── models/base.py
│   ├── exceptions/
│   ├── utils/
│   └── middleware/
├── apps/
│   ├── jobs/
│   └── langchain_integration/
├── infrastructure/
├── tests/
└── logs/
```

## 🛠️ Configuração do Ambiente

### 1. Clone o repositório
```bash
git clone <repository-url>
cd feedscraper_langchain
```

### 2. Crie e ative o ambiente virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements/development.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 5. Execute as migrações
```bash
python manage.py migrate
```

### 6. Crie um superusuário
```bash
python manage.py createsuperuser
```

### 7. Execute o servidor
```bash
python manage.py runserver
```

## 📝 Variáveis de Ambiente

Configure as seguintes variáveis no arquivo `.env`:

- `SECRET_KEY`: Chave secreta do Django
- `DATABASE_*`: Configurações do banco de dados
- `OPENAI_API_KEY`: Chave da API do OpenAI
- `LANGCHAIN_*`: Configurações do LangChain

## 🏗️ Arquitetura

### Core
- **BaseModel**: Modelo base com campos comuns (UUID, timestamps, soft delete)
- **BaseRepository**: Padrão repository para operações de banco
- **Exceptions**: Exceções personalizadas
- **Middleware**: Middleware de segurança e logging

### Apps

#### Jobs
- **JobSchedulerService**: Gerencia jobs agendados
- **Tasks**: Definições de tarefas
- **Models**: Logs de execução e configurações

#### LangChain Integration
- **BaseLangChainService**: Service base para operações LangChain
- **TextProcessorService**: Processamento de texto
- **TextSummarizerService**: Sumarização de texto

## 🔧 Uso

### Processamento de Texto
```python
from apps.langchain_integration.services.text_processor import TextProcessorService

service = TextProcessorService()
result = service.process({'text': 'Seu texto aqui'})
```

### Agendamento de Jobs
```python
from apps.jobs.schedulers import JobSchedulerService
from apps.jobs.tasks import process_text_job

# Adicionar job
JobSchedulerService.add_job(
    func=process_text_job,
    trigger='interval',
    job_id='text_processor',
    minutes=30
)
```

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Executar testes com coverage
pytest --cov=apps --cov=core
```

## 📊 Monitoramento

- **Health Check**: `/health/`
- **Admin**: `/admin/`
- **Logs**: Arquivos em `logs/` e banco de dados

## 🚀 Deploy

### Docker
```bash
docker build -t feedscraper-langchain .
docker run -p 8000:8000 feedscraper-langchain
```

### Produção
1. Configure as variáveis de ambiente de produção
2. Execute `python manage.py collectstatic`
3. Configure PostgreSQL e Redis
4. Use Gunicorn como servidor WSGI

## 📚 Documentação

- [Django Documentation](https://docs.djangoproject.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.
