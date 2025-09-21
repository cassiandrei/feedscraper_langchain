"""
Testes unitários para os modelos do langchain_integration.
"""

from django.core.exceptions import ValidationError
from django.test import tag
from django.utils import timezone

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
        # Arrange & Act - Cria DataSource sem especificar scraping_config
        # para testar o default do modelo
        data_source = DataSource.objects.create(
            name="Test Source Default Config",
            url="http://example.com",
            content_type="html",
            description="Test description",
        )

        # Assert - Deve usar o default=dict do modelo
        self.assertEqual(data_source.scraping_config, {})
        self.assertIsInstance(data_source.scraping_config, dict)


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
            source=self.data_source,
            title="Test Note",
            content_preview="Test content preview",
        )

        # Assert
        self.assertEqual(note.title, "Test Note")
        self.assertEqual(note.content_preview, "Test content preview")
        self.assertEqual(note.source, self.data_source)
        self.assertIsNotNone(note.id)

    def test_technical_note_str_representation(self):
        """Teste da representação string da nota técnica."""
        # Arrange & Act
        note = TechnicalNoteFactory(title="Test Note")

        # Assert
        # O modelo retorna f"{self.title[:50]}... - {self.source.name}"
        expected_str = f"{note.title[:50]}... - {note.source.name}"
        self.assertEqual(str(note), expected_str)

    def test_technical_note_document_hash_unique(self):
        """Teste de hash único do documento."""
        # Arrange
        document_hash = "unique_hash_123"
        TechnicalNoteFactory(document_hash=document_hash)

        # Act & Assert
        with self.assertRaises(Exception):
            TechnicalNoteFactory(document_hash=document_hash)

    def test_technical_note_status_default(self):
        """Teste de status padrão."""
        # Arrange & Act
        note = TechnicalNoteFactory()

        # Assert
        self.assertEqual(note.status, "pending")

    def test_technical_note_fields(self):
        """Teste de campos principais do modelo."""
        # Arrange & Act
        note = TechnicalNoteFactory(
            title="Test Technical Note",
            original_url="http://example.com/note.pdf",
            publication_date="2023-01-15",
        )

        # Assert
        self.assertEqual(note.title, "Test Technical Note")
        self.assertEqual(note.original_url, "http://example.com/note.pdf")
        self.assertIsNotNone(note.publication_date)
        self.assertIsNotNone(note.document_hash)
        self.assertIsInstance(note.file_size, int)
        self.assertIsNotNone(note.local_file_path)


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
            technical_note=self.technical_note, operation="processing", level="info"
        )

        # Assert
        self.assertEqual(log.technical_note, self.technical_note)
        self.assertEqual(log.operation, "processing")
        self.assertEqual(log.level, "info")
        self.assertIsInstance(log.message, str)
        self.assertIsInstance(log.details, dict)
        self.assertTrue(log.is_active)

    def test_processing_log_str_representation(self):
        """Teste da representação string do log."""
        # Arrange & Act
        log = ProcessingLogFactory(
            technical_note=self.technical_note, operation="processing", level="info"
        )

        # Assert
        expected_str = f"{log.operation.title()}: {log.message[:50]}..."
        self.assertEqual(str(log), expected_str)

    def test_processing_log_execution_time(self):
        """Teste de tempo de execução."""
        # Arrange & Act
        execution_time = 2.5
        log = ProcessingLogFactory(
            technical_note=self.technical_note,
            operation="processing",
            execution_time=execution_time,
        )

        # Assert
        self.assertEqual(log.execution_time, execution_time)
        self.assertIsInstance(log.execution_time, float)

    def test_processing_log_details_field(self):
        """Teste do campo details do log."""
        # Arrange & Act
        custom_details = {"step": "validation", "errors": 0, "warnings": 2}
        log = ProcessingLogFactory(
            technical_note=self.technical_note,
            operation="validation",
            details=custom_details,
        )

        # Assert
        self.assertEqual(log.details, custom_details)
        self.assertIn("step", log.details)
        self.assertEqual(log.details["errors"], 0)
        # Duration should be None or handle gracefully
        if hasattr(log, "duration"):
            self.assertIsNone(log.duration)
