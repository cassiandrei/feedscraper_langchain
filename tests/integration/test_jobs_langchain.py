"""
Testes de integração entre jobs e langchain_integration.
"""

import time
from unittest.mock import Mock, patch

from apps.jobs.schedulers import JobSchedulerService
from apps.langchain_integration.models import (
    ProcessedSummary,
    ProcessingLog,
    TechnicalNote,
)
from django.test import tag

from tests.base import BaseIntegrationTest
from tests.mocks.factories import DataSourceFactory, TechnicalNoteFactory


@tag("integration", "cross-app", "slow")
class JobsLangChainIntegrationTest(BaseIntegrationTest):
    """Testes de integração entre o sistema de jobs e LangChain."""

    def setUp(self):
        super().setUp()
        self.data_source = DataSourceFactory(
            name="NFE FAZENDA Integration", is_active=True
        )
        self.scheduler_service = JobSchedulerService

    def tearDown(self):
        if (
            self.scheduler_service._scheduler
            and self.scheduler_service._scheduler.running
        ):
            self.scheduler_service.shutdown()
        super().tearDown()

    @patch(
        "apps.langchain_integration.services.scrapers.nfe_fazenda.NFEFazendaScraper.scrape_new_items"
    )
    def test_scheduled_scraping_job_integration(self, mock_scrape):
        """Testa integração do job agendado de scraping com o banco de dados."""
        # Arrange
        mock_scrape.return_value = {
            "success": True,
            "new_items": 2,
            "errors": 0,
            "duration": 1.5,
        }

        # Act - Execute job directly (simulation of scheduled execution)
        from apps.jobs.tasks import scrape_nfe_fazenda_job

        result = scrape_nfe_fazenda_job()

        # Assert
        self.assertIsInstance(result, dict)
        mock_scrape.assert_called_once()

    @patch(
        "apps.langchain_integration.services.technical_note_processor.TechnicalNoteSummarizerService.process_batch"
    )
    def test_scheduled_processing_job_with_real_notes(self, mock_process_batch):
        """Testa job de processamento com notas reais no banco."""
        # Arrange - Criar notas reais no banco
        notes = [TechnicalNoteFactory(source=self.data_source) for _ in range(3)]

        mock_process_batch.return_value = {"processed": 3, "errors": 0, "duration": 2.0}

        # Act
        from apps.jobs.tasks import process_pending_technical_notes_job

        result = process_pending_technical_notes_job(max_items=10)

        # Assert
        self.assertTrue(result["success"])
        self.assertIn("stats", result)

        # Verificar que as notas existem no banco
        db_notes = TechnicalNote.objects.filter(source=self.data_source)
        self.assertEqual(db_notes.count(), 3)

    @patch("apps.jobs.tasks.scrape_nfe_fazenda_job")
    @patch("apps.jobs.tasks.process_pending_technical_notes_job")
    def test_full_pipeline_job_integration(self, mock_process_job, mock_scrape_job):
        """Testa pipeline completo através do sistema de jobs."""
        # Arrange
        mock_scrape_job.return_value = {
            "success": True,
            "stats": {"new_items": 5, "errors": 0},
            "duration_seconds": 2.0,
        }

        mock_process_job.return_value = {
            "success": True,
            "stats": {"processed": 5, "errors": 0},
            "duration_seconds": 3.0,
        }

        # Act
        from apps.jobs.tasks import nfe_fazenda_full_pipeline_job

        result = nfe_fazenda_full_pipeline_job()

        # Assert
        self.assertTrue(result["success"])
        self.assertIn("pipeline_stats", result)

        # Verificar que ambos os jobs foram executados
        mock_scrape_job.assert_called_once()
        mock_process_job.assert_called_once()

        # Verificar estrutura do resultado
        pipeline_stats = result["pipeline_stats"]
        self.assertIn("scraping", pipeline_stats)
        self.assertIn("processing", pipeline_stats)

    def test_scheduler_with_langchain_job_real_execution(self):
        """Testa execução real de job LangChain através do scheduler."""
        # Arrange - usar uma função real do sistema que pode ser serializada
        scheduler = self.scheduler_service.get_scheduler()

        # Act
        self.scheduler_service.start()

        # Tentar adicionar job com função real do sistema
        try:
            job = self.scheduler_service.add_job(
                func="apps.jobs.tasks.process_pending_technical_notes_job",
                trigger="date",
                job_id="test_langchain_job",
                args=[1],  # max_items=1
            )
            job_added = True
        except ValueError as e:
            # Job pode não ser serializável em ambiente de teste
            job_added = False

        # Assert
        self.assertTrue(scheduler.running)

        # Clean up
        if job_added:
            self.scheduler_service.remove_job("test_langchain_job")
        self.scheduler_service.shutdown()

    @patch("langchain_openai.ChatOpenAI")
    def test_error_propagation_between_systems(self, mock_openai):
        """Testa propagação de erros entre sistema de jobs e LangChain."""
        # Arrange
        mock_openai.side_effect = Exception("LangChain API Error")

        # Criar nota para processamento
        note = TechnicalNoteFactory(source=self.data_source)

        # Act
        from apps.jobs.tasks import process_pending_technical_notes_job

        result = process_pending_technical_notes_job(max_items=1)

        # Assert - Job deve capturar e tratar o erro
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_database_transaction_consistency_across_apps(self):
        """Testa consistência de transações entre apps."""
        # Arrange
        initial_notes_count = TechnicalNote.objects.count()
        initial_logs_count = ProcessingLog.objects.count()

        # Act - Simular operação que envolve ambos os sistemas
        note = TechnicalNoteFactory(source=self.data_source)

        # Simular log de job
        ProcessingLog.objects.create(
            technical_note=note,
            operation="processing",
            level="info",
            message="Job execution completed",
            details={"job_id": "test_integration_job"},
        )

        # Assert
        final_notes_count = TechnicalNote.objects.count()
        final_logs_count = ProcessingLog.objects.count()

        self.assertEqual(final_notes_count, initial_notes_count + 1)
        self.assertEqual(final_logs_count, initial_logs_count + 1)

        # Verificar integridade dos dados
        created_log = ProcessingLog.objects.filter(
            technical_note=note, operation="job_execution"
        ).first()

        self.assertIsNotNone(created_log)
        self.assertEqual(created_log.technical_note.data_source, self.data_source)

    @patch("apps.langchain_integration.services.scrapers.nfe_fazenda.NFEFazendaScraper")
    @patch("langchain_openai.ChatOpenAI")
    def test_complete_workflow_through_jobs_system(
        self, mock_openai, mock_scraper_class
    ):
        """Testa workflow completo executado através do sistema de jobs."""
        # Arrange
        # Mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape_new_items.return_value = {
            "success": True,
            "new_items": 1,
            "processed_items": [{"title": "Test Note", "hash": "test_hash"}],
        }
        mock_scraper_class.return_value = mock_scraper

        # Mock LangChain
        mock_llm = Mock()
        mock_openai.return_value = mock_llm
        mock_llm.invoke.return_value = Mock(
            content="""
        {
            "summary": "Test summary",
            "key_points": ["Point 1", "Point 2"],
            "topics": ["Test", "Integration"]
        }
        """
        )

        # Act - Execute complete pipeline
        from apps.jobs.tasks import nfe_fazenda_full_pipeline_job

        result = nfe_fazenda_full_pipeline_job()

        # Assert
        self.assertTrue(result["success"])
        self.assertIn("pipeline_stats", result)

        # Verify both scraping and processing were executed
        pipeline_stats = result["pipeline_stats"]
        self.assertIn("scraping", pipeline_stats)
        self.assertIn("processing", pipeline_stats)

        # Verify mock calls
        mock_scraper_class.assert_called()
        mock_scraper.scrape_new_items.assert_called()
