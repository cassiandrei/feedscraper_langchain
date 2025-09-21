#!/bin/bash
# Script para monitorar logs NFE Fazenda com filtros e cores

LOG_FILE="logs/app.log"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Monitorando logs NFE Fazenda...${NC}"
echo -e "${BLUE}📁 Arquivo: $LOG_FILE${NC}"
echo -e "${YELLOW}⏰ Iniciado em: $(date)${NC}"
echo -e "${PURPLE}💡 Para parar: Ctrl+C${NC}"
echo "================================================"

# Função para destacar diferentes tipos de log
highlight_logs() {
    while IFS= read -r line; do
        if [[ $line == *"ERROR"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ $line == *"WARNING"* ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ $line == *"INFO"* ]] && [[ $line == *"job"* || $line == *"Job"* || $line == *"NFE"* || $line == *"scraping"* ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ $line == *"DEBUG"* ]]; then
            echo -e "${BLUE}$line${NC}"
        else
            echo "$line"
        fi
    done
}

# Verificar se arquivo existe
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${RED}❌ Arquivo de log não encontrado: $LOG_FILE${NC}"
    exit 1
fi

# Monitorar com filtros e cores
case "${1:-all}" in
    "jobs")
        echo -e "${PURPLE}🔍 Filtro: Apenas logs de jobs${NC}"
        echo "================================================"
        tail -f "$LOG_FILE" | grep -E "(job|scheduler|Job|Scheduler|NFE|nfe|scraping)" | highlight_logs
        ;;
    "errors")
        echo -e "${PURPLE}🔍 Filtro: Apenas erros${NC}"
        echo "================================================"
        tail -f "$LOG_FILE" | grep "ERROR" | highlight_logs
        ;;
    "clean")
        echo -e "${PURPLE}🔍 Filtro: Sem DEBUG${NC}"
        echo "================================================"
        tail -f "$LOG_FILE" | grep -v "DEBUG" | highlight_logs
        ;;
    "last")
        echo -e "${PURPLE}🔍 Mostrando últimas 20 linhas e continuando...${NC}"
        echo "================================================"
        tail -n 20 -f "$LOG_FILE" | highlight_logs
        ;;
    *)
        echo -e "${PURPLE}🔍 Mostrando todos os logs${NC}"
        echo "================================================"
        tail -f "$LOG_FILE" | highlight_logs
        ;;
esac
