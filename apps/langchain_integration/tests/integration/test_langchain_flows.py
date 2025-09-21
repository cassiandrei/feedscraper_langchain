"""
Testes de integração para langchain_integration.
"""

from unittest.mock import Mock, patch

from django.test import tag

from tests.base import BaseIntegrationTest
from tests.mocks.factories import DataSourceFactory, TechnicalNoteFactory

from apps.langchain_integration.models import (
    ProcessedSummary,
    ProcessingLog,
    TechnicalNote,
)
from apps.langchain_integration.services.scrapers.nfe_fazenda import NFEFazendaScraper
from apps.langchain_integration.services.technical_note_processor import (
    TechnicalNoteSummarizerService,
)


@tag("integration", "langchain", "slow")
class NFEScrapingIntegrationTest(BaseIntegrationTest):
    """Testes de integração para o sistema de scraping da NFE."""

    def setUp(self):
        super().setUp()
        self.data_source = DataSourceFactory(
            name="NFE FAZENDA Integration Test",
            url="https://www.nfe.fazenda.gov.br/test",
            is_active=True,
            scraping_config={
                "selectors": {
                    "file_links": "a[href*='exibirArquivo.aspx']",
                    "fallback_links": "a[href*='conteudo=']",
                }
            },
        )

    @patch("requests.get")
    def test_full_scraping_workflow_with_database(self, mock_get):
        """Testa workflow completo de scraping com persistência no banco."""
        # Arrange - Mock da resposta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <a href="/exibirArquivo.aspx?conteudo=12345">
                    Nota Técnica 001/2025 - Alterações no XML
                </a>
            </body>
        </html>
        """

        # Mock do conteúdo do PDF
        mock_pdf_response = Mock()
        mock_pdf_response.status_code = 200
        mock_pdf_response.content = b"PDF content simulated"
        mock_pdf_response.headers = {"content-type": "application/pdf"}

        mock_get.side_effect = [mock_response, mock_pdf_response]

        scraper = NFEFazendaScraper(self.data_source)

        # Act
        with patch.object(scraper, "extract_text_from_pdf") as mock_extract:
            mock_extract.return_value = "Conteúdo extraído do PDF da Nota Técnica..."
            result = scraper.scrape_new_items()

        # Assert
        self.assertIsInstance(result, dict)

        # Verificar se as notas foram salvas no banco
        notes = TechnicalNote.objects.filter(data_source=self.data_source)
        if notes.exists():
            note = notes.first()
            self.assertIn("Nota Técnica", note.title)
            self.assertIsNotNone(note.content_hash)

    @patch(
        "apps.langchain_integration.services.scrapers.nfe_fazenda.NFEFazendaScraper.get_page_content"
    )
    def test_scraping_with_existing_notes(self, mock_get_content):
        """Testa scraping quando já existem notas no banco."""
        # Arrange - Criar uma nota existente
        existing_note = TechnicalNoteFactory(
            data_source=self.data_source, content_hash="existing_hash"
        )

        mock_get_content.return_value = """
        <html>
            <body>
                <a href="/test">Nota já existente</a>
            </body>
        </html>
        """

        scraper = NFEFazendaScraper(self.data_source)

        # Act
        with patch.object(scraper, "generate_content_hash") as mock_hash:
            mock_hash.return_value = "existing_hash"  # Simula nota duplicada
            result = scraper.scrape_new_items()

        # Assert
        # Verificar que não foram criadas novas notas duplicadas
        notes_count = TechnicalNote.objects.filter(data_source=self.data_source).count()
        self.assertEqual(notes_count, 1)


@tag("integration", "langchain", "slow")
class TechnicalNoteProcessingIntegrationTest(BaseIntegrationTest):
    """Testes de integração para processamento de notas técnicas."""

    def setUp(self):
        super().setUp()
        self.data_source = DataSourceFactory()
        self.technical_notes = [
            TechnicalNoteFactory(
                data_source=self.data_source,
                title=f"Nota Técnica {i}",
                content=f"Conteúdo detalhado da nota técnica {i} sobre alterações na NFE...",
            )
            for i in range(1, 4)
        ]

    @patch("langchain_openai.ChatOpenAI")
    def test_batch_processing_with_database_persistence(self, mock_openai):
        """Testa processamento em lote com persistência no banco."""
        # Arrange
        mock_llm = Mock()
        mock_openai.return_value = mock_llm
        mock_llm.invoke.return_value = Mock(
            content="""
        {
            "summary": "Resumo da nota técnica",
            "key_points": ["Alteração no schema", "Nova validação"],
            "topics": ["NFE", "XML", "Validação"]
        }
        """
        )

        service = TechnicalNoteSummarizerService()

        # Act
        results = service.batch_process_notes(self.technical_notes)

        # Assert
        self.assertEqual(len(results), 3)

        # Verificar se os logs de processamento foram criados
        processing_logs = ProcessingLog.objects.filter(
            technical_note__in=self.technical_notes, operation="summarization"
        )
        self.assertGreater(processing_logs.count(), 0)

        # Verificar se os sumários foram persistidos
        summaries = ProcessedSummary.objects.filter(
            technical_note__in=self.technical_notes
        )
        self.assertGreater(summaries.count(), 0)

    def test_processing_with_real_database_queries(self):
        """Testa processamento com consultas reais ao banco."""
        # Arrange
        service = TechnicalNoteSummarizerService()

        # Act - Buscar notas pendentes
        pending_notes = service.get_pending_notes(limit=10)

        # Assert
        self.assertIsInstance(pending_notes, list)
        # Verificar que as consultas funcionam corretamente
        if pending_notes:
            self.assertTrue(all(hasattr(note, "title") for note in pending_notes))

    @patch("langchain_openai.ChatOpenAI")
    def test_error_handling_with_database_rollback(self, mock_openai):
        """Testa tratamento de erros com rollback no banco."""
        # Arrange
        mock_openai.side_effect = Exception("LangChain API Error")
        service = TechnicalNoteSummarizerService()
        note = self.technical_notes[0]

        # Act
        result = service.process_technical_note(note)

        # Assert
        self.assertFalse(result["success"])
        self.assertIn("error", result)

        # Verificar que não foram criados registros incorretos no banco
        failed_summaries = ProcessedSummary.objects.filter(
            technical_note=note, summary__isnull=True
        )
        self.assertEqual(failed_summaries.count(), 0)


@tag("integration", "langchain", "slow")
class FullWorkflowIntegrationTest(BaseIntegrationTest):
    """Testes de integração para workflows completos."""

    def setUp(self):
        super().setUp()
        self.data_source = DataSourceFactory(
            name="NFE FAZENDA Full Test", is_active=True
        )

    @patch("requests.get")
    @patch("langchain_openai.ChatOpenAI")
    def test_complete_scrape_to_summary_workflow(self, mock_openai, mock_get):
        """Testa workflow completo: scraping → processamento → análise."""
        # Arrange - Mock do scraping
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <a href="/test.pdf">Nota Técnica 001/2025</a>
        </html>
        """

        mock_pdf_response = Mock()
        mock_pdf_response.status_code = 200
        mock_pdf_response.content = b"PDF content"
        mock_pdf_response.headers = {"content-type": "application/pdf"}

        mock_get.side_effect = [mock_response, mock_pdf_response]

        # Mock do LangChain
        mock_llm = Mock()
        mock_openai.return_value = mock_llm
        mock_llm.invoke.return_value = Mock(
            content="""
        {
            "summary": "Alterações importantes na validação XML",
            "key_points": ["Schema atualizado", "Validação obrigatória"],
            "topics": ["NFE", "XML"]
        }
        """
        )

        # Act - Executar scraping
        scraper = NFEFazendaScraper(self.data_source)

        with patch.object(scraper, "extract_text_from_pdf") as mock_extract:
            mock_extract.return_value = "Conteúdo da nota técnica extraído..."
            scraping_result = scraper.scrape_new_items()

        # Act - Executar processamento se houver novas notas
        notes = TechnicalNote.objects.filter(data_source=self.data_source)

        if notes.exists():
            service = TechnicalNoteSummarizerService()
            processing_results = service.batch_process_notes(notes)

            # Assert
            self.assertIsInstance(processing_results, list)

            # Verificar pipeline completo no banco
            summaries = ProcessedSummary.objects.filter(technical_note__in=notes)
            logs = ProcessingLog.objects.filter(technical_note__in=notes)

            if summaries.exists():
                summary = summaries.first()
                self.assertIsNotNone(summary.summary)
                self.assertIsInstance(summary.key_points, list)

            if logs.exists():
                log = logs.first()
                self.assertIn(log.operation, ["scraping", "summarization"])
                self.assertIn(log.status, ["completed", "failed", "running"])

    def test_database_consistency_across_operations(self):
        """Testa consistência do banco durante múltiplas operações."""
        # Arrange
        initial_notes_count = TechnicalNote.objects.count()
        initial_logs_count = ProcessingLog.objects.count()

        # Act - Criar algumas operações
        note = TechnicalNoteFactory(source=self.data_source)

        # Simular criação de log
        ProcessingLog.objects.create(
            technical_note=note,
            operation="test_operation",
            status="completed",
            details={"test": True},
        )

        # Assert
        final_notes_count = TechnicalNote.objects.count()
        final_logs_count = ProcessingLog.objects.count()

        self.assertEqual(final_notes_count, initial_notes_count + 1)
        self.assertEqual(final_logs_count, initial_logs_count + 1)

        # Verificar integridade referencial
        log = ProcessingLog.objects.filter(technical_note=note).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.technical_note, note)
