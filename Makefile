# Makefile para Projeto NFE Fazenda Scraper
# Comandos para gerenciamento de jobs e monitoramento

.PHONY: help setup-jobs setup-jobs-only setup-jobs-daemon status-jobs stop-jobs run-scraping run-processing monitor-logs clean

# Configuração do ambiente Python
PYTHON := python
VENV_PATH := .venv
MANAGE := $(PYTHON) manage.py

# Cores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
BOLD := \033[1m
NC := \033[0m # No Color

help: ## Mostrar este menu de ajuda
	@echo "$(BOLD)📋 Comandos disponíveis para NFE Fazenda Scraper:$(NC)\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo "\n$(YELLOW)💡 Exemplos de uso:$(NC)"
	@echo "  make setup-jobs     # Configurar e manter jobs rodando"
	@echo "  make monitor-logs   # Monitorar logs em tempo real"
	@echo "  make status-jobs    # Verificar status dos jobs"
	@echo "  make stop-jobs      # Parar todos os jobs"

setup-jobs: ## Configurar e iniciar jobs NFE (modo interativo)
	@echo "$(BLUE)🚀 Configurando jobs NFE Fazenda...$(NC)"
	$(MANAGE) start_jobs

setup-jobs-only: ## Apenas configurar jobs sem mantê-los rodando
	@echo "$(BLUE)⚙️  Configurando jobs NFE (setup only)...$(NC)"
	$(MANAGE) start_jobs --setup-only

setup-jobs-daemon: ## Configurar jobs em modo daemon (background)
	@echo "$(BLUE)🔄 Iniciando jobs NFE em modo daemon...$(NC)"
	$(MANAGE) start_jobs --daemon &
	@echo "$(GREEN)✅ Jobs iniciados em background$(NC)"

status-jobs: ## Verificar status atual dos jobs
	@echo "$(BLUE)📊 Verificando status dos jobs...$(NC)"
	$(MANAGE) start_jobs --status

stop-jobs: ## Parar todos os jobs NFE
	@echo "$(RED)🛑 Parando jobs NFE...$(NC)"
	$(MANAGE) start_jobs --stop
	@echo "$(GREEN)✅ Jobs parados$(NC)"

run-scraping: ## Executar job de scraping manualmente
	@echo "$(YELLOW)🕷️  Executando scraping manual...$(NC)"
	$(MANAGE) start_jobs --run scraping

run-processing: ## Executar job de processamento IA manualmente
	@echo "$(YELLOW)🧠 Executando processamento IA manual...$(NC)"
	$(MANAGE) start_jobs --run processing

monitor-logs: ## Monitorar logs NFE em tempo real
	@echo "$(BLUE)👀 Iniciando monitor de logs...$(NC)"
	@echo "$(YELLOW)💡 Para parar: Ctrl+C$(NC)"
	@chmod +x logs/monitor_logs.sh
	@./logs/monitor_logs.sh

monitor-logs-errors: ## Monitorar apenas erros nos logs
	@echo "$(RED)🚨 Monitorando apenas ERROS...$(NC)"
	@tail -f logs/app.log | grep --color=always -E "(ERROR|CRITICAL)"

monitor-logs-jobs: ## Monitorar apenas logs relacionados a jobs
	@echo "$(GREEN)👷 Monitorando logs de JOBS...$(NC)"
	@tail -f logs/app.log | grep --color=always -E "(SCRAPING|PROCESSING|PIPELINE|Job|job)"

logs-today: ## Mostrar logs de hoje
	@echo "$(BLUE)📅 Logs de hoje...$(NC)"
	@grep "$$(date +'%Y-%m-%d')" logs/app.log | tail -50

logs-last-hour: ## Mostrar logs da última hora
	@echo "$(BLUE)⏰ Logs da última hora...$(NC)"
	@grep "$$(date +'%Y-%m-%d %H')" logs/app.log | tail -30

clean: ## Limpar arquivos temporários e cache
	@echo "$(YELLOW)🧹 Limpando arquivos temporários...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Limpeza concluída$(NC)"

# Comandos de desenvolvimento
dev-setup: ## Configurar ambiente de desenvolvimento
	@echo "$(BLUE)🔧 Configurando ambiente de desenvolvimento...$(NC)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "$(YELLOW)📦 Criando ambiente virtual...$(NC)"; \
		python -m venv $(VENV_PATH); \
	fi
	@echo "$(YELLOW)📚 Instalando dependências...$(NC)"
	@$(VENV_PATH)/bin/pip install -r requirements/development.txt
	@echo "$(YELLOW)🗄️  Aplicando migrações...$(NC)"
	@$(MANAGE) migrate
	@echo "$(GREEN)✅ Ambiente configurado$(NC)"

test: ## Executar testes
	@echo "$(BLUE)🧪 Executando testes...$(NC)"
	@$(PYTHON) -m pytest tests/ -v

test-jobs: ## Executar testes específicos dos jobs
	@echo "$(BLUE)👷 Testando jobs...$(NC)"
	@$(PYTHON) -m pytest tests/ -k "job" -v

# Comandos do Django
migrate: ## Aplicar migrações do Django
	@echo "$(BLUE)🗄️  Aplicando migrações...$(NC)"
	@$(MANAGE) migrate

makemigrations: ## Criar novas migrações
	@echo "$(BLUE)📝 Criando migrações...$(NC)"
	@$(MANAGE) makemigrations

runserver: ## Iniciar servidor Django
	@echo "$(BLUE)🌐 Iniciando servidor Django...$(NC)"
	@$(MANAGE) runserver

shell: ## Abrir Django shell
	@echo "$(BLUE)🐍 Abrindo Django shell...$(NC)"
	@$(MANAGE) shell

# Informações do sistema
info: ## Mostrar informações do sistema
	@echo "$(BOLD)📋 Informações do Sistema:$(NC)"
	@echo "$(BLUE)Python:$(NC) $$(python --version)"
	@echo "$(BLUE)Django:$(NC) $$(python -c 'import django; print(django.get_version())' 2>/dev/null || echo 'Não disponível')"
	@echo "$(BLUE)Ambiente Virtual:$(NC) $$(if [ -d "$(VENV_PATH)" ]; then echo "✅ Configurado"; else echo "❌ Não encontrado"; fi)"
	@echo "$(BLUE)Banco de Dados:$(NC) $$(if [ -f "db.sqlite3" ]; then echo "✅ db.sqlite3 encontrado"; else echo "❌ Banco não encontrado"; fi)"
	@echo "$(BLUE)Logs:$(NC) $$(if [ -f "logs/app.log" ]; then echo "✅ logs/app.log ($$(wc -l < logs/app.log) linhas)"; else echo "❌ Logs não encontrados"; fi)"

backup-logs: ## Fazer backup dos logs
	@echo "$(YELLOW)📋 Fazendo backup dos logs...$(NC)"
	@if [ -f "logs/app.log" ]; then \
		cp logs/app.log "logs/app.log.backup.$$(date +%Y%m%d_%H%M%S)"; \
		echo "$(GREEN)✅ Backup criado$(NC)"; \
	else \
		echo "$(RED)❌ Arquivo de log não encontrado$(NC)"; \
	fi

# Comando padrão
.DEFAULT_GOAL := help
