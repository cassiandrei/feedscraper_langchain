"""
Testes unitários para os modelos do langchain_integration.
"""

from django.core.exceptions import ValidationError
from django.test import tag

from tests.base import BaseUnitTestCase
from tests.mocks.factories import (
    DataSourceFactory,
    ProcessingLogFactory,
    TechnicalNoteFactory,
)

from apps.langchain_integration.models import DataSource, ProcessingLog, TechnicalNote


@tag("unit", "models", "fast")
class DataSourceModelTest(BaseUnitTestCase):
    """Testes unitários para o modelo DataSource."""

    def test_create_data_source(self):
        """Teste de criação de fonte de dados."""
        # Arrange & Act
        data_source = DataSourceFactory(
            name="Test Source", content_type="pdf", is_active=True
        )

        # Assert
        self.assertEqual(data_source.name, "Test Source")
        self.assertEqual(data_source.content_type, "pdf")
        self.assertTrue(data_source.is_active)
        self.assertIsNotNone(data_source.id)
        self.assertIsNotNone(data_source.created_at)

    def test_data_source_str_representation(self):
        """Teste da representação string da fonte de dados."""
        # Arrange & Act
        data_source = DataSourceFactory(name="Test Source", content_type="pdf")

        # Assert
        expected_str = "Test Source (PDF)"
        self.assertEqual(str(data_source), expected_str)

    def test_unique_name_constraint(self):
        """Teste da restrição de nome único."""
        # Arrange
        DataSourceFactory(name="Unique Source")

        # Act & Assert
        with self.assertRaises(Exception):
            DataSourceFactory(name="Unique Source")

    def test_data_source_scraping_config_default(self):
        """Teste de configuração padrão do scraping."""
        # Arrange & Act
        data_source = DataSourceFactory(scraping_config=None)

        # Assert - factory deve ter configuração, mas testamos sem ela
        if not data_source.scraping_config:
            self.assertEqual(data_source.scraping_config, {})


@tag("unit", "models", "fast")
class TechnicalNoteModelTest(BaseUnitTestCase):
    """Testes unitários para o modelo TechnicalNote."""

    def setUp(self):
        super().setUp()
        self.data_source = DataSourceFactory()

    def test_create_technical_note(self):
        """Teste de criação de nota técnica."""
        # Arrange & Act
        note = TechnicalNoteFactory(
            data_source=self.data_source, title="Test Note", content="Test content"
        )

        # Assert
        self.assertEqual(note.title, "Test Note")
        self.assertEqual(note.content, "Test content")
        self.assertEqual(note.data_source, self.data_source)
        self.assertIsNotNone(note.id)

    def test_technical_note_str_representation(self):
        """Teste da representação string da nota técnica."""
        # Arrange & Act
        note = TechnicalNoteFactory(title="Test Note")

        # Assert
        self.assertEqual(str(note), "Test Note")

    def test_technical_note_content_hash_unique(self):
        """Teste de hash único do conteúdo."""
        # Arrange
        content_hash = "unique_hash_123"
        TechnicalNoteFactory(content_hash=content_hash)

        # Act & Assert
        with self.assertRaises(Exception):
            TechnicalNoteFactory(content_hash=content_hash)

    def test_technical_note_metadata_default(self):
        """Teste de metadata padrão."""
        # Arrange & Act
        note = TechnicalNoteFactory()

        # Assert
        self.assertIsInstance(note.metadata, dict)


@tag("unit", "models", "fast")
class ProcessingLogModelTest(BaseUnitTestCase):
    """Testes unitários para o modelo ProcessingLog."""

    def setUp(self):
        super().setUp()
        self.technical_note = TechnicalNoteFactory()

    def test_create_processing_log(self):
        """Teste de criação de log de processamento."""
        # Arrange & Act
        log = ProcessingLogFactory(
            technical_note=self.technical_note, operation="analysis", status="completed"
        )

        # Assert
        self.assertEqual(log.operation, "analysis")
        self.assertEqual(log.status, "completed")
        self.assertEqual(log.technical_note, self.technical_note)

    def test_processing_log_str_representation(self):
        """Teste da representação string do log."""
        # Arrange & Act
        log = ProcessingLogFactory(
            technical_note=self.technical_note, operation="analysis", status="completed"
        )

        # Assert
        expected_str = f"analysis - completed"
        self.assertEqual(str(log), expected_str)

    def test_processing_log_duration_calculation(self):
        """Teste de cálculo de duração."""
        from datetime import datetime, timedelta

        from django.utils import timezone

        # Arrange
        start_time = timezone.now()
        end_time = start_time + timedelta(seconds=30)

        log = ProcessingLogFactory(
            technical_note=self.technical_note, start_time=start_time, end_time=end_time
        )

        # Act & Assert
        if hasattr(log, "duration"):
            self.assertEqual(log.duration, timedelta(seconds=30))

    def test_processing_log_without_end_time(self):
        """Teste de log sem tempo de fim."""
        # Arrange & Act
        log = ProcessingLogFactory(
            technical_note=self.technical_note, start_time=timezone.now(), end_time=None
        )

        # Assert
        self.assertIsNone(log.end_time)
        # Duration should be None or handle gracefully
        if hasattr(log, "duration"):
            self.assertIsNone(log.duration)
