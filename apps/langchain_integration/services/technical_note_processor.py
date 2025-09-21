import logging
import time
from typing import Any, Dict, List, Optional

from django.conf import settings
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from apps.langchain_integration.models import ProcessedSummary, TechnicalNote

from apps.langchain_integration.services.base import BaseLangChainService


logger = logging.getLogger(__name__)


class TechnicalNoteSummarizerService(BaseLangChainService):
    """
    Service especializado para sumarizar notas técnicas usando LangChain.

    Este service:
    - Processa texto extraído de PDFs
    - Gera resumos estruturados
    - Identifica pontos-chave e mudanças
    - Extrai tópicos principais
    - Salva resultados no banco de dados
    """

    def __init__(
        self, model_name: Optional[str] = None, temperature: Optional[float] = None
    ):
        """
        Inicializa o service de sumarização.

        Args:
            model_name: Nome do modelo (default: gpt-4-turbo-preview ou configurado)
            temperature: Temperatura do modelo (default: 0.1 para mais consistência)
        """
        # Para sumarização, usar temperatura mais baixa para consistência
        super().__init__(
            model_name=model_name
            or "gpt-4o-mini",  # Usar GPT-4-mini conforme especificado
            temperature=temperature if temperature is not None else 0.1,
        )

        self.output_parser = JsonOutputParser()

    def build_chain(self):
        """
        Constrói a chain do LangChain para sumarização de notas técnicas.

        Returns:
            Chain configurada para sumarização
        """
        # Template do prompt específico para notas técnicas fiscais
        prompt_template = """
        Você é um especialista em análise de documentos fiscais e tributários brasileiros.
        
        Analise o seguinte texto extraído de uma nota técnica da Receita Federal sobre NFe (Nota Fiscal eletrônica) e forneça um resumo estruturado.
        
        TEXTO DA NOTA TÉCNICA:
        {content}
        
        INSTRUÇÕES:
        1. Crie um resumo conciso mas completo (máximo 500 palavras)
        2. Identifique os pontos-chave mais importantes (3-8 pontos)
        3. Liste todas as mudanças, alterações ou novidades mencionadas
        4. Identifique os tópicos/temas principais abordados
        5. Mantenha foco em informações práticas para empresas que emitem NFe
        
        FORMATO DE RESPOSTA:
        Responda APENAS em formato JSON válido com a seguinte estrutura:
        {{
            "summary": "Resumo completo da nota técnica...",
            "key_points": [
                "Ponto importante 1",
                "Ponto importante 2",
                "..."
            ],
            "changes_identified": [
                "Mudança ou alteração 1",
                "Mudança ou alteração 2",
                "..."
            ],
            "topics": [
                "Tópico principal 1",
                "Tópico principal 2",
                "..."
            ],
            "confidence_score": 0.95
        }}
        
        IMPORTANTE: 
        - Se não houver mudanças específicas, deixe "changes_identified" como array vazio
        - O confidence_score deve ser um número entre 0 e 1 baseado na qualidade do texto fonte
        - Seja específico e técnico, mas mantenha linguagem acessível
        """

        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Construir a chain
        chain = prompt | self.llm | self.output_parser

        return chain

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa input através da chain LangChain (implementação da classe abstrata).

        Args:
            input_data: Dict contendo 'content' e opcionalmente outros metadados

        Returns:
            Dict com resultado do processamento
        """
        try:
            if not self.llm:
                raise ValueError("LLM não inicializado - verifique OPENAI_API_KEY")

            # Verificar se chain foi construída
            if not hasattr(self, "_chain"):
                self._chain = self.build_chain()

            # Executar chain
            result = self._chain.invoke(input_data)

            return {"success": True, "result": result, "model_used": self.model_name}

        except Exception as e:
            return self._handle_error(e, input_data)

    def process_technical_note(self, technical_note: TechnicalNote) -> Dict[str, Any]:
        """
        Processa uma nota técnica completa, gerando resumo e salvando no banco.

        Args:
            technical_note: Instância da TechnicalNote para processar

        Returns:
            Dict com resultado do processamento
        """
        start_time = time.time()

        try:
            logger.info(f"Iniciando processamento de nota técnica: {technical_note.id}")

            # Verificar se já foi processada
            if hasattr(technical_note, "summary"):
                return {
                    "success": False,
                    "error": "Nota técnica já foi processada",
                    "technical_note_id": str(technical_note.id),
                }

            # Marcar como processando
            technical_note.status = "processing"
            technical_note.save()

            # Usar o preview como conteúdo para processamento
            content = technical_note.content_preview
            if not content or len(content.strip()) < 50:
                raise ValueError("Conteúdo insuficiente para processamento")

            # Processar com LangChain
            result = self.process({"content": content})

            if not result["success"]:
                technical_note.status = "error"
                technical_note.save()
                return result

            # Extrair dados do resultado
            summary_data = result["result"]

            # Criar o resumo processado
            processed_summary = ProcessedSummary.objects.create(
                technical_note=technical_note,
                summary=summary_data.get("summary", ""),
                key_points=summary_data.get("key_points", []),
                changes_identified=summary_data.get("changes_identified", []),
                topics=summary_data.get("topics", []),
                model_used=self.model_name,
                processing_time=time.time() - start_time,
                tokens_used=result.get("tokens_used"),
                confidence_score=summary_data.get("confidence_score", 0.0),
            )

            # Marcar nota técnica como processada
            technical_note.status = "processed"
            technical_note.save()

            end_time = time.time()

            logger.info(
                f"Nota técnica processada com sucesso em {end_time - start_time:.2f}s"
            )

            return {
                "success": True,
                "technical_note_id": str(technical_note.id),
                "summary_id": str(processed_summary.id),
                "processing_time": end_time - start_time,
                "model_used": self.model_name,
                "summary_preview": (
                    summary_data.get("summary", "")[:200] + "..."
                    if summary_data.get("summary", "")
                    else ""
                ),
            }

        except Exception as e:
            # Marcar como erro
            technical_note.status = "error"
            technical_note.save()

            error_msg = str(e)
            logger.error(
                f"Erro ao processar nota técnica {technical_note.id}: {error_msg}"
            )

            return {
                "success": False,
                "error": error_msg,
                "technical_note_id": str(technical_note.id),
                "processing_time": time.time() - start_time,
            }

    def process_batch(self, technical_notes: List[TechnicalNote]) -> Dict[str, Any]:
        """
        Processa um lote de notas técnicas.

        Args:
            technical_notes: Lista de TechnicalNote para processar

        Returns:
            Dict com estatísticas do processamento em lote
        """
        start_time = time.time()
        stats = {
            "total": len(technical_notes),
            "processed": 0,
            "errors": 0,
            "skipped": 0,
            "processing_time": 0,
            "results": [],
        }

        logger.info(
            f"Iniciando processamento em lote de {len(technical_notes)} notas técnicas"
        )

        for technical_note in technical_notes:
            try:
                result = self.process_technical_note(technical_note)
                stats["results"].append(result)

                if result["success"]:
                    stats["processed"] += 1
                else:
                    if "já foi processada" in result.get("error", ""):
                        stats["skipped"] += 1
                    else:
                        stats["errors"] += 1

            except Exception as e:
                logger.error(
                    f"Erro inesperado ao processar nota {technical_note.id}: {str(e)}"
                )
                stats["errors"] += 1
                stats["results"].append(
                    {
                        "success": False,
                        "error": str(e),
                        "technical_note_id": str(technical_note.id),
                    }
                )

        stats["processing_time"] = time.time() - start_time

        logger.info(f"Processamento em lote concluído: {stats}")
        return stats

    def get_pending_notes(self, limit: Optional[int] = None) -> List[TechnicalNote]:
        """
        Retorna notas técnicas pendentes de processamento.

        Args:
            limit: Limite de notas para retornar

        Returns:
            Lista de TechnicalNote pendentes
        """
        queryset = TechnicalNote.objects.filter(status="pending").order_by("created_at")

        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de processamento.

        Returns:
            Dict com estatísticas
        """
        from django.db.models import Count

        # Contar por status
        status_counts = dict(
            TechnicalNote.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        # Contar resumos processados
        total_summaries = ProcessedSummary.objects.count()

        # Estatísticas por modelo
        model_stats = dict(
            ProcessedSummary.objects.values("model_used")
            .annotate(count=Count("id"))
            .values_list("model_used", "count")
        )

        return {
            "status_counts": status_counts,
            "total_summaries": total_summaries,
            "model_usage": model_stats,
            "pending_count": status_counts.get("pending", 0),
            "processed_count": status_counts.get("processed", 0),
            "error_count": status_counts.get("error", 0),
        }


class TechnicalNoteAnalysisService(BaseLangChainService):
    """
    Service para análises mais avançadas de notas técnicas.

    Complementa o TechnicalNoteSummarizerService com:
    - Análise de impacto
    - Classificação por urgência
    - Comparação com notas anteriores
    - Extração de prazos e datas importantes
    """

    def __init__(
        self, model_name: Optional[str] = None, temperature: Optional[float] = None
    ):
        super().__init__(
            model_name=model_name or "gpt-4o-mini",
            temperature=temperature if temperature is not None else 0.2,
        )

        self.output_parser = JsonOutputParser()

    def build_chain(self):
        """
        Constrói chain para análise avançada de notas técnicas.

        Returns:
            Chain configurada para análise
        """
        prompt_template = """
        Você é um consultor tributário especialista em NFe e regulamentações fiscais brasileiras.
        
        Analise a seguinte nota técnica e forneça uma análise de impacto detalhada:
        
        TÍTULO: {title}
        RESUMO: {summary}
        PONTOS-CHAVE: {key_points}
        MUDANÇAS: {changes_identified}
        
        Forneça uma análise estruturada sobre:
        
        FORMATO DE RESPOSTA (JSON):
        {{
            "impact_level": "alto|médio|baixo",
            "urgency": "urgente|importante|informativo",
            "affected_business_types": ["tipo1", "tipo2", ...],
            "implementation_deadline": "data ou prazo se mencionado, ou null",
            "action_required": "Sim|Não|Recomendado",
            "recommended_actions": [
                "Ação recomendada 1",
                "Ação recomendada 2"
            ],
            "compliance_risk": "alto|médio|baixo",
            "estimated_effort": "horas ou descrição do esforço necessário"
        }}
        """

        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | self.output_parser
        return chain

    def analyze_impact(self, processed_summary: ProcessedSummary) -> Dict[str, Any]:
        """
        Realiza análise de impacto de uma nota técnica processada.

        Args:
            processed_summary: Resumo processado para analisar

        Returns:
            Dict com análise de impacto
        """
        try:
            technical_note = processed_summary.technical_note

            input_data = {
                "title": technical_note.title,
                "summary": processed_summary.summary,
                "key_points": processed_summary.key_points,
                "changes_identified": processed_summary.changes_identified,
            }

            result = self.process(input_data)

            if result["success"]:
                # Salvar análise como metadata no ProcessedSummary
                analysis_data = result["result"]

                # Atualizar o ProcessedSummary com dados da análise
                # Isso poderia ser um campo JSON adicional ou modelo separado
                # Por simplicidade, vamos adicionar aos detalhes do log

                return {
                    "success": True,
                    "analysis": analysis_data,
                    "summary_id": str(processed_summary.id),
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Erro na análise de impacto: {str(e)}")
            return {"success": False, "error": str(e)}
