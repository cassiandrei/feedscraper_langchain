import io
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin

import PyPDF2
from bs4 import BeautifulSoup

from .base import BaseFeedScraper


logger = logging.getLogger(__name__)


class NFEFazendaScraper(BaseFeedScraper):
    """
    Scraper específico para notas técnicas do site da NFE Fazenda.

    Site: https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=

    Este scraper:
    - Acessa a listagem de notas técnicas
    - Extrai links para os PDFs
    - Baixa e processa os PDFs
    - Extrai texto para preview
    """

    def __init__(self, data_source, **kwargs):
        """
        Inicializa o scraper para NFE Fazenda.

        Args:
            data_source: DataSource model instance
            **kwargs: Argumentos passados para a classe base
        """
        super().__init__(data_source, **kwargs)

        # Configurações específicas para NFE Fazenda
        self.base_url = "https://www.nfe.fazenda.gov.br"

        # Headers específicos que podem ser necessários
        self.session.headers.update(
            {
                "Referer": "https://www.nfe.fazenda.gov.br/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            }
        )

    def _extract_items_from_listing(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrai itens de notas técnicas da página de listagem da NFE Fazenda.

        Args:
            soup: BeautifulSoup object da página de listagem

        Returns:
            Lista de dicionários com informações das notas técnicas
        """
        items = []

        try:
            # A estrutura específica pode variar, mas geralmente é uma tabela ou lista
            # Vamos procurar por links que contêm 'exibirArquivo.aspx'

            # Procurar por todos os links que parecem ser de arquivos/PDFs
            links = soup.find_all("a", href=re.compile(r"exibirArquivo\.aspx"))

            if not links:
                # Fallback: procurar por qualquer link que contenha 'conteudo='
                links = soup.find_all("a", href=re.compile(r"conteudo="))

            logger.info(f"Encontrados {len(links)} links de arquivos")

            for link in links:
                try:
                    href = link.get("href")
                    if not href:
                        continue

                    # Construir URL completa
                    if href.startswith("http"):
                        full_url = href
                    else:
                        full_url = urljoin(self.base_url, href)

                    # Extrair título - pode estar no texto do link ou em elementos próximos
                    title = self._extract_title_from_link(link, soup)

                    if not title:
                        continue

                    # Tentar extrair data de publicação
                    publication_date = self._extract_date_from_context(link, soup)

                    item = {
                        "title": title.strip(),
                        "url": full_url,
                        "publication_date": publication_date,
                    }

                    items.append(item)

                except Exception as e:
                    logger.warning(f"Erro ao processar link: {str(e)}")
                    continue

            # Remover duplicatas baseado na URL
            seen_urls = set()
            unique_items = []
            for item in items:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    unique_items.append(item)

            logger.info(f"Extraídos {len(unique_items)} itens únicos da listagem")
            return unique_items

        except Exception as e:
            logger.error(f"Erro ao extrair itens da listagem: {str(e)}")
            return []

    def _extract_title_from_link(self, link, soup: BeautifulSoup) -> str:
        """
        Extrai o título da nota técnica a partir do link e contexto.

        Args:
            link: Tag <a> do BeautifulSoup
            soup: BeautifulSoup object completo da página

        Returns:
            Título extraído ou string vazia se não encontrado
        """
        # Estratégia 1: Texto do próprio link
        link_text = link.get_text(strip=True)
        if link_text and len(link_text) > 10:  # Filtrar textos muito curtos
            return link_text

        # Estratégia 2: Procurar em elementos pais ou irmãos
        parent = link.parent
        if parent:
            # Procurar no mesmo td/div
            parent_text = parent.get_text(strip=True)
            if parent_text and len(parent_text) > 10:
                return parent_text

            # Procurar em elementos irmãos
            for sibling in parent.find_all(["td", "div", "span"]):
                sibling_text = sibling.get_text(strip=True)
                if sibling_text and len(sibling_text) > 10 and sibling != link:
                    return sibling_text

        # Estratégia 3: Procurar na mesma linha da tabela
        tr_parent = link.find_parent("tr")
        if tr_parent:
            tds = tr_parent.find_all("td")
            for td in tds:
                td_text = td.get_text(strip=True)
                if td_text and len(td_text) > 10 and link not in td.find_all("a"):
                    return td_text

        # Fallback: usar parte da URL ou timestamp
        return f"Nota Técnica {datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _extract_date_from_context(self, link, soup: BeautifulSoup) -> datetime:
        """
        Tenta extrair data de publicação do contexto do link.

        Args:
            link: Tag <a> do BeautifulSoup
            soup: BeautifulSoup object completo da página

        Returns:
            Data de publicação ou None se não encontrada
        """
        # Padrões de data comuns
        date_patterns = [
            r"\d{2}/\d{2}/\d{4}",  # dd/mm/yyyy
            r"\d{2}-\d{2}-\d{4}",  # dd-mm-yyyy
            r"\d{4}/\d{2}/\d{2}",  # yyyy/mm/dd
            r"\d{4}-\d{2}-\d{2}",  # yyyy-mm-dd
        ]

        # Procurar na mesma linha da tabela
        tr_parent = link.find_parent("tr")
        if tr_parent:
            tr_text = tr_parent.get_text()
            for pattern in date_patterns:
                matches = re.findall(pattern, tr_text)
                if matches:
                    try:
                        date_str = matches[0]
                        # Tentar diferentes formatos
                        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"]:
                            try:
                                return datetime.strptime(date_str, fmt).date()
                            except ValueError:
                                continue
                    except Exception:
                        continue

        return None

    def _get_content_from_item(self, item_info: Dict[str, Any]) -> Tuple[bytes, str]:
        """
        Obtém o conteúdo do PDF da nota técnica.

        Args:
            item_info: Informações do item com 'url', 'title', etc.

        Returns:
            Tuple com (conteúdo_pdf_em_bytes, preview_texto)
        """
        url = item_info["url"]

        try:
            # Baixar o PDF
            response = self._make_request(url)
            pdf_content = response.content

            # Extrair texto do PDF para preview
            preview_text = self._extract_text_from_pdf(pdf_content)

            return pdf_content, preview_text

        except Exception as e:
            logger.error(f"Erro ao baixar conteúdo de {url}: {str(e)}")
            raise

    def _extract_text_from_pdf(self, pdf_content: bytes, max_pages: int = 3) -> str:
        """
        Extrai texto de um PDF para criar um preview.

        Args:
            pdf_content: Conteúdo do PDF em bytes
            max_pages: Número máximo de páginas para extrair (para limitar o preview)

        Returns:
            Texto extraído do PDF
        """
        try:
            # Usar BytesIO para criar um arquivo-like object
            pdf_file = io.BytesIO(pdf_content)

            # Tentar com PyPDF2 primeiro
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_content = []

                # Limitar o número de páginas para o preview
                pages_to_process = min(len(pdf_reader.pages), max_pages)

                for page_num in range(pages_to_process):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)

                full_text = "\n\n".join(text_content)

                # Limpar e formatar o texto
                cleaned_text = self._clean_extracted_text(full_text)

                return cleaned_text

            except Exception as e:
                logger.warning(f"Erro com PyPDF2: {str(e)}")

                # Fallback: tentar com pdfplumber se disponível
                try:
                    import pdfplumber

                    pdf_file.seek(0)  # Reset do buffer

                    with pdfplumber.open(pdf_file) as pdf:
                        text_content = []
                        pages_to_process = min(len(pdf.pages), max_pages)

                        for page_num in range(pages_to_process):
                            page = pdf.pages[page_num]
                            text = page.extract_text()
                            if text and text.strip():
                                text_content.append(text)

                        full_text = "\n\n".join(text_content)
                        return self._clean_extracted_text(full_text)

                except ImportError:
                    logger.warning("pdfplumber não disponível, usando PyPDF2")
                    return f"[Erro na extração de texto do PDF: {str(e)}]"
                except Exception as e2:
                    logger.error(f"Erro com pdfplumber: {str(e2)}")
                    return f"[Erro na extração de texto: {str(e2)}]"

        except Exception as e:
            logger.error(f"Erro fatal na extração de texto do PDF: {str(e)}")
            return f"[Erro na extração de texto do PDF: {str(e)}]"

    def _clean_extracted_text(self, text: str) -> str:
        """
        Limpa e formata o texto extraído do PDF.

        Args:
            text: Texto bruto extraído

        Returns:
            Texto limpo e formatado
        """
        if not text:
            return ""

        # Remover quebras de linha excessivas
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

        # Remover espaços em excesso
        text = re.sub(r" +", " ", text)

        # Remover caracteres de controle problemáticos
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]", "", text)

        # Limitar o tamanho do preview
        if len(text) > 2000:
            text = text[:2000] + "... [texto truncado]"

        return text.strip()

    def get_scraping_config(self) -> Dict[str, Any]:
        """
        Retorna configuração específica para este scraper.

        Returns:
            Configuração como dict
        """
        return {
            "base_url": self.base_url,
            "content_type": "pdf",
            "selectors": {
                "file_links": 'a[href*="exibirArquivo.aspx"]',
                "fallback_links": 'a[href*="conteudo="]',
            },
            "rate_limit": self.delay_between_requests,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
        }
