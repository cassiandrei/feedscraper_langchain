import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.utils import timezone

from apps.jobs.schedulers import JobSchedulerService
from apps.jobs.tasks import (
    process_pending_technical_notes_job,
    scrape_nfe_fazenda_job,
)
from apps.langchain_integration.models import DataSource


logger = logging.getLogger(__name__)


class NFEJobManager:
    """
    Gerenciador específico para jobs relacionados às notas técnicas da NFE Fazenda.

    Este manager:
    - Configura jobs recorrentes para scraping e processamento
    - Fornece métodos para execução manual
    - Monitora e relata status dos jobs
    - Gerencia configurações específicas
    """

    # IDs dos jobs para controle
    SCRAPING_JOB_ID = "nfe_fazenda_scraping"
    PROCESSING_JOB_ID = "nfe_technical_notes_processing"

    def __init__(self):
        """Inicializa o gerenciador de jobs NFE."""
        self.scheduler = JobSchedulerService()

    def setup_default_jobs(self) -> Dict[str, Any]:
        """
        Configura os jobs padrão para NFE Fazenda.

        Returns:
            Dict com status da configuração dos jobs
        """
        results = {
            "scraping_job": None,
            "processing_job": None,
            "errors": [],
        }

        try:
            logger.info("Configurando jobs padrão para NFE Fazenda")

            # 1. Job de scraping (diário às 9h)
            try:
                self.scheduler.add_job(
                    func=scrape_nfe_fazenda_job,
                    trigger="cron",
                    job_id=self.SCRAPING_JOB_ID,
                    day_of_week="mon-fri",  # Segunda a sexta
                    hour=9,
                    minute=0,
                    name="NFE Fazenda - Scraping Diário",
                    max_instances=1,
                    coalesce=True,
                )
                results["scraping_job"] = "configured"
                logger.info(f"Job de scraping configurado: {self.SCRAPING_JOB_ID}")

            except Exception as e:
                error_msg = f"Erro ao configurar job de scraping: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["scraping_job"] = "error"

            # 2. Job de processamento (a cada 2 horas durante horário comercial)
            try:
                self.scheduler.add_job(
                    func=process_pending_technical_notes_job,
                    trigger="cron",
                    job_id=self.PROCESSING_JOB_ID,
                    hour="8-18/2",  # A cada 2 horas das 8h às 18h
                    minute=15,
                    name="NFE Fazenda - Processamento IA",
                    max_instances=1,
                    coalesce=True,
                    kwargs={"max_items": 15},
                )
                results["processing_job"] = "configured"
                logger.info(
                    f"Job de processamento configurado: {self.PROCESSING_JOB_ID}"
                )

            except Exception as e:
                error_msg = f"Erro ao configurar job de processamento: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["processing_job"] = "error"

            success_count = sum(
                1 for result in results.values() if result == "configured"
            )

            logger.info(
                f"Configuração de jobs concluída: {success_count}/3 jobs configurados"
            )

            return results

        except Exception as e:
            logger.error(f"Erro geral na configuração de jobs: {str(e)}")
            results["errors"].append(f"Erro geral: {str(e)}")
            return results

    def run_scraping_now(self) -> Dict[str, Any]:
        """
        Executa o job de scraping imediatamente.

        Returns:
            Dict com resultado da execução
        """
        try:
            logger.info("Executando scraping manual da NFE Fazenda")
            result = scrape_nfe_fazenda_job()
            logger.info(f"Scraping manual concluído: {result}")
            return result
        except Exception as e:
            logger.error(f"Erro no scraping manual: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def run_processing_now(self, max_items: int = 10) -> Dict[str, Any]:
        """
        Executa o job de processamento imediatamente.

        Args:
            max_items: Número máximo de itens para processar

        Returns:
            Dict com resultado da execução
        """
        try:
            logger.info(f"Executando processamento manual (max {max_items} itens)")
            result = process_pending_technical_notes_job(max_items=max_items)
            logger.info(f"Processamento manual concluído: {result}")
            return result
        except Exception as e:
            logger.error(f"Erro no processamento manual: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def get_job_status(self) -> Dict[str, Any]:
        """
        Retorna o status de todos os jobs NFE.

        Returns:
            Dict com status detalhado dos jobs
        """
        try:
            jobs_info = self.scheduler.list_jobs()
            nfe_jobs = {}

            job_ids = [
                self.SCRAPING_JOB_ID,
                self.PROCESSING_JOB_ID,
            ]

            for job_id in job_ids:
                job_info = next(
                    (job for job in jobs_info if job.get("id") == job_id), None
                )
                if job_info:
                    nfe_jobs[job_id] = {
                        "status": "active",
                        "next_run": job_info.get("next_run"),
                        "name": job_info.get("name"),
                        "trigger": job_info.get("trigger"),
                    }
                else:
                    nfe_jobs[job_id] = {
                        "status": "not_scheduled",
                        "next_run": None,
                        "name": None,
                        "trigger": None,
                    }

            return {
                "jobs": nfe_jobs,
                "scheduler_running": self.scheduler.is_running(),
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Erro ao obter status dos jobs: {str(e)}")
            return {"error": str(e), "timestamp": timezone.now().isoformat()}

    def pause_job(self, job_id: str) -> Dict[str, Any]:
        """
        Pausa um job específico.

        Args:
            job_id: ID do job para pausar

        Returns:
            Dict com resultado da operação
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job pausado: {job_id}")
            return {
                "success": True,
                "message": f"Job {job_id} pausado com sucesso",
                "timestamp": timezone.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Erro ao pausar job {job_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def resume_job(self, job_id: str) -> Dict[str, Any]:
        """
        Resume um job pausado.

        Args:
            job_id: ID do job para resumir

        Returns:
            Dict com resultado da operação
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job resumido: {job_id}")
            return {
                "success": True,
                "message": f"Job {job_id} resumido com sucesso",
                "timestamp": timezone.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Erro ao resumir job {job_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }

    def remove_all_jobs(self) -> Dict[str, Any]:
        """
        Remove todos os jobs NFE.

        Returns:
            Dict com resultado da operação
        """
        results = {"removed": [], "errors": []}

        job_ids = [
            self.SCRAPING_JOB_ID,
            self.PROCESSING_JOB_ID,
        ]

        for job_id in job_ids:
            try:
                self.scheduler.remove_job(job_id)
                results["removed"].append(job_id)
                logger.info(f"Job removido: {job_id}")
            except Exception as e:
                error_msg = f"Erro ao remover job {job_id}: {str(e)}"
                results["errors"].append(error_msg)
                logger.warning(error_msg)

        return {
            "success": len(results["errors"]) == 0,
            "results": results,
            "timestamp": timezone.now().isoformat(),
        }

    def get_data_source_status(self) -> Dict[str, Any]:
        """
        Retorna status da fonte de dados NFE Fazenda.

        Returns:
            Dict com informações da fonte de dados
        """
        try:
            data_source = DataSource.objects.get(name="NFE FAZENDA")

            # Contar notas técnicas por status
            from django.db.models import Count

            from apps.langchain_integration.models import TechnicalNote

            status_counts = dict(
                TechnicalNote.objects.filter(source=data_source)
                .values("status")
                .annotate(count=Count("id"))
                .values_list("status", "count")
            )

            return {
                "data_source": {
                    "id": str(data_source.id),
                    "name": data_source.name,
                    "url": data_source.url,
                    "is_active": data_source.is_active,
                    "content_type": data_source.content_type,
                    "created_at": data_source.created_at.isoformat(),
                    "updated_at": data_source.updated_at.isoformat(),
                },
                "statistics": {
                    "total_notes": sum(status_counts.values()),
                    "by_status": status_counts,
                    "pending_processing": status_counts.get("pending", 0),
                    "processed": status_counts.get("processed", 0),
                    "errors": status_counts.get("error", 0),
                },
                "timestamp": timezone.now().isoformat(),
            }

        except DataSource.DoesNotExist:
            return {
                "error": "Fonte de dados NFE FAZENDA não encontrada",
                "timestamp": timezone.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Erro ao obter status da fonte de dados: {str(e)}")
            return {"error": str(e), "timestamp": timezone.now().isoformat()}
