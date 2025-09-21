#!/usr/bin/env python
"""
Exemplo de uso do FeedScraper LangChain

Este script demonstra como usar os services de LangChain e agendar jobs.
"""

import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

import logging

from apps.jobs.schedulers import JobSchedulerService
from apps.jobs.tasks import process_text_job, summarize_text_job
from apps.langchain_integration.services.text_processor import (
    TextProcessorService,
    TextSummarizerService,
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def exemplo_processamento_texto():
    """Exemplo de processamento de texto com LangChain."""
    logger.info("=== Exemplo: Processamento de Texto ===")

    # Inicializar service
    service = TextProcessorService(
        template="Analise o seguinte texto e extraia os pontos principais: {text}"
    )

    # Texto de exemplo
    texto = """
    O Django é um framework web Python de alto nível que encoraja o desenvolvimento 
    rápido e design limpo e pragmático. Construído por desenvolvedores experientes, 
    ele cuida de grande parte do aborrecimento do desenvolvimento web, para que você 
    possa se concentrar em escrever seu aplicativo sem precisar reinventar a roda.
    """

    # Processar texto
    resultado = service.process({"text": texto})

    if resultado["success"]:
        logger.info(f"Texto processado com sucesso!")
        logger.info(f"Resultado: {resultado['result']}")
    else:
        logger.error(f"Erro no processamento: {resultado['error']}")


def exemplo_sumarizacao():
    """Exemplo de sumarização de texto."""
    logger.info("=== Exemplo: Sumarização de Texto ===")

    # Inicializar service
    service = TextSummarizerService(max_length=50)

    # Texto de exemplo
    texto = """
    O LangChain é uma estrutura para desenvolvimento de aplicações alimentadas por 
    modelos de linguagem. Ele permite que você conecte um LLM (Large Language Model) 
    a outras fontes de dados e permite que o LLM interaja com seu ambiente. O 
    LangChain fornece componentes modulares para construir aplicações alimentadas 
    por LLM, e também fornece chains pré-construídas que combinam esses componentes 
    para casos de uso específicos.
    """

    # Sumarizar texto
    resultado = service.process({"text": texto})

    if resultado["success"]:
        logger.info(f"Texto sumarizado com sucesso!")
        logger.info(f"Resumo: {resultado['result']}")
    else:
        logger.error(f"Erro na sumarização: {resultado['error']}")


def exemplo_job_agendado():
    """Exemplo de agendamento de job."""
    logger.info("=== Exemplo: Job Agendado ===")

    try:
        # Iniciar o scheduler
        JobSchedulerService.start()

        # Agendar job para processar texto a cada 5 minutos
        JobSchedulerService.add_job(
            func=lambda: process_text_job(
                "Este é um texto de exemplo para processamento agendado.",
                "Processe este texto: {text}",
            ),
            trigger="interval",
            job_id="exemplo_processamento",
            minutes=5,
        )

        # Agendar job para sumarizar texto diariamente
        JobSchedulerService.add_job(
            func=lambda: summarize_text_job(
                "Este é um texto mais longo que precisa ser sumarizado regularmente...",
                100,
            ),
            trigger="cron",
            job_id="exemplo_sumarizacao",
            hour=9,  # 9h da manhã
            minute=0,
        )

        # Listar jobs agendados
        jobs = JobSchedulerService.list_jobs()
        logger.info(f"Jobs agendados: {len(jobs)}")
        for job in jobs:
            logger.info(f"- {job.id}: próxima execução em {job.next_run_time}")

    except Exception as e:
        logger.error(f"Erro ao agendar jobs: {str(e)}")


def exemplo_uso_completo():
    """Demonstra o uso completo dos services e jobs."""
    logger.info("🚀 Iniciando demonstração do FeedScraper LangChain")

    # Nota: Para usar LangChain com OpenAI, você precisa configurar OPENAI_API_KEY
    logger.info(
        "⚠️  Nota: Para executar os exemplos de LangChain, configure OPENAI_API_KEY no arquivo .env"
    )

    try:
        # Exemplo 1: Processamento de texto
        # exemplo_processamento_texto()

        # Exemplo 2: Sumarização
        # exemplo_sumarizacao()

        # Exemplo 3: Jobs agendados
        exemplo_job_agendado()

        logger.info("✅ Demonstração concluída com sucesso!")

    except Exception as e:
        logger.error(f"❌ Erro na demonstração: {str(e)}")

    finally:
        # Limpar jobs de exemplo
        try:
            JobSchedulerService.remove_job("exemplo_processamento")
            JobSchedulerService.remove_job("exemplo_sumarizacao")
            logger.info("🧹 Jobs de exemplo removidos")
        except:
            pass


if __name__ == "__main__":
    exemplo_uso_completo()
