"""
Testes unitários para as tarefas de jobs.
"""

from unittest.mock import Mock, patch

from django.test import tag

from tests.base import BaseUnitTestCase
from tests.mocks.factories import DataSourceFactory


@tag("unit", "jobs", "fast")
class JobTasksTest(BaseUnitTestCase):
    """Testes unitários para as tarefas de jobs."""

    def setUp(self):
        """Setup dos testes."""
        super().setUp()
        self.data_source = DataSourceFactory(
            name="NFE FAZENDA",
            url="https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx",
            content_type="pdf",
            is_active=True,
        )

    @patch("apps.jobs.tasks.NFEFazendaScraper")
    def test_scrape_nfe_fazenda_job_success(self, mock_scraper_class):
        """Teste de job de scraping da NFE Fazenda com sucesso."""
        # Arrange
        mock_scraper = Mock()
        mock_scraper.scrape_new_items.return_value = {
            "new_items": 1,
            "errors": 0,
            "duration": 0.5,
        }
        mock_scraper_class.return_value = mock_scraper

        # Act
        from apps.jobs.tasks import scrape_nfe_fazenda_job

        result = scrape_nfe_fazenda_job()

        # Assert
        self.assertIsInstance(result, dict)
        mock_scraper.scrape_new_items.assert_called_once()

    def test_scrape_nfe_fazenda_job_no_active_source(self):
        """Teste de job de scraping sem fonte ativa."""
        # Arrange
        self.data_source.is_active = False
        self.data_source.save()

        # Act
        from apps.jobs.tasks import scrape_nfe_fazenda_job

        result = scrape_nfe_fazenda_job()

        # Assert
        self.assertIn("error", result)
        self.assertIn("Fonte de dados inativa", result["error"])

    @patch("apps.jobs.tasks.TechnicalNoteSummarizerService")
    def test_process_pending_technical_notes_job_success(self, mock_service_class):
        """Teste de job de processamento de notas pendentes."""
        # Arrange
        mock_service = Mock()
        mock_service.get_pending_notes.return_value = [
            Mock()
        ]  # Simula uma nota pendente
        mock_service.process_batch.return_value = {
            "processed": 3,
            "errors": 0,
            "duration": 1.5,
        }
        mock_service_class.return_value = mock_service

        # Act
        from apps.jobs.tasks import process_pending_technical_notes_job

        result = process_pending_technical_notes_job(max_items=5)

        # Assert
        self.assertTrue(result["success"])
        self.assertIn("stats", result)
        mock_service.get_pending_notes.assert_called_once_with(limit=5)
        mock_service.process_batch.assert_called_once()

    @patch("apps.jobs.tasks.TechnicalNoteSummarizerService")
    def test_process_pending_technical_notes_job_with_errors(self, mock_service_class):
        """Teste de job de processamento com erros."""
        # Arrange
        mock_service = Mock()
        mock_service.get_pending_notes.side_effect = Exception("Erro no processamento")
        mock_service_class.return_value = mock_service

        # Act
        from apps.jobs.tasks import process_pending_technical_notes_job

        result = process_pending_technical_notes_job(max_items=5)

        # Assert
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("apps.jobs.tasks.process_pending_technical_notes_job")
    @patch("apps.jobs.tasks.scrape_nfe_fazenda_job")
    def test_nfe_fazenda_full_pipeline_job(self, mock_scrape_job, mock_process_job):
        """Teste do job de pipeline completo."""
        # Arrange
        mock_scrape_job.return_value = {
            "success": True,
            "stats": {"new_items": 5, "errors": 0},
            "duration_seconds": 1.0,
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
        self.assertIn("scraping", result["pipeline_stats"])
        self.assertIn("processing", result["pipeline_stats"])
        mock_scrape_job.assert_called_once()
        mock_process_job.assert_called_once()

    def test_health_check_job(self):
        """Teste do job de health check."""
        # Act
        from apps.jobs.tasks import health_check_job

        result = health_check_job()

        # Assert
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
