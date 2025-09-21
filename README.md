# FeedScraper LangChain

Sistema Django para coleta e processamento automático de notas técnicas NFE usando LangChain e IA.

## 🎯 O que faz

- **Coleta automática** de notas técnicas do site da Receita Federal
- **Processamento inteligente** com LangChain e GPT-4
- **Sumarização automática** de documentos técnicos
- **Agendamento de jobs** para execução em background
- **Interface administrativa** Django para gerenciamento

## 🚀 Como executar

### Setup rápido

```bash
# Clonar e navegar para o projeto
git clone <repository-url>
cd feedscraper_langchain

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements/development.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com sua API key do OpenAI

# Inicializar projeto (migrações + superusuário)
python scripts/init_project.py

# Forçar recriação de superusuário
python scripts/init_project.py --force-superuser

# Executar servidor
python manage.py runserver
```

### Acessar o sistema

- **Admin**: http://127.0.0.1:8000/admin/
- **Login**: admin / admin123 (altere em produção)

## 📝 Configuração mínima

Edite o arquivo `.env`:

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
OPENAI_API_KEY=sua-api-key-openai
DATABASE_URL=sqlite:///db.sqlite3
```

## 📄 Licença

MIT License - veja o arquivo LICENSE para detalhes.