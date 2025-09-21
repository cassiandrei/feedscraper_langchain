"""
Testes para o sistema de Jobs e APScheduler.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase
from django.utils import timezone

from apps.jobs.schedulers import JobSchedulerService
from apps.jobs.tasks import (
    health_check_job,
    nfe_fazenda_full_pipeline_job,
    process_pending_technical_notes_job,
    scrape_nfe_fazenda_job,
)
from apps.langchain_integration.models import DataSource, TechnicalNote


class JobSchedulerServiceTest(TestCase):
    """Testes para o JobSchedulerService."""

    @patch('apps.jobs.schedulers.JobSchedulerService.get_scheduler')
    def test_scheduler_start(self, mock_get_scheduler):
        """Teste de inicialização do scheduler."""
        mock_scheduler = Mock()
        mock_scheduler.running = False
        mock_get_scheduler.return_value = mock_scheduler
        
        JobSchedulerService.start()
        
        mock_scheduler.start.assert_called_once()

    @patch('apps.jobs.schedulers.JobSchedulerService.get_scheduler')
    def test_scheduler_start_already_running(self, mock_get_scheduler):
        """Teste de inicialização do scheduler já em execução."""
        mock_scheduler = Mock()
        mock_scheduler.running = True
        mock_get_scheduler.return_value = mock_scheduler
        
        JobSchedulerService.start()
        
        mock_scheduler.start.assert_not_called()

    @patch('apps.jobs.schedulers.JobSchedulerService._scheduler')
    def test_scheduler_stop(self, mock_scheduler):
        """Teste de parada do scheduler."""
        mock_scheduler.running = True
        
        JobSchedulerService.shutdown()
        
        mock_scheduler.shutdown.assert_called_once()

    @patch('apps.jobs.schedulers.JobSchedulerService.get_scheduler')
    def test_add_job(self, mock_get_scheduler):
        """Teste de adição de job."""
        mock_scheduler = Mock()
        mock_get_scheduler.return_value = mock_scheduler
        
        def dummy_task():
            pass
        
        JobSchedulerService.add_job(
            func=dummy_task,
            trigger='interval',
            job_id='test_job',
            seconds=60
        )
        
        mock_scheduler.add_job.assert_called_once_with(
            func=dummy_task,
            trigger='interval',
            id='test_job',
            replace_existing=True,
            seconds=60
        )

    @patch('apps.jobs.schedulers.JobSchedulerService.get_scheduler')
    def test_remove_job(self, mock_get_scheduler):
        """Teste de remoção de job."""
        mock_scheduler = Mock()
        mock_get_scheduler.return_value = mock_scheduler
        
        JobSchedulerService.remove_job('test_job')
        
        mock_scheduler.remove_job.assert_called_once_with('test_job')

    @patch('apps.jobs.schedulers.JobSchedulerService.get_scheduler')
    def test_list_jobs(self, mock_get_scheduler):
        """Teste de listagem de jobs."""
        mock_scheduler = Mock()
        mock_job = Mock()
        mock_job.id = 'test_job'
        mock_scheduler.get_jobs.return_value = [mock_job]
        mock_get_scheduler.return_value = mock_scheduler
        
        jobs = JobSchedulerService.list_jobs()
        
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, 'test_job')
        mock_scheduler.get_jobs.assert_called_once()

    @patch('apps.jobs.schedulers.JobSchedulerService._scheduler')
    def test_is_running(self, mock_scheduler):
        """Teste de verificação se scheduler está rodando."""
        mock_scheduler.running = True
        
        result = JobSchedulerService.is_running()
        
        self.assertTrue(result)


class JobTasksTest(TestCase):
    """Testes para as tarefas de jobs."""

    def setUp(self):
        """Setup dos testes."""
        # Criar uma fonte de dados para testes
        self.data_source = DataSource.objects.create(
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

    @patch('apps.jobs.tasks.NFEFazendaScraper')
    def test_scrape_nfe_fazenda_job_success(self, mock_scraper_class):
        """Teste de job de scraping da NFE Fazenda com sucesso."""
        mock_scraper = Mock()
        mock_scraper.scrape_new_items.return_value = {
            'new_items': 1,
            'errors': 0,
            'duration': 0.5
        }
        mock_scraper_class.return_value = mock_scraper

        from apps.jobs.tasks import scrape_nfe_fazenda_job
        result = scrape_nfe_fazenda_job()

        self.assertIsInstance(result, dict)
        mock_scraper.scrape_new_items.assert_called_once()

    def test_scrape_nfe_fazenda_job_no_active_source(self):
        """Teste de job de scraping sem fonte ativa."""
        # Desativar a fonte
        self.data_source.is_active = False
        self.data_source.save()

        from apps.jobs.tasks import scrape_nfe_fazenda_job
        result = scrape_nfe_fazenda_job()

        self.assertIn('error', result)
        self.assertIn('Fonte de dados inativa', result['error'])

    @patch('apps.jobs.tasks.TechnicalNoteSummarizerService')
    def test_process_pending_technical_notes_job_success(self, mock_service_class):
        """Teste de job de processamento de notas pendentes."""
        mock_service = Mock()
        mock_service.get_pending_notes.return_value = [Mock()]  # Simula uma nota pendente
        mock_service.process_batch.return_value = {
            'processed': 3,
            'errors': 0,
            'duration': 1.5
        }
        mock_service_class.return_value = mock_service

        from apps.jobs.tasks import process_pending_technical_notes_job
        result = process_pending_technical_notes_job(max_items=5)

        self.assertTrue(result['success'])
        self.assertIn('stats', result)
        mock_service.get_pending_notes.assert_called_once_with(limit=5)
        mock_service.process_batch.assert_called_once()

    @patch('apps.jobs.tasks.TechnicalNoteSummarizerService')
    def test_process_pending_technical_notes_job_with_errors(self, mock_service_class):
        """Teste de job de processamento com erros."""
        mock_service = Mock()
        mock_service.get_pending_notes.side_effect = Exception("Erro no processamento")
        mock_service_class.return_value = mock_service

        from apps.jobs.tasks import process_pending_technical_notes_job
        result = process_pending_technical_notes_job(max_items=5)

        self.assertFalse(result['success'])
        self.assertIn('error', result)

    @patch('apps.jobs.tasks.process_pending_technical_notes_job')
    @patch('apps.jobs.tasks.scrape_nfe_fazenda_job')
    def test_nfe_fazenda_full_pipeline_job(self, mock_scrape_job, mock_process_job):
        """Teste do job de pipeline completo."""
        mock_scrape_job.return_value = {
            'success': True,
            'stats': {'new_items': 5, 'errors': 0},
            'duration_seconds': 1.0
        }
        
        mock_process_job.return_value = {
            'success': True,
            'stats': {'processed': 3, 'errors': 0},
            'duration_seconds': 2.0
        }

        from apps.jobs.tasks import nfe_fazenda_full_pipeline_job
        result = nfe_fazenda_full_pipeline_job()

        self.assertTrue(result['success'])
        self.assertIn('pipeline_stats', result)
        self.assertIn('scraping', result['pipeline_stats'])
        self.assertIn('processing', result['pipeline_stats'])
        mock_scrape_job.assert_called_once()
        mock_process_job.assert_called_once()

    def test_health_check_job(self):
        """Teste do job de health check."""
        from apps.jobs.tasks import health_check_job
        result = health_check_job()

        # A função health_check_job retorna boolean diretamente
        self.assertIsInstance(result, bool)
        self.assertTrue(result)

    

    @patch('apps.jobs.tasks.scrape_nfe_fazenda_job')
    @patch('apps.jobs.tasks.process_pending_technical_notes_job')
    def test_nfe_fazenda_full_pipeline_job(self, mock_process_job, mock_scrape_job):
        """Teste do job de pipeline completo."""
        # Mock dos jobs individuais
        mock_scrape_job.return_value = {
            'success': True,
            'stats': {'new_items': 5}
        }
        mock_process_job.return_value = {
            'success': True,
            'processed': 5
        }

        result = nfe_fazenda_full_pipeline_job()

        self.assertTrue(result['success'])
        self.assertEqual(result['pipeline_stats']['scraping']['stats']['new_items'], 5)
        self.assertEqual(result['pipeline_stats']['processing']['processed'], 5)

        mock_scrape_job.assert_called_once()
        mock_process_job.assert_called_once_with(max_items=20)

    def test_health_check_job(self):
        """Teste do job de health check."""
        # Criar alguns dados para verificação
        TechnicalNote.objects.create(
            source=self.data_source,
            title="Nota Teste",
            original_url="https://example.com/teste.pdf",
            document_hash="hash_test",
            status="pending"
        )

        result = health_check_job()

        self.assertIsInstance(result, bool)
        self.assertTrue(result)
