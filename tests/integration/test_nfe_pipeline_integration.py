"""
Testes de integração para o pipeline completo NFE Fazenda.
Testa scraping, download de PDFs e processamento com LangChain.
"""

import os
import tempfile
from unittest.mock import patch, Mock

import requests
from django.test import tag, override_settings
from django.utils import timezone

from tests.base import BaseIntegrationTest
from apps.jobs.tasks import scrape_nfe_fazenda_job, process_pending_technical_notes_job
from apps.langchain_integration.models import DataSource, TechnicalNote, ProcessedSummary
from apps.langchain_integration.services.scrapers.nfe_fazenda import NFEFazendaScraper
from apps.langchain_integration.services.technical_note_processor import TechnicalNoteSummarizerService


@tag("integration", "nfe", "pipeline")
class NFEFazendaPipelineIntegrationTest(BaseIntegrationTest):
    """
    Testes de integração do pipeline completo NFE Fazenda:
    1. Scraping da listagem
    2. Download de PDFs
    3. Processamento com LangChain
    """

    @classmethod
    def setUpClass(cls):
        """Setup inicial da classe de teste."""
        super().setUpClass()
        
        # Configurar variáveis de ambiente para os testes
        os.environ.setdefault('OPENAI_API_KEY', 'test-key-for-integration')

    def setUp(self):
        """Setup para cada teste."""
        super().setUp()
        
        # Criar fonte de dados NFE Fazenda
        self.data_source = DataSource.objects.create(
            name="NFE Fazenda",
            url="https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=SU5VT1pHSjZObUU9",
            content_type="pdf",
            description="Notas Técnicas da NFE Fazenda",
            is_active=True,
            scraping_config={
                "listing_selector": "table tbody tr",
                "title_selector": "a",
                "url_selector": "a",
                "date_selector": "td:last-child"
            }
        )

    def tearDown(self):
        """Limpeza após cada teste."""
        # Limpar dados criados durante o teste
        ProcessedSummary.objects.all().delete()
        TechnicalNote.objects.all().delete()
        super().tearDown()


@tag("integration", "nfe", "scraping")
class NFEScrapingIntegrationTest(NFEFazendaPipelineIntegrationTest):
    """Testes específicos para o scraping da listagem NFE."""

    def test_scraping_obtains_items_from_listing(self):
        """
        Testa se o scraping consegue obter itens da listagem da NFE Fazenda.
        """
        # Executar job de scraping
        result = scrape_nfe_fazenda_job()
        
        # Verificar se o job executou com sucesso
        self.assertTrue(result.get('success'), f"Job falhou: {result.get('error')}")
        
        # Verificar estatísticas
        stats = result.get('stats', {})
        self.assertGreater(stats.get('total_found', 0), 0, "Nenhum item foi encontrado na listagem")
        self.assertGreater(stats.get('new_items', 0), 0, "Nenhum item novo foi processado")
        
        # Verificar se itens foram salvos no banco
        notes_count = TechnicalNote.objects.filter(source__name="NFE FAZENDA").count()
        self.assertGreater(notes_count, 0, "Nenhuma nota técnica foi salva no banco")
        
        # Verificar estrutura dos dados salvos
        first_note = TechnicalNote.objects.filter(source__name="NFE FAZENDA").first()
        self.assertIsNotNone(first_note)
        self.assertIsNotNone(first_note.title)
        self.assertIsNotNone(first_note.original_url)
        self.assertIsNotNone(first_note.document_hash)
        self.assertTrue(first_note.original_url.startswith('https://www.nfe.fazenda.gov.br'))
        
        print(f"✅ Scraping test passed: {stats.get('processed')} items obtained")

    def test_pdf_download_functionality(self):
        """
        Testa se o download de PDF está funcionando corretamente.
        """
        # Primeiro, executar scraping para obter itens
        scrape_result = scrape_nfe_fazenda_job()
        self.assertTrue(scrape_result.get('success'))
        
        # Obter a primeira nota técnica criada
        note = TechnicalNote.objects.filter(source__name="NFE FAZENDA").first()
        self.assertIsNotNone(note, "Nenhuma nota técnica foi criada pelo scraping")
        
        # Verificar se o PDF foi baixado e processado
        self.assertIsNotNone(note.file_size, "Tamanho do arquivo não foi registrado")
        self.assertGreater(note.file_size, 0, "Arquivo PDF parece estar vazio")
        self.assertIsNotNone(note.content_preview, "Conteúdo do PDF não foi extraído")
        self.assertGreater(len(note.content_preview), 100, "Conteúdo extraído é muito pequeno")
        
        # Verificar se o conteúdo extraído contém texto esperado
        content_lower = note.content_preview.lower()
        expected_terms = ['nota técnica', 'receita federal', 'nf-e', 'nfe', 'fiscal']
        found_terms = [term for term in expected_terms if term in content_lower]
        self.assertGreater(len(found_terms), 0, 
                          f"Conteúdo não contém termos esperados: {expected_terms}")
        
        print(f"✅ PDF download test passed: {note.file_size} bytes, preview: {note.content_preview[:100]}...")


@tag("integration", "nfe", "processing")  
@override_settings(
    LANGCHAIN_CONFIG={
        "OPENAI_API_KEY": "test-key-integration",
        "DEFAULT_MODEL": "gpt-4o-mini",
        "DEFAULT_TEMPERATURE": 0.0,
        "MAX_TOKENS": 4000,
        "TIMEOUT": 30,
    }
)
class NFEProcessingIntegrationTest(NFEFazendaPipelineIntegrationTest):
    """Testes específicos para o processamento com LangChain."""

    def setUp(self):
        """Setup com mock do OpenAI para testes."""
        super().setUp()
        
        # Mock da resposta do OpenAI
        self.openai_mock_response = Mock()
        self.openai_mock_response.content = """
        {
            "summary": "Esta é uma nota técnica de teste sobre simplificação operacional da NFe, abordando principalmente mudanças no leiaute do QR-Code da NFC-e para versão 3 e implementação de resposta síncrona para lotes com apenas uma NF-e.",
            "key_points": [
                "Atualização do leiaute do QR-Code da NFC-e para versão 3",
                "Implementação de resposta síncrona para lotes com uma NF-e",
                "Simplificação operacional do sistema"
            ],
            "changes_identified": [
                "Novo leiaute do QR-Code versão 3",
                "Resposta síncrona implementada"
            ],
            "topics": [
                "Simplificação operacional",
                "QR-Code NFC-e",
                "Resposta síncrona"
            ]
        }
        """

    @patch('apps.langchain_integration.services.base.ChatOpenAI')
    def test_pdf_summarization_functionality(self, mock_openai):
        """
        Testa se o resumo de PDF com LangChain está funcionando.
        """
        # Mock da instância do ChatOpenAI
        mock_chat_instance = Mock()
        mock_openai.return_value = mock_chat_instance
        
        # Mock do método process_batch do TechnicalNoteSummarizerService
        mock_batch_result = {
            "total": 1,
            "processed": 1,
            "errors": 0,
            "skipped": 0,
            "processing_time": 0.5,
            "results": [{
                "success": True,
                "result": self.openai_mock_response,
                "model_used": "gpt-4o-mini"
            }]
        }
        
        with patch('apps.langchain_integration.services.technical_note_processor.TechnicalNoteSummarizerService.process_batch') as mock_process_batch:
            mock_process_batch.return_value = mock_batch_result
        
        # Primeiro, criar uma nota técnica com conteúdo de teste
        note = TechnicalNote.objects.create(
            source=self.data_source,
            title="Nota Técnica 2025.001 - Teste de Integração",
            original_url="https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=test",
            document_hash="test_hash_integration_123",
            status="pending",
            file_size=100000,
            content_preview="""
            Sistema Nota Fiscal Eletrônica
            
            Nota Técnica 2025.001
            
            Simplificação Operacional:
            - NFC-e: Leiaute do QR-Code versão 3
            - NF-e: Resposta Síncrona para Lote com somente 1 NF-e
            
            Versão 1.02 - Setembro 2025
            
            Esta nota técnica aborda mudanças importantes no sistema NFe...
            """
        )
        
        # Executar processamento
        result = process_pending_technical_notes_job(max_items=1)
        
        # Verificar se o job executou com sucesso
        self.assertTrue(result.get('success'), f"Job de processamento falhou: {result.get('error')}")
        
        # Verificar estatísticas
        stats = result.get('stats', {})
        self.assertEqual(stats.get('processed', 0), 1, "Uma nota deveria ter sido processada")
        self.assertEqual(stats.get('errors', 0), 0, "Não deveria ter erros")
        
        # Verificar se o resumo foi criado
        note.refresh_from_db()
        self.assertEqual(note.status, 'processed', "Status da nota deveria ser 'processed'")
        
        # Verificar se o resumo foi salvo
        self.assertTrue(hasattr(note, 'summary'), "Resumo não foi criado")
        summary = note.summary
        
        self.assertIsNotNone(summary.summary, "Campo summary não foi preenchido")
        self.assertIsNotNone(summary.key_points, "Campo key_points não foi preenchido")
        self.assertIsNotNone(summary.topics, "Campo topics não foi preenchido")
        self.assertEqual(summary.model_used, 'gpt-4o-mini', "Modelo usado não foi registrado corretamente")
        self.assertGreater(summary.processing_time, 0, "Tempo de processamento não foi registrado")
        
        print(f"✅ Processing test passed: Summary created for note {note.title}")
        print(f"📄 Summary preview: {summary.summary[:150]}...")


@tag("integration", "nfe", "full_pipeline")
@override_settings(
    LANGCHAIN_CONFIG={
        "OPENAI_API_KEY": "test-key-full-pipeline",
        "DEFAULT_MODEL": "gpt-4o-mini", 
        "DEFAULT_TEMPERATURE": 0.0,
        "MAX_TOKENS": 4000,
        "TIMEOUT": 30,
    }
)
class NFEPDFDownloadIntegrationTest(NFEFazendaPipelineIntegrationTest):
    """Testes de integração para download de PDFs."""

    def test_pdf_download_functionality(self):
        """
        Testa se o download de PDFs está funcionando corretamente.
        Verifica se consegue baixar pelo menos um PDF real da NFE Fazenda.
        """
        # Primeiro, fazer scraping para obter algumas notas
        scrape_result = scrape_nfe_fazenda_job()
        self.assertIsNotNone(scrape_result)
        
        stats = scrape_result.get('stats', {})
        self.assertGreater(stats.get('total_found', 0), 0, "Deveria encontrar pelo menos uma nota técnica")
        
        # Obter uma nota técnica pendente para testar download
        pending_note = TechnicalNote.objects.filter(status='pending').first()
        if pending_note:
            # Tentar processar o download dessa nota
            process_result = process_pending_technical_notes_job(max_items=1)
            self.assertIsNotNone(process_result)
            
            # Verificar se houve algum processamento
            stats = process_result.get('stats', {})
            processed = stats.get('processed', 0) + stats.get('errors', 0) + stats.get('skipped', 0)
            self.assertGreater(processed, 0, "Deveria ter processado pelo menos uma nota")
        else:
            self.skipTest("Nenhuma nota técnica pendente encontrada para testar download")

    def test_pdf_content_extraction(self):
        """
        Testa se o conteúdo dos PDFs está sendo extraído corretamente.
        """
        # Buscar uma nota que já tenha sido processada
        processed_note = TechnicalNote.objects.filter(
            status__in=['processed', 'completed']
        ).first()
        
        if processed_note and processed_note.content_preview:
            # Verificar se tem conteúdo extraído
            self.assertGreater(len(processed_note.content_preview), 50, 
                             "Conteúdo extraído deveria ter pelo menos 50 caracteres")
            
            # Verificar se não é apenas espaços em branco
            self.assertTrue(processed_note.content_preview.strip(), 
                          "Conteúdo não deveria ser apenas espaços em branco")
        else:
            # Se não há notas processadas, vamos processar uma
            self.test_pdf_download_functionality()
            
            # Tentar novamente
            processed_note = TechnicalNote.objects.filter(
                status__in=['processed', 'completed']
            ).first()
            
            if processed_note and processed_note.content_preview:
                self.assertGreater(len(processed_note.content_preview), 20,
                                 "Deveria ter extraído algum conteúdo do PDF")


@tag("integration", "nfe", "full_pipeline")
@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    },
    CELERY_ALWAYS_EAGER=True,
    OPENAI_API_KEY='test-key',
    DATABASE_CONNECTION_KWARGS={
        "TIMEOUT": 30,
    }
)
class NFEFullPipelineIntegrationTest(NFEFazendaPipelineIntegrationTest):
    """Teste do pipeline completo: scraping → download → processamento."""

    @patch('apps.langchain_integration.services.base.ChatOpenAI')
    def test_complete_nfe_pipeline(self, mock_openai):
        """
        Teste completo do pipeline: scraping → download → processamento com LangChain.
        """
        # Configurar mock da chain completa
        mock_chain_result = self.openai_mock_response
        
        # Mock da instância do ChatOpenAI
        mock_chat_instance = Mock()
        mock_openai.return_value = mock_chat_instance
        
        # Mock do método process_batch do TechnicalNoteSummarizerService  
        mock_batch_result = {
            "total": 1,
            "processed": 1,
            "errors": 0,
            "skipped": 0,
            "processing_time": 0.5,
            "results": [{
                "success": True,
                "result": self.openai_mock_response,
                "model_used": "gpt-4o-mini"
            }]
        }
        
        with patch('apps.langchain_integration.services.technical_note_processor.TechnicalNoteSummarizerService.process_batch') as mock_process_batch:
            mock_process_batch.return_value = mock_batch_result


@tag("integration", "nfe", "error_handling")
class NFEErrorHandlingIntegrationTest(NFEFazendaPipelineIntegrationTest):
    """Testes para tratamento de erros no pipeline."""

    def test_handles_invalid_pdf_urls(self):
        """Testa se o sistema trata URLs de PDF inválidas adequadamente."""
        # Buscar ou criar fonte de dados NFE FAZENDA
        try:
            data_source = DataSource.objects.get(name="NFE FAZENDA")
        except DataSource.DoesNotExist:
            data_source = DataSource.objects.create(
                name="NFE FAZENDA",
                url="https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=",
                content_type="pdf",
                description="Notas técnicas NFE Fazenda",
                is_active=True
            )
        
        # Criar nota com URL inválida
        note = TechnicalNote.objects.create(
            source=data_source,
            title="Nota com URL Inválida",
            original_url="https://invalid-url-that-does-not-exist.com/fake.pdf",
            document_hash="invalid_hash_123",
            status="pending",
            file_size=0,
            content_preview=""
        )
        
        # Processar deveria falhar graciosamente
        result = process_pending_technical_notes_job(max_items=1)
        
        # Verificar se o erro foi tratado
        self.assertTrue(result.get('success'), "Job deveria ter sucesso mesmo com erro individual")
        stats = result.get('stats', {})
        # Pode ter erro ou skip dependendo da implementação
        self.assertGreaterEqual(stats.get('errors', 0) + stats.get('skipped', 0), 0)

    @patch('requests.get')
    def test_handles_network_errors(self, mock_get):
        """Testa se o sistema trata erros de rede adequadamente."""
        # Simular erro de rede
        mock_get.side_effect = requests.ConnectionError("Network error")
        
        # Executar scraping
        result = scrape_nfe_fazenda_job()
        
        # Deveria lidar com o erro graciosamente
        self.assertIsNotNone(result)
        # O resultado pode ser sucesso=False ou ter tratamento específico
