import uuid
from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase
from django.utils import timezone

from apps.langchain_integration.models import (
    DataSource,
    ProcessedSummary,
    ProcessingLog,
    TechnicalNote,
)
from apps.langchain_integration.services.scrapers.base import BaseFeedScraper
from apps.langchain_integration.services.scrapers.nfe_fazenda import NFEFazendaScraper
from apps.langchain_integration.services.technical_note_processor import (
    TechnicalNoteSummarizerService,
)


class DataSourceModelTest(TestCase):
    """Testes para o modelo DataSource."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.data_source_data = {
            "name": "Test Source",
            "url": "https://example.com/feed",
            "content_type": "pdf",
            "description": "Test data source",
            "is_active": True,
            "scraping_config": {"test": "config"},
        }

    def test_create_data_source(self):
        """Teste de criação de fonte de dados."""
        data_source = DataSource.objects.create(**self.data_source_data)

        self.assertEqual(data_source.name, "Test Source")
        self.assertEqual(data_source.content_type, "pdf")
        self.assertTrue(data_source.is_active)
        self.assertIsNotNone(data_source.id)
        self.assertIsNotNone(data_source.created_at)

    def test_data_source_str_representation(self):
        """Teste da representação string da fonte de dados."""
        data_source = DataSource.objects.create(**self.data_source_data)
        expected_str = f"{self.data_source_data['name']} (PDF)"
        self.assertEqual(str(data_source), expected_str)

    def test_unique_name_constraint(self):
        """Teste da restrição de nome único."""
        DataSource.objects.create(**self.data_source_data)

        with self.assertRaises(Exception):
            DataSource.objects.create(**self.data_source_data)


class TechnicalNoteModelTest(TestCase):
    """Testes para o modelo TechnicalNote."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.data_source = DataSource.objects.create(
            name="NFE FAZENDA",
            url="https://nfe.fazenda.gov.br/test",
            content_type="pdf",
        )

        self.technical_note_data = {
            "source": self.data_source,
            "title": "Nota Técnica de Teste",
            "original_url": "https://example.com/nota.pdf",
            "document_hash": "abcd1234567890",
            "publication_date": timezone.now().date(),
            "status": "pending",
            "file_size": 1024,
            "content_preview": "Conteúdo de preview da nota técnica...",
        }

    def test_create_technical_note(self):
        """Teste de criação de nota técnica."""
        note = TechnicalNote.objects.create(**self.technical_note_data)

        self.assertEqual(note.title, "Nota Técnica de Teste")
        self.assertEqual(note.status, "pending")
        self.assertEqual(note.source, self.data_source)
        self.assertIsNotNone(note.id)

    def test_document_hash_unique_constraint(self):
        """Teste da restrição de hash único."""
        TechnicalNote.objects.create(**self.technical_note_data)

        with self.assertRaises(Exception):
            TechnicalNote.objects.create(**self.technical_note_data)

    def test_technical_note_str_representation(self):
        """Teste da representação string da nota técnica."""
        note = TechnicalNote.objects.create(**self.technical_note_data)
        expected_str = f"Nota Técnica de Teste... - NFE FAZENDA"
        self.assertEqual(str(note), expected_str)


class TechnicalNoteSummarizerServiceTest(TestCase):
    """Testes para o service de sumarização."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.data_source = DataSource.objects.create(
            name="NFE FAZENDA",
            url="https://nfe.fazenda.gov.br/test",
            content_type="pdf",
        )

        self.technical_note = TechnicalNote.objects.create(
            source=self.data_source,
            title="Nota Técnica de Teste",
            original_url="https://example.com/nota.pdf",
            document_hash="unique_hash_123",
            status="pending",
            content_preview="Conteúdo suficiente para processamento de teste...",
        )

    @patch("apps.langchain_integration.services.technical_note_processor.ChatOpenAI")
    def test_get_pending_notes(self, mock_openai):
        """Teste para obter notas pendentes."""
        service = TechnicalNoteSummarizerService()
        pending_notes = service.get_pending_notes()

        self.assertEqual(len(pending_notes), 1)
        self.assertEqual(pending_notes[0].id, self.technical_note.id)

    def test_get_processing_stats(self):
        """Teste para obter estatísticas de processamento."""
        service = TechnicalNoteSummarizerService()
        stats = service.get_processing_stats()

        self.assertIn("status_counts", stats)
        self.assertIn("total_summaries", stats)
        self.assertIn("pending_count", stats)
        self.assertEqual(stats["pending_count"], 1)

    @patch("apps.langchain_integration.services.technical_note_processor.ChatOpenAI")
    def test_process_technical_note_success(self, mock_openai):
        """Teste de processamento bem-sucedido de nota técnica."""
        # Mock do LangChain
        mock_chain = Mock()
        mock_chain.invoke.return_value = {
            "summary": "Resumo de teste",
            "key_points": ["Ponto 1", "Ponto 2"],
            "changes_identified": ["Mudança 1"],
            "topics": ["Tópico 1"],
            "confidence_score": 0.95,
        }

        service = TechnicalNoteSummarizerService()

        with patch.object(service, "build_chain", return_value=mock_chain):
            with patch.object(service, "process") as mock_process:
                mock_process.return_value = {
                    "success": True,
                    "result": {
                        "summary": "Resumo de teste",
                        "key_points": ["Ponto 1", "Ponto 2"],
                        "changes_identified": ["Mudança 1"],
                        "topics": ["Tópico 1"],
                        "confidence_score": 0.95,
                    },
                }

                result = service.process_technical_note(self.technical_note)

                self.assertTrue(result["success"])
                self.assertIn("technical_note_id", result)

                # Verificar se a nota foi marcada como processada
                self.technical_note.refresh_from_db()
                self.assertEqual(self.technical_note.status, "processed")

                # Verificar se o resumo foi criado
                self.assertTrue(hasattr(self.technical_note, "summary"))
                summary = self.technical_note.summary
                self.assertEqual(summary.summary, "Resumo de teste")
                self.assertEqual(len(summary.key_points), 2)

    @patch("apps.langchain_integration.services.technical_note_processor.ChatOpenAI")
    def test_process_technical_note_already_processed(self, mock_openai):
        """Teste de processamento de nota já processada."""
        # Criar um resumo existente
        ProcessedSummary.objects.create(
            technical_note=self.technical_note,
            summary="Resumo já existente",
            model_used="gpt-4o-mini",
        )

        service = TechnicalNoteSummarizerService()
        result = service.process_technical_note(self.technical_note)

        self.assertFalse(result["success"])
        self.assertIn("já foi processada", result["error"])


class BaseFeedScraperTest(TestCase):
    """Testes para a classe base de scraping."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.data_source = DataSource.objects.create(
            name="Test Scraper Source",
            url="https://example.com/feed",
            content_type="pdf",
        )

    def test_generate_content_hash(self):
        """Teste de geração de hash de conteúdo."""

        class TestScraper(BaseFeedScraper):
            def _extract_items_from_listing(self, soup):
                return []

            def _get_content_from_item(self, item_info):
                return b"test content", "test preview"

        scraper = TestScraper(self.data_source)

        content = b"test content"
        hash_result = scraper._generate_content_hash(content)

        self.assertEqual(len(hash_result), 32)  # MD5 hash length
        self.assertIsInstance(hash_result, str)

    def test_is_duplicate(self):
        """Teste de detecção de duplicatas."""

        class TestScraper(BaseFeedScraper):
            def _extract_items_from_listing(self, soup):
                return []

            def _get_content_from_item(self, item_info):
                return b"test content", "test preview"

        scraper = TestScraper(self.data_source)

        # Criar nota técnica com hash específico
        test_hash = "test_hash_123"
        TechnicalNote.objects.create(
            source=self.data_source,
            title="Test Note",
            original_url="https://example.com/test.pdf",
            document_hash=test_hash,
            status="pending",
        )

        # Testar detecção de duplicata
        self.assertTrue(scraper._is_duplicate(test_hash))
        self.assertFalse(scraper._is_duplicate("different_hash"))

    def test_create_technical_note(self):
        """Teste de criação de nota técnica via scraper."""

        class TestScraper(BaseFeedScraper):
            def _extract_items_from_listing(self, soup):
                return []

            def _get_content_from_item(self, item_info):
                return b"test content", "test preview"

        scraper = TestScraper(self.data_source)

        note = scraper._create_technical_note(
            title="Test Note",
            original_url="https://example.com/test.pdf",
            content_hash="unique_hash",
            file_size=1024,
            content_preview="Test preview",
        )

        self.assertEqual(note.title, "Test Note")
        self.assertEqual(note.source, self.data_source)
        self.assertEqual(note.status, "pending")
        self.assertIsNotNone(note.id)


class NFEFazendaScraperTest(TestCase):
    """Testes para o scraper específico da NFE Fazenda."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.data_source = DataSource.objects.create(
            name="NFE FAZENDA",
            url="https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=",
            content_type="pdf",
        )

    def test_get_scraping_config(self):
        """Teste de obtenção de configuração do scraper."""
        scraper = NFEFazendaScraper(self.data_source)
        config = scraper.get_scraping_config()

        self.assertIn("base_url", config)
        self.assertEqual(config["content_type"], "pdf")
        self.assertIn("selectors", config)

    def test_clean_extracted_text(self):
        """Teste de limpeza de texto extraído."""
        scraper = NFEFazendaScraper(self.data_source)

        dirty_text = "Texto   com     espaços\n\n\n\nexcessivos"
        clean_text = scraper._clean_extracted_text(dirty_text)

        self.assertNotIn("   ", clean_text)  # Não deve ter múltiplos espaços
        self.assertNotIn("\n\n\n", clean_text)  # Não deve ter múltiplas quebras

    @patch("apps.langchain_integration.services.scrapers.nfe_fazenda.PyPDF2.PdfReader")
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        """Teste de extração de texto de PDF."""
        # Mock do PyPDF2
        mock_page = Mock()
        mock_page.extract_text.return_value = "Texto extraído do PDF"

        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance

        scraper = NFEFazendaScraper(self.data_source)

        pdf_content = b"fake pdf content"
        extracted_text = scraper._extract_text_from_pdf(pdf_content)

        self.assertIn("Texto extraído do PDF", extracted_text)
