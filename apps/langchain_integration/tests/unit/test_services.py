"""
Testes unitários para os serviços do langchain_integration.
"""

from unittest.mock import Mock, patch

from bs4 import BeautifulSoup
from django.test import tag

from tests.base import BaseUnitTestCase, LangChainTestCase
from tests.mocks.factories import (
    DataSourceFactory,
    ProcessedSummaryFactory,
    TechnicalNoteFactory,
)

from apps.langchain_integration.services.scrapers.nfe_fazenda import NFEFazendaScraper
from apps.langchain_integration.services.technical_note_processor import (
    TechnicalNoteAnalysisService,
    TechnicalNoteSummarizerService,
)


@tag("unit", "services", "fast")
class NFEFazendaScraperTest(BaseUnitTestCase):
    """Testes unitários para o scraper NFE Fazenda."""

    def setUp(self):
        super().setUp()
        self.data_source = DataSourceFactory(
            name="NFE FAZENDA",
            url="https://www.nfe.fazenda.gov.br/test",
            content_type="pdf",
            is_active=True,
            scraping_config={
                "selectors": {
                    "file_links": "a[href*='exibirArquivo.aspx']",
                    "fallback_links": "a[href*='conteudo=']",
                }
            },
        )

    @patch("requests.Session.get")
    def test_extract_links_success(self, mock_get):
        """Teste de extração de links com sucesso."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <table>
                    <tr>
                        <td><a href="/exibirArquivo.aspx?conteudo=1">Nota Técnica 1</a></td>
                        <td>20/01/2025</td>
                    </tr>
                    <tr>
                        <td><a href="/exibirArquivo.aspx?conteudo=2">Nota Técnica 2</a></td>
                        <td>21/01/2025</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        scraper = NFEFazendaScraper(self.data_source)

        # Act
        soup = BeautifulSoup(mock_response.text, "html.parser")
        items = scraper._extract_items_from_listing(soup)

        # Assert
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)
        self.assertIn("title", items[0])
        self.assertIn("url", items[0])

    @patch("requests.Session.get")
    def test_extract_links_request_failure(self, mock_get):
        """Teste de falha na requisição."""
        # Arrange
        mock_get.side_effect = Exception("Network error")
        scraper = NFEFazendaScraper(self.data_source)

        # Act & Assert
        with self.assertRaises(Exception):
            scraper._make_request("https://example.com")

    def test_parse_technical_note_title(self):
        """Teste de parsing do título da nota técnica."""
        # Arrange
        scraper = NFEFazendaScraper(self.data_source)
        soup = BeautifulSoup(
            '<a href="test.pdf">Nota Técnica 001/2025 - Alterações no XML da NFE</a>',
            "html.parser",
        )
        link = soup.find("a")

        # Act
        title = scraper._extract_title_from_link(link, soup)

        # Assert
        self.assertIn("Nota Técnica", title)
        self.assertIn("001/2025", title)

    def test_generate_content_hash(self):
        """Teste de geração de hash do conteúdo."""
        # Arrange
        scraper = NFEFazendaScraper(self.data_source)
        content = "Conteúdo de teste para hash"

        # Act
        hash1 = scraper._generate_content_hash(content)
        hash2 = scraper._generate_content_hash(content)
        hash3 = scraper._generate_content_hash("Conteúdo diferente")

        # Assert
        self.assertEqual(hash1, hash2)  # Mesmo conteúdo, mesmo hash
        self.assertNotEqual(hash1, hash3)  # Conteúdo diferente, hash diferente
        self.assertIsInstance(hash1, str)


@tag("unit", "services", "fast")
class TechnicalNoteSummarizerServiceTest(LangChainTestCase):
    """Testes unitários para o serviço de sumarização."""

    def setUp(self):
        super().setUp()
        self.technical_note = TechnicalNoteFactory(
            title="Nota Técnica de Teste",
            content="Conteúdo detalhado sobre alterações na NFE...",
        )

    def test_process_technical_note_success(self):
        """Teste de processamento bem-sucedido."""
        # Arrange
        service = TechnicalNoteSummarizerService()

        with patch.object(service, "build_chain") as mock_build_chain:
            mock_chain = Mock()
            mock_chain.invoke.return_value = {
                "summary": "Resumo da nota técnica",
                "key_points": ["Ponto 1", "Ponto 2"],
                "topics": ["NFE", "XML"],
            }
            mock_build_chain.return_value = mock_chain

            # Act
            result = service.process_technical_note(self.technical_note)

            # Assert
            self.assertTrue(result["success"])
            self.assertIn("summary", result)
            self.assertIn("key_points", result)

    def test_process_technical_note_insufficient_content(self):
        """Teste com conteúdo insuficiente."""
        # Arrange
        short_note = TechnicalNoteFactory(content="Muito pouco conteúdo")
        service = TechnicalNoteSummarizerService()

        # Act
        result = service.process_technical_note(short_note)

        # Assert
        self.assertFalse(result["success"])
        self.assertIn("conteúdo insuficiente", result["error"])

    def test_batch_process_notes(self):
        """Teste de processamento em lote."""
        # Arrange
        notes = [TechnicalNoteFactory() for _ in range(3)]
        service = TechnicalNoteSummarizerService()

        with patch.object(service, "process_technical_note") as mock_process:
            mock_process.return_value = {"success": True}

            # Act
            results = service.batch_process_notes(notes)

            # Assert
            self.assertEqual(len(results), 3)
            self.assertEqual(mock_process.call_count, 3)

    def test_get_pending_notes(self):
        """Teste de obtenção de notas pendentes."""
        # Arrange
        TechnicalNoteFactory()  # Nota normal
        service = TechnicalNoteSummarizerService()

        # Act
        pending_notes = service.get_pending_notes(limit=5)

        # Assert
        self.assertIsInstance(pending_notes, list)


@tag("unit", "services", "fast")
class TechnicalNoteAnalysisServiceTest(LangChainTestCase):
    """Testes unitários para o serviço de análise."""

    def setUp(self):
        super().setUp()
        self.technical_note = TechnicalNoteFactory()
        self.summary = ProcessedSummaryFactory(technical_note=self.technical_note)

    def test_analyze_impact(self):
        """Teste de análise de impacto."""
        # Arrange
        service = TechnicalNoteAnalysisService()

        with patch.object(service, "build_chain") as mock_build_chain:
            mock_chain = Mock()
            mock_chain.invoke.return_value = {
                "impact_level": "high",
                "affected_areas": ["Emissão de NFE", "Validação XML"],
                "implementation_timeline": "30 dias",
                "complexity": "medium",
            }
            mock_build_chain.return_value = mock_chain

            # Act
            result = service.analyze_impact(self.summary)

            # Assert
            self.assertEqual(result["impact_level"], "high")
            self.assertIn("Emissão de NFE", result["affected_areas"])
            self.assertEqual(result["implementation_timeline"], "30 dias")

    def test_calculate_priority_score(self):
        """Teste de cálculo de pontuação de prioridade."""
        # Arrange
        service = TechnicalNoteAnalysisService()
        analysis = {
            "impact_level": "high",
            "complexity": "medium",
            "implementation_timeline": "30 dias",
        }

        # Act
        score = service.calculate_priority_score(analysis, self.summary)

        # Assert
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_get_related_summaries(self):
        """Teste de obtenção de sumários relacionados."""
        # Arrange
        service = TechnicalNoteAnalysisService()

        # Create some related summaries
        ProcessedSummaryFactory(
            technical_note=TechnicalNoteFactory(), topics=["NFE", "XML"]
        )
        ProcessedSummaryFactory(
            technical_note=TechnicalNoteFactory(), topics=["Validação", "Schema"]
        )

        # Act
        related = service.get_related_summaries(self.summary, limit=5)

        # Assert
        self.assertIsInstance(related, list)

    def test_chain_building(self):
        """Teste de construção da chain."""
        # Arrange
        service = TechnicalNoteAnalysisService()

        # Act
        chain = service.build_chain()

        # Assert
        self.assertIsNotNone(chain)
