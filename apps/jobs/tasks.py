import logging
from typing import Any, Dict

from django.utils import timezone

from apps.langchain_integration.models import DataSource, TechnicalNote
from apps.langchain_integration.services.scrapers.nfe_fazenda import NFEFazendaScraper
from apps.langchain_integration.services.technical_note_processor import (
    TechnicalNoteSummarizerService,
)

from apps.langchain_integration.services.text_processor import (
    TextProcessorService,
    TextSummarizerService,
)

logger = logging.getLogger(__name__)


def process_text_job(text: str, template: str = None) -> Dict[str, Any]:
    """
    Job task for processing text using LangChain.

    Args:
        text: The text to process
        template: Optional template string

    Returns:
        Dict containing result and metadata
    """
    start_time = timezone.now()

    try:
        logger.info(f"Starting text processing job at {start_time}")

        # Initialize service
        service = TextProcessorService(template=template)

        # Process text
        result = service.process({"text": text})

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Text processing completed in {duration}s")

        return {
            "success": result["success"],
            "result": result.get("result"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "error": result.get("error"),
            "model_used": result.get("model_used"),
        }

    except Exception as e:
        logger.error(f"Error in text processing job: {str(e)}")
        end_time = timezone.now()
        return {
            "success": False,
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
        }


def summarize_text_job(text: str, max_length: int = 150) -> Dict[str, Any]:
    """
    Job task for summarizing text using LangChain.

    Args:
        text: The text to summarize
        max_length: Maximum length of the summary

    Returns:
        Dict containing result and metadata
    """
    start_time = timezone.now()

    try:
        logger.info(f"Starting text summarization job at {start_time}")

        # Initialize service
        service = TextSummarizerService(max_length=max_length)

        # Summarize text
        result = service.process({"text": text})

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Text summarization completed in {duration}s")

        return {
            "success": result["success"],
            "result": result.get("result"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "error": result.get("error"),
            "model_used": result.get("model_used"),
        }

    except Exception as e:
        logger.error(f"Error in text summarization job: {str(e)}")
        end_time = timezone.now()
        return {
            "success": False,
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
        }


def scrape_nfe_fazenda_job() -> Dict[str, Any]:
    """
    Job para fazer scraping de notas técnicas do site da NFE Fazenda.

    Returns:
        Dict com estatísticas do scraping
    """
    start_time = timezone.now()

    try:
        logger.info(f"Iniciando job de scraping NFE Fazenda em {start_time}")

        # Buscar a fonte de dados da NFE Fazenda
        try:
            data_source = DataSource.objects.get(name="NFE FAZENDA")
        except DataSource.DoesNotExist:
            # Criar a fonte se não existir
            data_source = DataSource.objects.create(
                name="NFE FAZENDA",
                url="https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=",
                content_type="pdf",
                description="Notas técnicas oficiais sobre NFe do portal da Receita Federal",
                is_active=True,
                scraping_config={
                    "selectors": {
                        "file_links": "a[href*='exibirArquivo.aspx']",
                        "fallback_links": "a[href*='conteudo=']",
                    }
                },
            )
            logger.info("Fonte de dados NFE FAZENDA criada automaticamente")

        # Verificar se a fonte está ativa
        if not data_source.is_active:
            logger.warning("Fonte de dados NFE FAZENDA está inativa, pulando scraping")
            return {
                "success": False,
                "error": "Fonte de dados inativa",
                "start_time": start_time.isoformat(),
                "end_time": timezone.now().isoformat(),
            }

        # Inicializar scraper
        scraper = NFEFazendaScraper(data_source)

        # Executar scraping
        stats = scraper.scrape_new_items()

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(
            f"Scraping NFE Fazenda concluído em {duration:.2f}s. Stats: {stats}"
        )

        return {
            "success": True,
            "stats": stats,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "data_source_id": str(data_source.id),
        }

    except Exception as e:
        logger.error(f"Erro no job de scraping NFE Fazenda: {str(e)}")
        end_time = timezone.now()
        return {
            "success": False,
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
        }


def process_pending_technical_notes_job(max_items: int = 10) -> Dict[str, Any]:
    """
    Job para processar notas técnicas pendentes com LangChain.

    Args:
        max_items: Número máximo de itens para processar por execução

    Returns:
        Dict com estatísticas do processamento
    """
    start_time = timezone.now()

    try:
        logger.info(
            f"Iniciando processamento de notas técnicas pendentes em {start_time}"
        )

        # Inicializar service de sumarização
        summarizer_service = TechnicalNoteSummarizerService()

        # Buscar notas pendentes
        pending_notes = summarizer_service.get_pending_notes(limit=max_items)

        if not pending_notes:
            logger.info("Nenhuma nota técnica pendente encontrada")
            return {
                "success": True,
                "stats": {"total": 0, "processed": 0, "errors": 0, "skipped": 0},
                "start_time": start_time.isoformat(),
                "end_time": timezone.now().isoformat(),
            }

        # Processar em lote
        stats = summarizer_service.process_batch(pending_notes)

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Processamento concluído em {duration:.2f}s. Stats: {stats}")

        return {
            "success": True,
            "stats": stats,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
        }

    except Exception as e:
        logger.error(f"Erro no processamento de notas técnicas pendentes: {str(e)}")
        end_time = timezone.now()
        return {
            "success": False,
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
        }


def langchain_batch_job():
    """
    Batch job for processing multiple items with LangChain.
    """
    logger.info("Starting LangChain batch job")

    try:
        # Example implementation - customize based on your needs
        from apps.jobs.models import JobExecutionLog

        # Get pending items from database
        # Process them using LangChain services
        # Save results

        logger.info("LangChain batch job completed successfully")

    except Exception as e:
        logger.error(f"Error in batch job: {str(e)}")
        raise


def nfe_fazenda_full_pipeline_job() -> Dict[str, Any]:
    """
    Job completo que executa todo o pipeline: scraping + processamento.

    Returns:
        Dict com estatísticas de todo o pipeline
    """
    start_time = timezone.now()
    pipeline_stats = {"scraping": {}, "processing": {}, "total_time": 0}

    try:
        logger.info(f"Iniciando pipeline completo NFE Fazenda em {start_time}")

        # 1. Executar scraping
        scraping_result = scrape_nfe_fazenda_job()
        pipeline_stats["scraping"] = scraping_result

        if scraping_result["success"]:
            logger.info("Scraping concluído, iniciando processamento...")

            # 2. Processar notas pendentes (aguardar um pouco para dar tempo do scraping salvar)
            import time

            time.sleep(2)

            processing_result = process_pending_technical_notes_job(max_items=20)
            pipeline_stats["processing"] = processing_result
        else:
            logger.warning("Scraping falhou, pulando processamento")
            pipeline_stats["processing"] = {
                "success": False,
                "error": "Scraping falhou",
            }

        end_time = timezone.now()
        pipeline_stats["total_time"] = (end_time - start_time).total_seconds()

        logger.info(
            f"Pipeline completo concluído em {pipeline_stats['total_time']:.2f}s"
        )

        return {
            "success": True,
            "pipeline_stats": pipeline_stats,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }

    except Exception as e:
        logger.error(f"Erro no pipeline completo: {str(e)}")
        end_time = timezone.now()
        pipeline_stats["total_time"] = (end_time - start_time).total_seconds()

        return {
            "success": False,
            "error": str(e),
            "pipeline_stats": pipeline_stats,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }


def health_check_job():
    """
    Health check job to monitor system status.
    """
    try:
        logger.info("Health check job executed successfully")

        # Verificar estatísticas básicas
        from apps.langchain_integration.services.technical_note_processor import (
            TechnicalNoteSummarizerService,
        )

        service = TechnicalNoteSummarizerService()
        stats = service.get_processing_stats()

        logger.info(f"Sistema saudável. Stats: {stats}")

        return {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": timezone.now().isoformat(),
        }


def summarize_text_job(text: str, max_length: int = 150) -> Dict[str, Any]:
    """
    Job task for summarizing text using LangChain.

    Args:
        text: The text to summarize
        max_length: Maximum length of the summary

    Returns:
        Dict containing result and metadata
    """
    start_time = timezone.now()

    try:
        logger.info(f"Starting text summarization job at {start_time}")

        # Initialize service
        service = TextSummarizerService(max_length=max_length)

        # Summarize text
        result = service.process({"text": text})

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Text summarization completed in {duration}s")

        return {
            "success": result["success"],
            "result": result.get("result"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "error": result.get("error"),
            "model_used": result.get("model_used"),
            "max_length": result.get("max_length"),
        }

    except Exception as e:
        logger.error(f"Error in text summarization job: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": timezone.now().isoformat(),
        }


def langchain_batch_job():
    """
    Batch job for processing multiple items with LangChain.

    Note: JobExecutionLog is now handled automatically by django-apscheduler.
    Check DjangoJobExecution model for execution logs.
    """
    logger.info("Starting LangChain batch job")

    try:
        # Example implementation - customize based on your needs
        # from django_apscheduler.models import DjangoJob, DjangoJobExecution

        # Get pending items from database
        # Process them using LangChain services
        # Results are automatically logged by django-apscheduler

        logger.info("LangChain batch job completed successfully")

    except Exception as e:
        logger.error(f"Error in batch job: {str(e)}")
        raise


def health_check_job():
    """
    Health check job to monitor system status.
    """
    try:
        from django.core.cache import cache
        from django.db import connection

        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Check cache
        cache.set("health_check", "ok", 30)
        if cache.get("health_check") != "ok":
            raise Exception("Cache not working")

        logger.info("Health check job completed successfully")
        return True

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False
