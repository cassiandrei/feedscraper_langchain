import hashlib
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone

from apps.langchain_integration.models import DataSource, ProcessingLog, TechnicalNote


logger = logging.getLogger(__name__)


class BaseFeedScraper(ABC):
    """
    Classe base para scraping de diferentes tipos de feeds e conteúdo.

    Esta classe fornece funcionalidade comum para:
    - Fazer requests HTTP com retry e rate limiting
    - Parsear HTML usando BeautifulSoup
    - Gerenciar sessões e headers
    - Log de operações
    - Detecção de duplicatas via hash
    - Armazenamento no banco de dados
    """

    def __init__(
        self,
        data_source: DataSource,
        session: Optional[requests.Session] = None,
        delay_between_requests: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """
        Inicializa o scraper base.

        Args:
            data_source: Fonte de dados do Django model
            session: Sessão HTTP reutilizável (opcional)
            delay_between_requests: Delay entre requests em segundos
            max_retries: Número máximo de tentativas
            timeout: Timeout para requests em segundos
        """
        self.data_source = data_source
        self.session = session or self._create_session()
        self.delay_between_requests = delay_between_requests
        self.max_retries = max_retries
        self.timeout = timeout
        self.last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Cria uma nova sessão HTTP com configurações padrão."""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        return session

    def _rate_limit(self):
        """Implementa rate limiting entre requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.delay_between_requests:
            sleep_time = self.delay_between_requests - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """
        Faz uma requisição HTTP com retry e rate limiting.

        Args:
            url: URL para fazer o request
            **kwargs: Argumentos adicionais para requests

        Returns:
            Response object

        Raises:
            requests.RequestException: Se falhar após todas as tentativas
        """
        self._rate_limit()

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                logger.warning(
                    f"Request attempt {attempt + 1} failed for {url}: {str(e)}"
                )
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)  # Exponential backoff

    def _parse_html(self, content: str) -> BeautifulSoup:
        """
        Parse HTML content usando BeautifulSoup.

        Args:
            content: HTML content como string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(content, "html.parser")

    def _generate_content_hash(self, content: bytes) -> str:
        """
        Gera hash MD5 do conteúdo para detecção de duplicatas.

        Args:
            content: Conteúdo em bytes

        Returns:
            Hash MD5 como string hexadecimal
        """
        return hashlib.md5(content).hexdigest()

    def _is_duplicate(self, content_hash: str) -> bool:
        """
        Verifica se o conteúdo já foi processado baseado no hash.

        Args:
            content_hash: Hash MD5 do conteúdo

        Returns:
            True se é duplicata, False caso contrário
        """
        return TechnicalNote.objects.filter(document_hash=content_hash).exists()

    def _log_operation(
        self,
        technical_note: Optional[TechnicalNote],
        operation: str,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
    ):
        """
        Log de operação no banco de dados.

        Args:
            technical_note: Instância da nota técnica (pode ser None)
            operation: Tipo de operação
            level: Nível do log (info, warning, error, debug)
            message: Mensagem do log
            details: Detalhes adicionais em formato dict
            execution_time: Tempo de execução em segundos
        """
        if technical_note:
            ProcessingLog.objects.create(
                technical_note=technical_note,
                operation=operation,
                level=level,
                message=message,
                details=details or {},
                execution_time=execution_time,
            )

        # Log também no sistema de logging padrão
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, f"[{operation.upper()}] {message}")

    def _create_technical_note(
        self,
        title: str,
        original_url: str,
        content_hash: str,
        publication_date=None,
        file_size: Optional[int] = None,
        content_preview: str = "",
        status: str = "pending",
    ) -> TechnicalNote:
        """
        Cria uma nova nota técnica no banco de dados.

        Args:
            title: Título da nota técnica
            original_url: URL original do documento
            content_hash: Hash MD5 do conteúdo
            publication_date: Data de publicação
            file_size: Tamanho do arquivo em bytes
            content_preview: Prévia do conteúdo
            status: Status inicial

        Returns:
            Instância da TechnicalNote criada
        """
        return TechnicalNote.objects.create(
            source=self.data_source,
            title=title,
            original_url=original_url,
            document_hash=content_hash,
            publication_date=publication_date,
            file_size=file_size,
            content_preview=content_preview,
            status=status,
        )

    @abstractmethod
    def _extract_items_from_listing(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrai itens individuais da listagem principal.

        Args:
            soup: BeautifulSoup object da página de listagem

        Returns:
            Lista de dicionários com informações dos itens

        Deve retornar lista com dicts contendo pelo menos:
        - title: Título do item
        - url: URL do item/documento
        - publication_date: Data de publicação (opcional)
        """
        pass

    @abstractmethod
    def _get_content_from_item(self, item_info: Dict[str, Any]) -> Tuple[bytes, str]:
        """
        Obtém o conteúdo completo de um item específico.

        Args:
            item_info: Informações do item retornadas por _extract_items_from_listing

        Returns:
            Tuple com (conteúdo_em_bytes, preview_em_texto)

        Para PDFs: baixa o arquivo e extrai preview do texto
        Para HTML: obtém o HTML e extrai texto
        Para outros formatos: implementa conforme necessário
        """
        pass

    def scrape_new_items(self) -> Dict[str, Any]:
        """
        Executa o scraping completo para novos itens.

        Returns:
            Dict com estatísticas do processamento:
            - total_found: Total de itens encontrados
            - new_items: Número de itens novos processados
            - duplicates_skipped: Número de duplicatas ignoradas
            - errors: Número de erros
            - processing_time: Tempo total de processamento
        """
        start_time = time.time()
        stats = {
            "total_found": 0,
            "new_items": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "processing_time": 0,
        }

        try:
            logger.info(f"Iniciando scraping para {self.data_source.name}")

            # 1. Obter página de listagem
            response = self._make_request(self.data_source.url)
            soup = self._parse_html(response.text)

            # 2. Extrair itens da listagem
            items = self._extract_items_from_listing(soup)
            stats["total_found"] = len(items)

            logger.info(f"Encontrados {len(items)} itens na listagem")

            # 3. Processar cada item
            for item_info in items:
                try:
                    # Verificar se já processamos este item (baseado na URL)
                    if TechnicalNote.objects.filter(
                        source=self.data_source, original_url=item_info["url"]
                    ).exists():
                        stats["duplicates_skipped"] += 1
                        continue

                    # Obter conteúdo do item
                    content, preview = self._get_content_from_item(item_info)
                    content_hash = self._generate_content_hash(content)

                    # Verificar duplicata por hash
                    if self._is_duplicate(content_hash):
                        stats["duplicates_skipped"] += 1
                        continue

                    # Criar nota técnica
                    technical_note = self._create_technical_note(
                        title=item_info["title"],
                        original_url=item_info["url"],
                        content_hash=content_hash,
                        publication_date=item_info.get("publication_date"),
                        file_size=len(content),
                        content_preview=preview[:1000],  # Limitar preview
                        status="pending",
                    )

                    self._log_operation(
                        technical_note=technical_note,
                        operation="scraping",
                        level="info",
                        message=f'Nova nota técnica coletada: {item_info["title"][:50]}...',
                        details={"item_info": item_info},
                    )

                    stats["new_items"] += 1

                except Exception as e:
                    logger.error(
                        f"Erro ao processar item {item_info.get('url', 'unknown')}: {str(e)}"
                    )
                    stats["errors"] += 1

                    self._log_operation(
                        technical_note=None,
                        operation="scraping",
                        level="error",
                        message=f"Erro ao processar item: {str(e)}",
                        details={"item_info": item_info, "error": str(e)},
                    )

            end_time = time.time()
            stats["processing_time"] = end_time - start_time

            logger.info(f"Scraping concluído. Stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Erro crítico no scraping: {str(e)}")
            stats["errors"] += 1
            stats["processing_time"] = time.time() - start_time
            raise

    def get_pending_items(self) -> List[TechnicalNote]:
        """
        Retorna itens pendentes de processamento para esta fonte.

        Returns:
            Lista de TechnicalNote com status 'pending'
        """
        return TechnicalNote.objects.filter(
            source=self.data_source, status="pending"
        ).order_by("created_at")

    def mark_as_processing(self, technical_note: TechnicalNote):
        """Marca uma nota técnica como sendo processada."""
        technical_note.status = "processing"
        technical_note.save()

        self._log_operation(
            technical_note=technical_note,
            operation="processing",
            level="info",
            message="Iniciado processamento da nota técnica",
        )

    def mark_as_processed(self, technical_note: TechnicalNote):
        """Marca uma nota técnica como processada com sucesso."""
        technical_note.status = "processed"
        technical_note.save()

        self._log_operation(
            technical_note=technical_note,
            operation="processing",
            level="info",
            message="Nota técnica processada com sucesso",
        )

    def mark_as_error(self, technical_note: TechnicalNote, error_message: str):
        """Marca uma nota técnica com erro no processamento."""
        technical_note.status = "error"
        technical_note.save()

        self._log_operation(
            technical_note=technical_note,
            operation="processing",
            level="error",
            message=f"Erro no processamento: {error_message}",
            details={"error": error_message},
        )
