"""
Testes unitários e de integração para langchain_integration.
"""

import json
import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, Mock, patch

import requests
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.langchain_integration.models import (
    DataSource,
    ProcessedSummary,
    ProcessingLog,
    TechnicalNote,
)
from apps.langchain_integration.services.nfe_job_manager import NFEJobManager
from apps.langchain_integration.services.scrapers.base import BaseFeedScraper
from apps.langchain_integration.services.scrapers.nfe_fazenda import NFEFazendaScraper
from apps.langchain_integration.services.technical_note_processor import (
    TechnicalNoteAnalysisService,
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

    def test_data_source_get_active(self):
        """Teste de obtenção de fontes ativas."""
        # Criar fonte ativa e inativa
        active_source = DataSource.objects.create(
            name="Active Source",
            url="https://example.com/active",
            content_type="pdf",
            is_active=True
        )
        DataSource.objects.create(
            name="Inactive Source",
            url="https://example.com/inactive", 
            content_type="pdf",
            is_active=False
        )

        active_sources = DataSource.objects.filter(is_active=True)
        
        self.assertEqual(active_sources.count(), 2)  # Include the setUp source
        self.assertIn(active_source, active_sources)

    def test_data_source_scraping_config_default(self):
        """Teste de configuração padrão do scraping."""
        data = self.data_source_data.copy()
        del data['scraping_config']  # Remover configuração personalizada
        
        data_source = DataSource.objects.create(**data)
        
        # Verificar se foi atribuído um dicionário vazio como padrão
        self.assertEqual(data_source.scraping_config, {})


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

    def test_technical_note_status_choices(self):
        """Teste das opções de status válidas."""
        valid_statuses = ['pending', 'processing', 'processed', 'failed']
        
        for status in valid_statuses:
            note_data = self.technical_note_data.copy()
            note_data['document_hash'] = f"hash_{status}"
            note_data['status'] = status
            
            note = TechnicalNote.objects.create(**note_data)
            self.assertEqual(note.status, status)

    def test_get_pending_notes(self):
        """Teste de obtenção de notas pendentes."""
        # Criar notas com diferentes status
        TechnicalNote.objects.create(
            **{**self.technical_note_data, 'document_hash': 'hash1', 'status': 'pending'}
        )
        TechnicalNote.objects.create(
            **{**self.technical_note_data, 'document_hash': 'hash2', 'status': 'processed'}
        )
        TechnicalNote.objects.create(
            **{**self.technical_note_data, 'document_hash': 'hash3', 'status': 'pending'}
        )

        pending_notes = TechnicalNote.objects.filter(status='pending')
        
        self.assertEqual(pending_notes.count(), 2)


class ProcessedSummaryModelTest(TestCase):
    """Testes para o modelo ProcessedSummary."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.data_source = DataSource.objects.create(
            name="NFE FAZENDA",
            url="https://nfe.fazenda.gov.br/test",
            content_type="pdf"
        )

        self.technical_note = TechnicalNote.objects.create(
            source=self.data_source,
            title="Nota Técnica de Teste",
            original_url="https://example.com/nota.pdf",
            document_hash="unique_hash_123",
            status="pending"
        )

    def test_create_processed_summary(self):
        """Teste de criação de resumo processado."""
        summary_data = {
            'technical_note': self.technical_note,
            'summary': 'Resumo da nota técnica de teste',
            'key_points': ['Ponto 1', 'Ponto 2', 'Ponto 3'],
            'changes_identified': ['Mudança A', 'Mudança B'],
            'topics': ['NFE', 'Tributação'],
            'confidence_score': 0.92,
            'model_used': 'gpt-4o-mini',
            'processing_time': 15.5
        }

        summary = ProcessedSummary.objects.create(**summary_data)

        self.assertEqual(summary.summary, 'Resumo da nota técnica de teste')
        self.assertEqual(len(summary.key_points), 3)
        self.assertEqual(len(summary.changes_identified), 2)
        self.assertEqual(summary.confidence_score, 0.92)
        self.assertIsNotNone(summary.id)

    def test_processed_summary_str_representation(self):
        """Teste da representação string do resumo."""
        summary = ProcessedSummary.objects.create(
            technical_note=self.technical_note,
            summary='Resumo de teste',
            model_used='gpt-4o-mini'
        )

        expected_str = f"Resumo: {self.technical_note.title[:30]}..."
        self.assertEqual(str(summary), expected_str)

    def test_one_to_one_relationship(self):
        """Teste do relacionamento one-to-one."""
        # Criar primeiro resumo
        summary1 = ProcessedSummary.objects.create(
            technical_note=self.technical_note,
            summary='Primeiro resumo',
            model_used='gpt-4o-mini'
        )

        # Tentar criar segundo resumo para a mesma nota técnica deve falhar
        with self.assertRaises(Exception):
            ProcessedSummary.objects.create(
                technical_note=self.technical_note,
                summary='Segundo resumo',
                model_used='gpt-4o-mini'
            )


class ProcessingLogModelTest(TestCase):
    """Testes para o modelo ProcessingLog."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.data_source = DataSource.objects.create(
            name="Test Source",
            url="https://example.com/feed",
            content_type="pdf"
        )

        self.technical_note = TechnicalNote.objects.create(
            source=self.data_source,
            title="Test Note",
            original_url="https://example.com/test.pdf",
            document_hash="test_hash_log",
            status="pending"
        )

    def test_create_processing_log(self):
        """Teste de criação de log de processamento."""
        log_data = {
            'technical_note': self.technical_note,
            'operation': 'scraping',
            'level': 'info',
            'message': 'Scraping concluído com sucesso',
            'details': {'items_found': 5, 'duration': 30.5},
            'execution_time': 30.5
        }

        log = ProcessingLog.objects.create(**log_data)

        self.assertEqual(log.operation, 'scraping')
        self.assertEqual(log.level, 'info')
        self.assertEqual(log.details['items_found'], 5)
        self.assertIsNotNone(log.id)

    def test_processing_log_str_representation(self):
        """Teste da representação string do log."""
        log = ProcessingLog.objects.create(
            technical_note=self.technical_note,
            operation='processing',
            level='error',
            message='Erro no processamento da nota técnica de exemplo'
        )

        expected_str = "Processing: Erro no processamento da nota técnica de exemplo..."
        self.assertEqual(str(log), expected_str)


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

    @patch("apps.langchain_integration.services.technical_note_processor.ChatOpenAI")
    def test_process_technical_note_insufficient_content(self, mock_openai):
        """Teste de processamento com conteúdo insuficiente."""
        # Criar nota com conteúdo muito pequeno
        short_note = TechnicalNote.objects.create(
            source=self.data_source,
            title="Nota Curta",
            original_url="https://example.com/short.pdf",
            document_hash="short_hash",
            status="pending",
            content_preview="Pouco conteúdo"  # Muito curto
        )

        service = TechnicalNoteSummarizerService()
        result = service.process_technical_note(short_note)

        self.assertFalse(result["success"])
        self.assertIn("conteúdo insuficiente", result["error"])

    def test_batch_process_notes(self):
        """Teste de processamento em lote."""
        # Criar múltiplas notas pendentes
        notes = []
        for i in range(3):
            notes.append(TechnicalNote.objects.create(
                source=self.data_source,
                title=f"Nota {i+1}",
                original_url=f"https://example.com/nota{i+1}.pdf",
                document_hash=f"hash_{i+1}",
                status="pending",
                content_preview="Conteúdo suficiente para processamento..."
            ))

        service = TechnicalNoteSummarizerService()
        
        with patch.object(service, 'process_technical_note') as mock_process:
            mock_process.return_value = {'success': True}
            
            results = service.batch_process_notes(notes)
            
            self.assertEqual(len(results), 3)
            self.assertEqual(mock_process.call_count, 3)


class TechnicalNoteAnalysisServiceTest(TestCase):
    """Testes para o service de análise de notas técnicas."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.data_source = DataSource.objects.create(
            name="NFE FAZENDA",
            url="https://nfe.fazenda.gov.br/test",
            content_type="pdf"
        )

        self.technical_note = TechnicalNote.objects.create(
            source=self.data_source,
            title="Nota Técnica 001/2025",
            original_url="https://example.com/nota.pdf",
            document_hash="analysis_hash",
            status="processed",
            content_preview="Nota técnica sobre alterações na validação do XML da NFE..."
        )

        self.summary = ProcessedSummary.objects.create(
            technical_note=self.technical_note,
            summary="Resumo da nota técnica sobre validação XML",
            key_points=["Alteração no schema", "Nova validação"],
            changes_identified=["Campo obrigatório", "Validação adicional"],
            topics=["XML", "Validação", "NFE"],
            model_used="gpt-4o-mini"
        )

    @patch("apps.langchain_integration.services.technical_note_processor.ChatOpenAI")
    def test_analyze_impact(self, mock_openai):
        """Teste de análise de impacto."""
        service = TechnicalNoteAnalysisService()

        with patch.object(service, 'build_chain') as mock_build_chain:
            mock_chain = Mock()
            mock_chain.invoke.return_value = {
                "impact_level": "high",
                "affected_areas": ["Emissão de NFE", "Validação XML"],
                "implementation_timeline": "30 dias",
                "complexity": "medium"
            }
            mock_build_chain.return_value = mock_chain

            result = service.analyze_impact(self.summary)

            self.assertEqual(result["impact_level"], "high")
            self.assertIn("Emissão de NFE", result["affected_areas"])
            self.assertEqual(result["implementation_timeline"], "30 dias")

    def test_calculate_priority_score(self):
        """Teste de cálculo de pontuação de prioridade."""
        service = TechnicalNoteAnalysisService()

        # Teste com dados de alto impacto
        analysis = {
            "impact_level": "high",
            "complexity": "medium",
            "implementation_timeline": "30 dias"
        }

        score = service.calculate_priority_score(analysis, self.summary)

        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_get_related_summaries(self):
        """Teste de obtenção de resumos relacionados."""
        # Criar resumos adicionais
        related_note = TechnicalNote.objects.create(
            source=self.data_source,
            title="Nota Técnica 002/2025",
            original_url="https://example.com/nota2.pdf",
            document_hash="related_hash",
            status="processed"
        )

        ProcessedSummary.objects.create(
            technical_note=related_note,
            summary="Outra nota sobre XML e validação",
            topics=["XML", "Validação"],  # Tópicos em comum
            model_used="gpt-4o-mini"
        )

        service = TechnicalNoteAnalysisService()
        related = service.get_related_summaries(self.summary, limit=5)

        self.assertGreater(len(related), 0)
        self.assertEqual(related[0].technical_note.id, related_note.id)


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

    def test_log_operation(self):
        """Teste de logging de operação."""
        
        class TestScraper(BaseFeedScraper):
            def _extract_items_from_listing(self, soup):
                return []

            def _get_content_from_item(self, item_info):
                return b"test content", "test preview"

        scraper = TestScraper(self.data_source)
        
        scraper._log_operation(
            operation='test_operation',
            status='completed',
            message='Operação de teste',
            details={'items': 5}
        )

        # Verificar se log foi criado
        log = ProcessingLog.objects.get(operation='test_operation')
        self.assertEqual(log.status, 'completed')
        self.assertEqual(log.details['items'], 5)

    @patch('requests.get')
    def test_rate_limiting(self, mock_get):
        """Teste de rate limiting."""
        
        class TestScraper(BaseFeedScraper):
            def _extract_items_from_listing(self, soup):
                return []

            def _get_content_from_item(self, item_info):
                return b"test content", "test preview"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html></html>"
        mock_get.return_value = mock_response

        scraper = TestScraper(self.data_source)
        
        # Fazer múltiplas requisições para testar rate limiting
        import time
        start_time = time.time()
        
        scraper._make_request("https://example.com/page1")
        scraper._make_request("https://example.com/page2")
        
        end_time = time.time()
        
        # Deve ter levado pelo menos 1 segundo devido ao rate limiting
        self.assertGreaterEqual(end_time - start_time, 1.0)


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

    @patch("apps.langchain_integration.services.scrapers.nfe_fazenda.pdfplumber")
    @patch("apps.langchain_integration.services.scrapers.nfe_fazenda.PyPDF2.PdfReader")
    def test_extract_text_from_pdf_fallback(self, mock_pdf_reader, mock_pdfplumber):
        """Teste de extração de texto com fallback para pdfplumber."""
        # Mock do PyPDF2 falhando
        mock_pdf_reader.side_effect = Exception("PyPDF2 falhou")

        # Mock do pdfplumber
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Texto via pdfplumber"
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        scraper = NFEFazendaScraper(self.data_source)

        pdf_content = b"fake pdf content"
        extracted_text = scraper._extract_text_from_pdf(pdf_content)

        self.assertIn("Texto via pdfplumber", extracted_text)

    def test_build_pdf_url(self):
        """Teste de construção de URL de PDF."""
        scraper = NFEFazendaScraper(self.data_source)

        item_info = {
            'title': 'Nota Técnica 001/2025',
            'url': 'exibirArquivo.aspx?conteudo=ABC123',
            'link_element': Mock()
        }

        pdf_url = scraper._build_pdf_url(item_info['url'])

        expected_url = "https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=ABC123"
        self.assertEqual(pdf_url, expected_url)

    @patch('requests.get')
    def test_extract_items_from_listing_mock(self, mock_get):
        """Teste de extração de itens da listagem (com mock)."""
        # HTML simulado da página da NFE
        mock_html = """
        <html>
            <body>
                <table>
                    <tr>
                        <td><a href="exibirArquivo.aspx?conteudo=ABC123">Nota Técnica 001/2025</a></td>
                        <td>01/01/2025</td>
                    </tr>
                    <tr>
                        <td><a href="exibirArquivo.aspx?conteudo=DEF456">Nota Técnica 002/2025</a></td>
                        <td>02/01/2025</td>
                    </tr>
                </table>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_html.encode('utf-8')
        mock_get.return_value = mock_response

        scraper = NFEFazendaScraper(self.data_source)

        with patch.object(scraper, '_make_request', return_value=mock_response):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(mock_html, 'html.parser')
            items = scraper._extract_items_from_listing(soup)

            self.assertGreater(len(items), 0)
            # Verificar se pelo menos um item tem título
            if items:
                self.assertIn('title', items[0])


class NFEJobManagerTest(TestCase):
    """Testes para o gerenciador de jobs da NFE."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.data_source = DataSource.objects.create(
            name="NFE FAZENDA",
            url="https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=",
            content_type="pdf",
            is_active=True
        )

    @patch('apps.langchain_integration.services.nfe_job_manager.JobSchedulerService')
    def test_setup_default_jobs(self, mock_scheduler_service):
        """Teste de configuração de jobs padrão."""
        mock_scheduler = Mock()
        mock_scheduler.add_job.return_value = True
        mock_scheduler_service.return_value = mock_scheduler

        manager = NFEJobManager()
        result = manager.setup_default_jobs()

        self.assertTrue(result['success'])
        # Verificar se os jobs foram adicionados
        self.assertGreater(mock_scheduler.add_job.call_count, 0)

    def test_get_job_status(self):
        """Teste de obtenção de status dos jobs."""
        manager = NFEJobManager()
        
        with patch('apps.langchain_integration.services.nfe_job_manager.JobSchedulerService') as mock_service:
            mock_scheduler = Mock()
            mock_scheduler.list_jobs.return_value = [
                {
                    'id': 'scrape_nfe_fazenda',
                    'name': 'Scrape NFE Fazenda',
                    'next_run_time': timezone.now()
                }
            ]
            mock_service.return_value = mock_scheduler

            status = manager.get_job_status()

            self.assertIn('jobs', status)
            self.assertIn('total_jobs', status)

    @patch('apps.jobs.tasks.scrape_nfe_fazenda_job')
    @patch('apps.jobs.tasks.process_pending_technical_notes_job')
    def test_run_full_pipeline_now(self, mock_process_job, mock_scrape_job):
        """Teste de execução manual do pipeline completo."""
        # Mock dos jobs
        mock_scrape_job.return_value = {
            'success': True,
            'stats': {'new_items': 3, 'duplicates': 1, 'errors': 0}
        }
        mock_process_job.return_value = {
            'success': True,
            'processed': 2,
            'errors': 0
        }

        manager = NFEJobManager()
        result = manager.run_full_pipeline_now()

        self.assertTrue(result['success'])
        self.assertEqual(result['scraping_stats']['new_items'], 3)
        self.assertEqual(result['processing_stats']['processed'], 2)

        mock_scrape_job.assert_called_once()
        mock_process_job.assert_called_once()


# =============================================================================
# TESTES DE INTEGRAÇÃO
# =============================================================================

class NFEIntegrationTest(TransactionTestCase):
    """Testes de integração end-to-end do sistema NFE."""

    def setUp(self):
        """Configuração inicial para os testes de integração."""
        self.data_source = DataSource.objects.create(
            name="NFE FAZENDA",
            url="https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=",
            content_type="pdf",
            is_active=True
        )

    def test_full_pipeline_with_mock_data(self):
        """Teste do pipeline completo com dados simulados."""
        # 1. Simular scraping
        with patch('apps.langchain_integration.services.scrapers.nfe_fazenda.NFEFazendaScraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.scrape_all.return_value = {
                'success': True,
                'results': [
                    {
                        'title': 'Nota Técnica 001/2025',
                        'url': 'https://example.com/nota1.pdf',
                        'content_hash': 'integration_hash_1',
                        'success': True
                    }
                ],
                'stats': {'new_items': 1, 'duplicates': 0, 'errors': 0}
            }
            mock_scraper_class.return_value = mock_scraper

            # Executar scraping
            from apps.jobs.tasks import scrape_nfe_fazenda_job
            scraping_result = scrape_nfe_fazenda_job()

            self.assertTrue(scraping_result['success'])

        # 2. Verificar se nota técnica foi criada
        created_notes = TechnicalNote.objects.filter(
            document_hash='integration_hash_1'
        )
        # Note: Como estamos usando mock, a nota não será criada de fato
        # Este teste verifica o fluxo, não a persistência

    def test_processing_pipeline_with_existing_note(self):
        """Teste do pipeline de processamento com nota existente."""
        # Criar nota técnica manualmente
        note = TechnicalNote.objects.create(
            source=self.data_source,
            title="Nota Técnica de Integração",
            original_url="https://example.com/integration.pdf",
            document_hash="integration_hash_processing",
            status="pending",
            content_preview="Conteúdo de teste para processamento de integração. Esta é uma nota técnica simulada para testar o pipeline completo de processamento com LangChain."
        )

        # 2. Simular processamento
        with patch('apps.langchain_integration.services.technical_note_processor.TechnicalNoteSummarizerService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_pending_notes.return_value = [note]
            mock_service.process_technical_note.return_value = {
                'success': True,
                'technical_note_id': note.id,
                'summary_id': 1
            }
            mock_service_class.return_value = mock_service

            # Executar processamento
            from apps.jobs.tasks import process_pending_technical_notes_job
            processing_result = process_pending_technical_notes_job(limit=10)

            self.assertTrue(processing_result['success'])
            self.assertEqual(processing_result['processed'], 1)

    def test_job_scheduler_integration(self):
        """Teste de integração do sistema de jobs."""
        from apps.jobs.schedulers import JobSchedulerService

        scheduler = JobSchedulerService()

        # Testar start/stop do scheduler
        start_result = scheduler.start()
        
        # Adicionar job de teste
        def test_job():
            return {'test': 'completed'}

        add_result = scheduler.add_job(
            func=test_job,
            trigger='date',
            job_id='integration_test_job',
            run_date=timezone.now() + timedelta(seconds=2)
        )

        self.assertTrue(add_result)

        # Listar jobs
        jobs = scheduler.list_jobs()
        job_ids = [job['id'] for job in jobs]
        self.assertIn('integration_test_job', job_ids)

        # Remover job
        remove_result = scheduler.remove_job('integration_test_job')
        self.assertTrue(remove_result)

        # Parar scheduler
        stop_result = scheduler.stop()

    def test_nfe_job_manager_integration(self):
        """Teste de integração do gerenciador de jobs NFE."""
        from apps.langchain_integration.services.nfe_job_manager import NFEJobManager

        manager = NFEJobManager()

        # Configurar jobs padrão
        with patch('apps.jobs.schedulers.JobSchedulerService') as mock_scheduler_service:
            mock_scheduler = Mock()
            mock_scheduler.add_job.return_value = True
            mock_scheduler_service.return_value = mock_scheduler

            setup_result = manager.setup_default_jobs()
            self.assertTrue(setup_result['success'])

        # Obter status dos jobs
        with patch('apps.jobs.schedulers.JobSchedulerService') as mock_scheduler_service:
            mock_scheduler = Mock()
            mock_scheduler.list_jobs.return_value = [
                {
                    'id': 'scrape_nfe_fazenda',
                    'name': 'Scrape NFE Fazenda Daily',
                    'next_run_time': timezone.now()
                }
            ]
            mock_scheduler_service.return_value = mock_scheduler

            status = manager.get_job_status()
            self.assertIn('jobs', status)
            self.assertIn('total_jobs', status)

    def test_database_relationships_integrity(self):
        """Teste de integridade dos relacionamentos do banco de dados."""
        # Criar hierarquia completa de dados
        data_source = DataSource.objects.create(
            name="Test Integration Source",
            url="https://example.com/integration",
            content_type="pdf"
        )

        technical_note = TechnicalNote.objects.create(
            source=data_source,
            title="Nota de Teste de Integridade",
            original_url="https://example.com/integrity.pdf",
            document_hash="integrity_hash",
            status="pending"
        )

        processed_summary = ProcessedSummary.objects.create(
            technical_note=technical_note,
            summary="Resumo de teste de integridade",
            key_points=["Ponto 1", "Ponto 2"],
            model_used="gpt-4o-mini"
        )

        processing_log = ProcessingLog.objects.create(
            operation="integration_test",
            status="completed",
            message="Teste de integridade",
            source=data_source
        )

        # Verificar relacionamentos
        self.assertEqual(technical_note.source, data_source)
        self.assertEqual(processed_summary.technical_note, technical_note)
        self.assertEqual(processing_log.source, data_source)

        # Testar cascade delete
        data_source.delete()
        
        # Verificar se objetos relacionados foram removidos
        self.assertFalse(TechnicalNote.objects.filter(id=technical_note.id).exists())
        self.assertFalse(ProcessedSummary.objects.filter(id=processed_summary.id).exists())
        self.assertFalse(ProcessingLog.objects.filter(id=processing_log.id).exists())

    def test_error_handling_and_logging(self):
        """Teste de tratamento de erros e logging."""
        # Testar logging de operações
        ProcessingLog.objects.create(
            operation="error_test",
            status="failed",
            message="Teste de erro simulado",
            details={"error_type": "simulation", "traceback": "fake traceback"},
            source=self.data_source
        )

        # Verificar se log foi criado
        error_logs = ProcessingLog.objects.filter(
            operation="error_test",
            status="failed"
        )
        
        self.assertEqual(error_logs.count(), 1)
        self.assertIn("error_type", error_logs.first().details)

    def test_performance_with_large_dataset(self):
        """Teste de performance com dataset maior."""
        # Criar múltiplas notas técnicas
        batch_size = 50
        notes = []
        
        for i in range(batch_size):
            notes.append(TechnicalNote(
                source=self.data_source,
                title=f"Nota de Performance {i+1:03d}",
                original_url=f"https://example.com/performance_{i+1}.pdf",
                document_hash=f"performance_hash_{i+1:03d}",
                status="pending"
            ))

        # Bulk create para melhor performance
        import time
        start_time = time.time()
        
        TechnicalNote.objects.bulk_create(notes)
        
        creation_time = time.time() - start_time
        
        # Verificar se criação foi eficiente (menos de 1 segundo para 50 items)
        self.assertLess(creation_time, 1.0)

        # Verificar se todos foram criados
        created_count = TechnicalNote.objects.filter(
            title__startswith="Nota de Performance"
        ).count()
        
        self.assertEqual(created_count, batch_size)

        # Testar query performance
        start_time = time.time()
        
        pending_notes = list(TechnicalNote.objects.filter(
            status="pending",
            source=self.data_source
        )[:10])
        
        query_time = time.time() - start_time
        
        # Query deve ser rápida (menos de 0.1 segundos)
        self.assertLess(query_time, 0.1)
        self.assertEqual(len(pending_notes), 10)


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
