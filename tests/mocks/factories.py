"""
Factories para criação de dados de teste.
"""

import random
from datetime import date, timedelta

import factory

from apps.langchain_integration.models import (
    DataSource,
    ProcessedSummary,
    ProcessingLog,
    TechnicalNote,
)
from django.utils import timezone
from factory import Faker, LazyFunction, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyDate, FuzzyText


class DataSourceFactory(DjangoModelFactory):
    """Factory para criar instâncias de DataSource."""

    class Meta:
        model = DataSource

    name = factory.Sequence(lambda n: f"Test Source {n}")
    url = factory.Faker("url")
    content_type = FuzzyChoice(["pdf", "html", "text"])
    description = factory.Faker("text", max_nb_chars=200)
    is_active = True
    scraping_config = factory.LazyFunction(
        lambda: {"enabled": True, "frequency": "daily", "max_items": 100}
    )


class TechnicalNoteFactory(DjangoModelFactory):
    """Factory para TechnicalNote."""

    class Meta:
        model = TechnicalNote

    source = SubFactory(DataSourceFactory)
    title = Faker("sentence", nb_words=5)
    original_url = Faker("url")
    document_hash = Faker("md5")
    publication_date = Faker("date_this_year")
    status = "pending"
    file_size = Faker("pyint", min_value=1000, max_value=500000)
    content_preview = Faker("text", max_nb_chars=500)
    local_file_path = Faker("file_path", depth=3, extension="pdf")


class ProcessingLogFactory(DjangoModelFactory):
    """Factory para criar instâncias de ProcessingLog."""

    class Meta:
        model = ProcessingLog

    technical_note = factory.SubFactory(TechnicalNoteFactory)
    operation = FuzzyChoice(["scraping", "download", "processing", "validation"])
    level = FuzzyChoice(["info", "warning", "error", "debug"])
    message = factory.Faker("sentence")
    details = factory.LazyFunction(
        lambda: {
            "success": True,
            "processed_items": random.randint(1, 100),
        }
    )
    execution_time = factory.Faker("pyfloat", min_value=0.1, max_value=5.0)


class ProcessedSummaryFactory(DjangoModelFactory):
    """Factory para criar instâncias de ProcessedSummary."""

    class Meta:
        model = ProcessedSummary

    technical_note = factory.SubFactory(TechnicalNoteFactory)
    summary = factory.Faker("text", max_nb_chars=500)
    key_points = factory.LazyFunction(
        lambda: [factory.Faker("sentence")._generate() for _ in range(3)]
    )
    changes_identified = factory.LazyFunction(
        lambda: [factory.Faker("sentence")._generate() for _ in range(2)]
    )
    topics = factory.LazyFunction(
        lambda: [factory.Faker("word")._generate() for _ in range(3)]
    )
    model_used = "gpt-3.5-turbo"
    processing_time = factory.Faker("pyfloat", min_value=0.5, max_value=5.0)
    tokens_used = factory.Faker("pyint", min_value=50, max_value=500)
    confidence_score = factory.Faker("pyfloat", min_value=0.5, max_value=1.0)
