from django.contrib import admin

from .models import DataSource, ProcessedSummary, ProcessingLog, TechnicalNote


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "content_type", "is_active", "created_at")
    list_filter = ("content_type", "is_active", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("name", "url", "content_type", "description", "is_active")},
        ),
        ("Configurações", {"fields": ("scraping_config",), "classes": ("collapse",)}),
        (
            "Metadados",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(TechnicalNote)
class TechnicalNoteAdmin(admin.ModelAdmin):
    list_display = (
        "title_truncated",
        "source",
        "status",
        "publication_date",
        "created_at",
    )
    list_filter = ("status", "source", "publication_date", "created_at")
    search_fields = ("title", "content_preview")
    readonly_fields = ("id", "document_hash", "created_at", "updated_at")
    date_hierarchy = "publication_date"

    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("source", "title", "original_url", "publication_date")},
        ),
        (
            "Status e Processamento",
            {"fields": ("status", "document_hash", "file_size")},
        ),
        (
            "Conteúdo",
            {
                "fields": ("content_preview", "local_file_path"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadados",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def title_truncated(self, obj):
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title

    title_truncated.short_description = "Título"


@admin.register(ProcessedSummary)
class ProcessedSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "technical_note_title",
        "model_used",
        "confidence_score",
        "processing_time",
        "created_at",
    )
    list_filter = ("model_used", "created_at")
    search_fields = ("technical_note__title", "summary")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Nota Técnica", {"fields": ("technical_note",)}),
        (
            "Resumo",
            {"fields": ("summary", "key_points", "changes_identified", "topics")},
        ),
        (
            "Metadados do Processamento",
            {
                "fields": (
                    "model_used",
                    "processing_time",
                    "tokens_used",
                    "confidence_score",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadados",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def technical_note_title(self, obj):
        return (
            obj.technical_note.title[:50] + "..."
            if len(obj.technical_note.title) > 50
            else obj.technical_note.title
        )

    technical_note_title.short_description = "Nota Técnica"


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = (
        "technical_note_title",
        "operation",
        "level",
        "message_truncated",
        "created_at",
    )
    list_filter = ("operation", "level", "created_at")
    search_fields = ("technical_note__title", "message")
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        ("Log", {"fields": ("technical_note", "operation", "level", "message")}),
        (
            "Detalhes",
            {"fields": ("details", "execution_time"), "classes": ("collapse",)},
        ),
        (
            "Metadados",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def technical_note_title(self, obj):
        return (
            obj.technical_note.title[:30] + "..."
            if len(obj.technical_note.title) > 30
            else obj.technical_note.title
        )

    technical_note_title.short_description = "Nota Técnica"

    def message_truncated(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message

    message_truncated.short_description = "Mensagem"
