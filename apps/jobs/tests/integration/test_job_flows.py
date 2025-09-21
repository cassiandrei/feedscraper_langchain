"""
Testes de integração para o sistema de jobs.
"""

import time
from unittest.mock import Mock, patch

from django.test import tag

from tests.base import BaseIntegrationTest
from tests.mocks.factories import DataSourceFactory, TechnicalNoteFactory

from apps.jobs.schedulers import JobSchedulerService


@tag("integration", "jobs", "slow")
class JobSchedulerIntegrationTest(BaseIntegrationTest):
    """Testes de integração para o sistema de agendamento."""

    def setUp(self):
        """Configuração para testes de integração."""
        super().setUp()
        self.scheduler_service = JobSchedulerService
        # Criar dados de teste
        self.data_source = DataSourceFactory(name="NFE FAZENDA Test", is_active=True)

    def tearDown(self):
        """Limpeza após testes de integração."""
        if (
            self.scheduler_service._scheduler
            and self.scheduler_service._scheduler.running
        ):
            self.scheduler_service.shutdown()
        super().tearDown()

    def test_scheduler_lifecycle_with_real_job(self):
        """Testa ciclo de vida completo do scheduler com job real."""
        # Arrange
        scheduler = self.scheduler_service.get_scheduler()
        job_executed = []

        def test_job():
            job_executed.append(True)

        # Act - Start scheduler
        self.scheduler_service.start()
        self.assertTrue(scheduler.running)

        # Add job
        job = self.scheduler_service.add_job(
            func=test_job, trigger="date", job_id="integration_test_job"
        )

        # Verify job was added
        jobs = self.scheduler_service.list_jobs()
        job_ids = [j.id for j in jobs]
        self.assertIn("integration_test_job", job_ids)

        # Wait a moment for potential execution
        time.sleep(0.5)

        # Remove job
        self.scheduler_service.remove_job("integration_test_job")

        # Verify job was removed
        jobs_after_removal = self.scheduler_service.list_jobs()
        job_ids_after = [j.id for j in jobs_after_removal]
        self.assertNotIn("integration_test_job", job_ids_after)

        # Shutdown
        self.scheduler_service.shutdown()
        self.assertFalse(scheduler.running)

    @patch("apps.jobs.tasks.NFEFazendaScraper")
    def test_scraping_job_integration_with_database(self, mock_scraper_class):
        """Testa integração do job de scraping com banco de dados."""
        # Arrange
        mock_scraper = Mock()
        mock_scraper.scrape_new_items.return_value = {
            "success": True,
            "new_items": 2,
            "errors": 0,
            "duration": 1.0,
        }
        mock_scraper_class.return_value = mock_scraper

        # Act
        from apps.jobs.tasks import scrape_nfe_fazenda_job

        result = scrape_nfe_fazenda_job()

        # Assert
        self.assertIsInstance(result, dict)
        self.assertTrue("success" in result or "new_items" in result)

        # Verify scraper was called
        mock_scraper_class.assert_called_once()
        mock_scraper.scrape_new_items.assert_called_once()

    @patch(
        "apps.langchain_integration.services.technical_note_processor.TechnicalNoteSummarizerService"
    )
    def test_processing_job_integration_with_database(self, mock_service_class):
        """Testa integração do job de processamento com banco de dados."""
        # Arrange - criar notas técnicas reais no banco
        note1 = TechnicalNoteFactory(source=self.data_source)
        note2 = TechnicalNoteFactory(source=self.data_source)

        mock_service = Mock()
        mock_service.get_pending_notes.return_value = [note1, note2]
        mock_service.process_batch.return_value = {
            "processed": 2,
            "errors": 0,
            "duration": 2.5,
        }
        mock_service_class.return_value = mock_service

        # Act
        from apps.jobs.tasks import process_pending_technical_notes_job

        result = process_pending_technical_notes_job(max_items=5)

        # Assert
        self.assertTrue(result["success"])
        self.assertIn("stats", result)
        self.assertEqual(result["stats"]["processed"], 2)

        # Verify service calls
        mock_service.get_pending_notes.assert_called_once_with(limit=5)
        mock_service.process_batch.assert_called_once()

    @patch("apps.jobs.tasks.process_pending_technical_notes_job")
    @patch("apps.jobs.tasks.scrape_nfe_fazenda_job")
    def test_full_pipeline_integration(self, mock_scrape_job, mock_process_job):
        """Testa pipeline completo de scraping e processamento."""
        # Arrange
        mock_scrape_job.return_value = {
            "success": True,
            "stats": {"new_items": 3, "errors": 0},
            "duration_seconds": 1.5,
        }

        mock_process_job.return_value = {
            "success": True,
            "stats": {"processed": 3, "errors": 0},
            "duration_seconds": 2.0,
        }

        # Act
        from apps.jobs.tasks import nfe_fazenda_full_pipeline_job

        result = nfe_fazenda_full_pipeline_job()

        # Assert
        self.assertTrue(result["success"])
        self.assertIn("pipeline_stats", result)

        # Verify both jobs were called
        mock_scrape_job.assert_called_once()
        mock_process_job.assert_called_once()

        # Verify pipeline stats structure
        pipeline_stats = result["pipeline_stats"]
        self.assertIn("scraping", pipeline_stats)
        self.assertIn("processing", pipeline_stats)
        self.assertEqual(pipeline_stats["scraping"]["stats"]["new_items"], 3)
        self.assertEqual(pipeline_stats["processing"]["stats"]["processed"], 3)
