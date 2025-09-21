from core.models.base import BaseModel
from django.db import models


class DataSource(BaseModel):
    """Model para fontes de dados que fornecem informações para processamento."""

    name = models.CharField(
        max_length=255, unique=True, help_text="Nome da fonte de dados"
    )
    url = models.URLField(help_text="URL da listagem principal")
    content_type = models.CharField(
        max_length=50,
        choices=[
            ("pdf", "PDF"),
            ("html", "HTML"),
            ("text", "Text"),
        ],
        help_text="Tipo de conteúdo processado",
    )
    description = models.TextField(blank=True, help_text="Descrição da fonte")
    is_active = models.BooleanField(
        default=True, help_text="Se a fonte está ativa para processamento"
    )
    scraping_config = models.JSONField(
        default=dict,
        help_text="Configurações específicas para scraping (seletores CSS, XPath, etc)",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Fonte de Dados"
        verbose_name_plural = "Fontes de Dados"

    def __str__(self):
        return f"{self.name} ({self.content_type.upper()})"


class TechnicalNote(BaseModel):
    """Model para armazenar notas técnicas coletadas."""

    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("processing", "Processando"),
        ("processed", "Processado"),
        ("error", "Erro"),
    ]

    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="technical_notes",
        help_text="Fonte da nota técnica",
    )
    title = models.CharField(max_length=500, help_text="Título da nota técnica")
    original_url = models.URLField(help_text="URL original do documento")
    document_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="Hash MD5 do documento para detectar duplicatas",
    )
    publication_date = models.DateField(
        null=True, blank=True, help_text="Data de publicação"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    file_size = models.IntegerField(
        null=True, blank=True, help_text="Tamanho do arquivo em bytes"
    )
    content_preview = models.TextField(
        blank=True, help_text="Prévia do conteúdo original"
    )

    # Campos para armazenamento local (opcional)
    local_file_path = models.CharField(
        max_length=500, blank=True, help_text="Caminho do arquivo local"
    )

    class Meta:
        ordering = ["-publication_date", "-created_at"]
        verbose_name = "Nota Técnica"
        verbose_name_plural = "Notas Técnicas"
        indexes = [
            models.Index(fields=["source", "status"]),
            models.Index(fields=["document_hash"]),
            models.Index(fields=["publication_date"]),
        ]

    def __str__(self):
        return f"{self.title[:50]}... - {self.source.name}"


class ProcessedSummary(BaseModel):
    """Model para armazenar resumos processados pelo LangChain."""

    technical_note = models.OneToOneField(
        TechnicalNote,
        on_delete=models.CASCADE,
        related_name="summary",
        help_text="Nota técnica resumida",
    )
    summary = models.TextField(help_text="Resumo gerado pelo LangChain")
    key_points = models.JSONField(
        default=list, help_text="Pontos principais extraídos (lista de strings)"
    )
    changes_identified = models.JSONField(
        default=list, help_text="Mudanças ou alterações identificadas"
    )
    topics = models.JSONField(
        default=list, help_text="Tópicos/temas principais identificados"
    )

    # Metadados do processamento
    model_used = models.CharField(max_length=100, help_text="Modelo de IA utilizado")
    processing_time = models.FloatField(
        null=True, blank=True, help_text="Tempo de processamento em segundos"
    )
    tokens_used = models.IntegerField(
        null=True, blank=True, help_text="Número de tokens utilizados"
    )
    confidence_score = models.FloatField(
        null=True, blank=True, help_text="Score de confiança do resumo (0-1)"
    )

    class Meta:
        verbose_name = "Resumo Processado"
        verbose_name_plural = "Resumos Processados"
        indexes = [
            models.Index(fields=["technical_note"]),
            models.Index(fields=["model_used"]),
        ]

    def __str__(self):
        return f"Resumo: {self.technical_note.title[:30]}..."


class ProcessingLog(BaseModel):
    """Model para log detalhado de processamento."""

    OPERATION_CHOICES = [
        ("scraping", "Scraping"),
        ("download", "Download"),
        ("processing", "Processamento IA"),
        ("validation", "Validação"),
    ]

    LEVEL_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("debug", "Debug"),
    ]

    technical_note = models.ForeignKey(
        TechnicalNote,
        on_delete=models.CASCADE,
        related_name="processing_logs",
        help_text="Nota técnica relacionada",
    )
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="info")
    message = models.TextField(help_text="Mensagem do log")
    details = models.JSONField(default=dict, help_text="Detalhes adicionais em JSON")
    execution_time = models.FloatField(
        null=True, blank=True, help_text="Tempo de execução em segundos"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Log de Processamento"
        verbose_name_plural = "Logs de Processamento"
        indexes = [
            models.Index(fields=["technical_note", "operation"]),
            models.Index(fields=["level", "created_at"]),
        ]

    def __str__(self):
        return f"{self.operation.title()}: {self.message[:50]}..."
