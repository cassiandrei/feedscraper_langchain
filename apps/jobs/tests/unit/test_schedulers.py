"""
Testes unitários para o JobSchedulerService.
"""

from unittest.mock import Mock, patch

from django.test import tag

from tests.base import BaseUnitTestCase

from apps.jobs.schedulers import JobSchedulerService


@tag("unit", "jobs", "fast")
class JobSchedulerServiceTest(BaseUnitTestCase):
    """Testes unitários para o JobSchedulerService."""

    @patch("apps.jobs.schedulers.JobSchedulerService.get_scheduler")
    def test_scheduler_start(self, mock_get_scheduler):
        """Teste de inicialização do scheduler."""
        # Arrange
        mock_scheduler = Mock()
        mock_scheduler.running = False
        mock_get_scheduler.return_value = mock_scheduler

        # Act
        JobSchedulerService.start()

        # Assert
        mock_scheduler.start.assert_called_once()

    @patch("apps.jobs.schedulers.JobSchedulerService.get_scheduler")
    def test_scheduler_start_already_running(self, mock_get_scheduler):
        """Teste de inicialização do scheduler já em execução."""
        # Arrange
        mock_scheduler = Mock()
        mock_scheduler.running = True
        mock_get_scheduler.return_value = mock_scheduler

        # Act
        JobSchedulerService.start()

        # Assert
        mock_scheduler.start.assert_not_called()

    @patch("apps.jobs.schedulers.JobSchedulerService._scheduler")
    def test_scheduler_stop(self, mock_scheduler):
        """Teste de parada do scheduler."""
        # Arrange
        mock_scheduler.running = True

        # Act
        JobSchedulerService.shutdown()

        # Assert
        mock_scheduler.shutdown.assert_called_once()

    @patch("apps.jobs.schedulers.JobSchedulerService.get_scheduler")
    def test_add_job(self, mock_get_scheduler):
        """Teste de adição de job."""
        # Arrange
        mock_scheduler = Mock()
        mock_get_scheduler.return_value = mock_scheduler

        def dummy_task():
            pass

        # Act
        JobSchedulerService.add_job(
            func=dummy_task, trigger="interval", job_id="test_job", seconds=60
        )

        # Assert
        mock_scheduler.add_job.assert_called_once_with(
            func=dummy_task,
            trigger="interval",
            id="test_job",
            replace_existing=True,
            seconds=60,
        )

    @patch("apps.jobs.schedulers.JobSchedulerService.get_scheduler")
    def test_remove_job(self, mock_get_scheduler):
        """Teste de remoção de job."""
        # Arrange
        mock_scheduler = Mock()
        mock_get_scheduler.return_value = mock_scheduler

        # Act
        JobSchedulerService.remove_job("test_job")

        # Assert
        mock_scheduler.remove_job.assert_called_once_with("test_job")

    @patch("apps.jobs.schedulers.JobSchedulerService.get_scheduler")
    def test_list_jobs(self, mock_get_scheduler):
        """Teste de listagem de jobs."""
        # Arrange
        mock_scheduler = Mock()
        mock_job = Mock()
        mock_job.id = "test_job"
        mock_scheduler.get_jobs.return_value = [mock_job]
        mock_get_scheduler.return_value = mock_scheduler

        # Act
        jobs = JobSchedulerService.list_jobs()

        # Assert
        mock_scheduler.get_jobs.assert_called_once()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, "test_job")
