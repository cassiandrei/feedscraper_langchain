# PRP (Product Requirement Prompt) - Template Base
## Django + LangChain + Scheduled Jobs

### Versão: 1.0
### Data: 20 de setembro de 2025

---

## 📋 Visão Geral do Projeto

Este template PRP serve como guia base para desenvolvimento de aplicações Django integradas com LangChain e sistema de jobs agendados via django-apscheduler, seguindo princípios de arquitetura limpa e boas práticas de desenvolvimento.

### Stack Tecnológica
- **Backend Framework**: Django 5.2+
- **AI/ML Framework**: LangChain (Python)
- **Job Scheduler**: django-apscheduler + APScheduler 4.0+
- **Database**: PostgreSQL (recomendado) / SQLite (desenvolvimento)
- **Python Version**: 3.12+
- **Environment Management**: django-environ

---

## 📦 Dependências e Requirements

### Estrutura de Requirements

```
requirements/
├── base.txt          # Dependências essenciais
├── development.txt   # Dependências de desenvolvimento
└── production.txt    # Dependências de produção
```

### requirements/base.txt

```txt
# Core Django
Django>=5.2,<5.3
djangorestframework>=3.15.0
django-cors-headers>=4.3.0
django-environ>=0.10.0

# Database
psycopg2-binary>=2.9.0
dj-database-url>=2.1.0

# LangChain
langchain>=0.2.0
langchain-core>=0.2.0
langchain-openai>=0.1.0
langchain-community>=0.2.0

# Job Scheduling
APScheduler>=4.0.0
django-apscheduler>=0.6.2

# HTTP Requests
requests>=2.31.0
urllib3>=2.0.0

# Date and Time
python-dateutil>=2.8.0
pytz>=2023.3

# Validation
pydantic>=2.7.0

# Caching
redis>=5.0.0
```

### requirements/development.txt

```txt
-r base.txt

# Testing Framework
pytest>=7.4.0
pytest-django>=4.5.2
pytest-cov>=4.1.0
pytest-mock>=3.11.0
factory-boy>=3.3.0
faker>=19.3.0

# Alternative: Django's built-in testing
# coverage>=7.2.0  # Se usar unittest ao invés de pytest

# Code Quality
black>=23.7.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.5.0
pre-commit>=3.3.0

# Debug & Development
django-debug-toolbar>=4.2.0
ipdb>=0.13.13
django-extensions>=3.2.0

# Documentation
sphinx>=7.1.0
sphinx-rtd-theme>=1.3.0
```

### requirements/testing.txt

```txt
-r base.txt

# Core testing dependencies
pytest>=7.4.0
pytest-django>=4.5.2
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-xdist>=3.3.0        # Parallel test execution
pytest-sugar>=0.9.7        # Better test output
pytest-clarity>=1.0.1      # Better assertion output

# Test data and factories  
factory-boy>=3.3.0
faker>=19.3.0

# Coverage and reporting
coverage>=7.2.0
coverage[toml]>=7.2.0

# Mock and stub utilities
responses>=0.23.0          # HTTP requests mocking
freezegun>=1.2.0          # Time/datetime mocking
testfixtures>=7.1.0       # Additional test utilities

# Performance testing (optional)
pytest-benchmark>=4.0.0   # Performance regression testing
```

### requirements/production.txt

```txt
-r base.txt

# Production Server
gunicorn>=21.2.0
whitenoise>=6.5.0

# Monitoring
sentry-sdk>=1.32.0

# Environment
python-dotenv>=1.0.0
```

---

## 🏗️ Arquitetura Limpa - Estrutura do Projeto

### Estrutura de Diretórios Recomendada

```
projeto/
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   ├── testing.txt
│   └── production.txt
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── testing.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── base.py
│   ├── permissions/
│   ├── utils/
│   └── validators/
├── apps/
│   ├── __init__.py
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── schedulers.py
│   │   ├── tasks.py
│   │   ├── views.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── unit/
│   │       │   ├── test_models.py
│   │       │   ├── test_tasks.py
│   │       │   └── test_schedulers.py
│   │       └── integration/
│   │           ├── test_job_flows.py
│   │           └── test_scheduler_integration.py
│   ├── langchain_integration/
│   │   ├── __init__.py
│   │   ├── chains/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── prompts/
│   │   ├── services/
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── unit/
│   │       │   ├── test_services.py
│   │       │   └── test_models.py
│   │       └── integration/
│   │           ├── test_langchain_flows.py
│   │           └── test_api_endpoints.py
│   └── [outras_apps]/
├── infrastructure/
│   ├── __init__.py
│   ├── database/
│   ├── cache/
│   ├── storage/
│   └── external_apis/
└── tests/
    ├── __init__.py
    ├── conftest.py              # Configurações pytest (se usado)
    ├── base.py                  # Base classes para testes
    ├── unit/                    # Testes unitários globais
    │   ├── __init__.py
    │   ├── test_core_utils.py
    │   └── test_core_models.py
    ├── integration/             # Testes de integração entre apps
    │   ├── __init__.py
    │   ├── test_jobs_langchain.py
    │   └── test_complete_workflows.py
    ├── functional/              # Testes funcionais/E2E
    │   ├── __init__.py
    │   ├── test_api_workflows.py
    │   └── test_user_journeys.py
    ├── fixtures/                # Dados para testes
    │   ├── test_data.json
    │   └── sample_files/
    │       └── example.txt
    └── mocks/                   # Factories e mocks
        ├── __init__.py
        ├── factories.py
        └── mock_services.py
```

---

## 🔧 Configurações Django

### Settings Base (config/settings/base.py)

```python
import os
import environ
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Inicializar django-environ
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'django-insecure-change-in-production'),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, f'sqlite:///{BASE_DIR}/db.sqlite3'),
    OPENAI_API_KEY=(str, ''),
    LANGCHAIN_TRACING_V2=(bool, False),
    LANGCHAIN_API_KEY=(str, ''),
    LANGCHAIN_PROJECT=(str, 'feedscraper-langchain'),
    REDIS_URL=(str, 'redis://localhost:6379/0'),
)

# Ler arquivo .env
environ.Env.read_env(BASE_DIR / '.env')

# Security
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'django_apscheduler',
    'rest_framework',
    'corsheaders',
]

LOCAL_APPS = [
    'core',
    'apps.jobs',
    'apps.langchain_integration',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Database
DATABASES = {
    'default': env.db()  # Usa DATABASE_URL automaticamente
}

# Alternativa para configuração manual:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': env('DB_NAME'),
#         'USER': env('DB_USER'),
#         'PASSWORD': env('DB_PASSWORD'),
#         'HOST': env('DB_HOST', default='localhost'),
#         'PORT': env('DB_PORT', default='5432'),
#     }
# }

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# APScheduler Configuration
SCHEDULER_CONFIG = {
    'apscheduler.jobstores.default': {
        'type': 'sqlalchemy',
        'url': env('DATABASE_URL')  # Usa a mesma URL do banco
    },
    'apscheduler.executors.default': {
        'type': 'threadpool',
        'max_workers': env.int('SCHEDULER_MAX_WORKERS', default=10),
    },
    'apscheduler.executors.processpool': {
        'type': 'processpool',
        'max_workers': env.int('SCHEDULER_PROCESS_WORKERS', default=5),
    },
    'apscheduler.job_defaults.coalesce': 'false',
    'apscheduler.job_defaults.max_instances': '3',
    'apscheduler.timezone': TIME_ZONE,
}

# LangChain Configuration
LANGCHAIN_CONFIG = {
    'OPENAI_API_KEY': env('OPENAI_API_KEY'),
    'DEFAULT_TEMPERATURE': env.float('LANGCHAIN_TEMPERATURE', default=0.7),
    'DEFAULT_MODEL': env('LANGCHAIN_MODEL', default='gpt-4-turbo-preview'),
    'MAX_TOKENS': env.int('LANGCHAIN_MAX_TOKENS', default=4096),
    'TIMEOUT': env.int('LANGCHAIN_TIMEOUT', default=30),
}

# LangSmith Configuration (Optional - for monitoring and debugging)
if env.bool('LANGCHAIN_TRACING_V2', default=False):
    LANGCHAIN_CONFIG.update({
        'LANGCHAIN_TRACING_V2': True,
        'LANGCHAIN_API_KEY': env('LANGCHAIN_API_KEY'),
        'LANGCHAIN_PROJECT': env('LANGCHAIN_PROJECT', default='feedscraper-langchain'),
        'LANGCHAIN_ENDPOINT': env('LANGCHAIN_ENDPOINT', default='https://api.smith.langchain.com'),
    })

# Set environment variables for LangChain
os.environ.update({key: str(value) for key, value in LANGCHAIN_CONFIG.items()})

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'formatter': 'verbose'
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apscheduler': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'langchain': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

---

## 🤖 Integração LangChain

### Service Layer Pattern

```python
# apps/langchain_integration/services/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from django.conf import settings

class BaseLangChainService(ABC):
    """Base service class for LangChain operations."""
    
    def __init__(self, model_name: Optional[str] = None, temperature: Optional[float] = None):
        self.model_name = model_name or settings.LANGCHAIN_CONFIG['DEFAULT_MODEL']
        self.temperature = temperature or settings.LANGCHAIN_CONFIG['DEFAULT_TEMPERATURE']
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the language model."""
        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=settings.LANGCHAIN_CONFIG['MAX_TOKENS'],
            timeout=settings.LANGCHAIN_CONFIG['TIMEOUT'],
        )
    
    @abstractmethod
    def build_chain(self) -> Runnable:
        """Build and return the LangChain chain."""
        pass
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data through the chain."""
        pass

# apps/langchain_integration/services/text_processor.py
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .base import BaseLangChainService

class TextProcessorService(BaseLangChainService):
    """Service for text processing using LangChain."""
    
    def __init__(self, template: str = None):
        super().__init__()
        self.template = template or "Process the following text: {text}"
    
    def build_chain(self):
        """Build the text processing chain."""
        prompt = ChatPromptTemplate.from_template(self.template)
        output_parser = StrOutputParser()
        return prompt | self.llm | output_parser
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process text input."""
        try:
            chain = self.build_chain()
            result = chain.invoke(input_data)
            return {
                'success': True,
                'result': result,
                'input': input_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input': input_data
            }
```

### Repository Pattern para LangChain

```python
# apps/langchain_integration/repositories/prompt_repository.py
from typing import Dict, List, Optional
from django.core.cache import cache
from core.models.base import BaseModel

class PromptRepository:
    """Repository for managing prompts."""
    
    CACHE_PREFIX = "prompt_"
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def get_prompt_by_key(key: str) -> Optional[str]:
        """Get prompt by key from cache or database."""
        cache_key = f"{PromptRepository.CACHE_PREFIX}{key}"
        prompt = cache.get(cache_key)
        
        if not prompt:
            # Implementar busca no banco de dados
            # prompt = PromptModel.objects.get(key=key).template
            cache.set(cache_key, prompt, PromptRepository.CACHE_TIMEOUT)
        
        return prompt
    
    @staticmethod
    def save_prompt(key: str, template: str, metadata: Dict = None) -> bool:
        """Save prompt to database and cache."""
        try:
            # Implementar salvamento no banco
            cache_key = f"{PromptRepository.CACHE_PREFIX}{key}"
            cache.set(cache_key, template, PromptRepository.CACHE_TIMEOUT)
            return True
        except Exception:
            return False
```

---

## ⏰ Sistema de Jobs Agendados

### Job Scheduler Service

```python
# apps/jobs/schedulers.py
import logging
from typing import Callable, Dict, Any
from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from django.conf import settings

logger = logging.getLogger(__name__)

class JobSchedulerService:
    """Service for managing scheduled jobs."""
    
    _scheduler = None
    
    @classmethod
    def get_scheduler(cls):
        """Get or create scheduler instance."""
        if cls._scheduler is None:
            cls._scheduler = cls._create_scheduler()
        return cls._scheduler
    
    @classmethod
    def _create_scheduler(cls):
        """Create and configure scheduler."""
        jobstores = {
            'default': DjangoJobStore()
        }
        
        executors = {
            'default': ThreadPoolExecutor(max_workers=10),
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=settings.TIME_ZONE
        )
        
        return scheduler
    
    @classmethod
    def start(cls):
        """Start the scheduler."""
        scheduler = cls.get_scheduler()
        if not scheduler.running:
            scheduler.start()
            logger.info("Job scheduler started")
    
    @classmethod
    def shutdown(cls):
        """Shutdown the scheduler."""
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown()
            logger.info("Job scheduler shutdown")
    
    @classmethod
    def add_job(
        cls, 
        func: Callable, 
        trigger: str, 
        job_id: str,
        **kwargs
    ):
        """Add a job to the scheduler."""
        scheduler = cls.get_scheduler()
        try:
            scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                **kwargs
            )
            logger.info(f"Job {job_id} added successfully")
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {str(e)}")
            raise
    
    @classmethod
    def remove_job(cls, job_id: str):
        """Remove a job from the scheduler."""
        scheduler = cls.get_scheduler()
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} removed successfully")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {str(e)}")
```

### Task Definitions

```python
# apps/jobs/tasks.py
import logging
from typing import Dict, Any
from django.utils import timezone
from apps.langchain_integration.services.text_processor import TextProcessorService

logger = logging.getLogger(__name__)

def process_text_job(text: str, template: str = None) -> Dict[str, Any]:
    """
    Job task for processing text using LangChain.
    
    Args:
        text: The text to process
        template: Optional template for processing
        
    Returns:
        Dict containing result and metadata
    """
    start_time = timezone.now()
    
    try:
        logger.info(f"Starting text processing job at {start_time}")
        
        # Initialize service
        service = TextProcessorService(template=template)
        
        # Process text
        result = service.process({'text': text})
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Text processing completed in {duration}s")
        
        return {
            'success': result['success'],
            'result': result.get('result'),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'error': result.get('error')
        }
        
    except Exception as e:
        logger.error(f"Error in text processing job: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'start_time': start_time.isoformat(),
            'end_time': timezone.now().isoformat()
        }

def langchain_batch_job():
    """
    Batch job for processing multiple items with LangChain.
    """
    logger.info("Starting LangChain batch job")
    
    try:
        # Implementar lógica de processamento em lote
        # Exemplo: buscar itens pendentes do banco de dados
        # processar usando LangChain
        # salvar resultados
        
        pass
        
    except Exception as e:
        logger.error(f"Error in batch job: {str(e)}")
        raise
```

---

## 🗄️ Models e Repository Pattern

### Base Models

```python
# core/models/base.py
from django.db import models
from django.utils import timezone
import uuid

class BaseModel(models.Model):
    """Base model with common fields."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']

class BaseRepository:
    """Base repository pattern implementation."""
    
    def __init__(self, model_class):
        self.model = model_class
    
    def get_by_id(self, obj_id):
        """Get object by ID."""
        try:
            return self.model.objects.get(id=obj_id, is_active=True)
        except self.model.DoesNotExist:
            return None
    
    def get_all_active(self):
        """Get all active objects."""
        return self.model.objects.filter(is_active=True)
    
    def create(self, **kwargs):
        """Create new object."""
        return self.model.objects.create(**kwargs)
    
    def update(self, obj_id, **kwargs):
        """Update object."""
        obj = self.get_by_id(obj_id)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            obj.save()
        return obj
    
    def soft_delete(self, obj_id):
        """Soft delete object."""
        obj = self.get_by_id(obj_id)
        if obj:
            obj.is_active = False
            obj.save()
        return obj
```

### Job Models

```python
# apps/jobs/models.py
from django.db import models
from core.models.base import BaseModel
import json

class JobExecutionLog(BaseModel):
    """Model for logging job executions."""
    
    JOB_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]
    
    job_id = models.CharField(max_length=255)
    job_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='PENDING')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    parameters = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.job_name} - {self.status}"
    
    @property
    def duration(self):
        """Calculate job duration."""
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return None

class LangChainPrompt(BaseModel):
    """Model for storing LangChain prompts."""
    
    key = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    template = models.TextField()
    description = models.TextField(blank=True)
    variables = models.JSONField(default=list)  # Lista de variáveis no template
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.key})"
```

---

## 🧪 Testes - Padrão AAA (Arrange, Act, Assert)

### Test Base Classes

```python
# tests/base.py
from django.test import TestCase
from django.test.utils import override_settings
from unittest.mock import Mock, patch
from apps.jobs.schedulers import JobSchedulerService

class BaseTestCase(TestCase):
    """Base test case with common utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.scheduler = JobSchedulerService.get_scheduler()
    
    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()
        if hasattr(self, 'scheduler') and self.scheduler.running:
            self.scheduler.shutdown()

@override_settings(
    LANGCHAIN_CONFIG={
        'OPENAI_API_KEY': 'test-key',
        'DEFAULT_MODEL': 'gpt-3.5-turbo',
        'DEFAULT_TEMPERATURE': 0.7,
        'MAX_TOKENS': 1000,
        'TIMEOUT': 10,
    }
)
class LangChainTestCase(BaseTestCase):
    """Base test case for LangChain tests."""
    
    def setUp(self):
        super().setUp()
        self.mock_llm_patcher = patch('langchain_openai.ChatOpenAI')
        self.mock_llm = self.mock_llm_patcher.start()
        self.mock_llm.return_value.invoke.return_value = Mock(content="Test response")
    
    def tearDown(self):
        self.mock_llm_patcher.stop()
        super().tearDown()
```

### Unit Tests Examples

```python
# apps/langchain_integration/tests/test_services.py
from unittest.mock import patch, MagicMock
from tests.base import LangChainTestCase
from apps.langchain_integration.services.text_processor import TextProcessorService

class TestTextProcessorService(LangChainTestCase):
    """Unit tests for TextProcessorService."""
    
    def test_process_success(self):
        """Test successful text processing."""
        # Arrange
        service = TextProcessorService()
        input_data = {'text': 'Test input'}
        expected_result = 'Processed text'
        
        with patch.object(service, 'build_chain') as mock_chain:
            mock_chain.return_value.invoke.return_value = expected_result
            
            # Act
            result = service.process(input_data)
            
            # Assert
            self.assertTrue(result['success'])
            self.assertEqual(result['result'], expected_result)
            self.assertEqual(result['input'], input_data)
            mock_chain.return_value.invoke.assert_called_once_with(input_data)
    
    def test_process_error_handling(self):
        """Test error handling in text processing."""
        # Arrange
        service = TextProcessorService()
        input_data = {'text': 'Test input'}
        error_message = 'Processing error'
        
        with patch.object(service, 'build_chain') as mock_chain:
            mock_chain.return_value.invoke.side_effect = Exception(error_message)
            
            # Act
            result = service.process(input_data)
            
            # Assert
            self.assertFalse(result['success'])
            self.assertEqual(result['error'], error_message)
            self.assertEqual(result['input'], input_data)
    
    def test_build_chain_structure(self):
        """Test that the chain is built correctly."""
        # Arrange
        service = TextProcessorService(template="Custom template: {text}")
        
        # Act
        chain = service.build_chain()
        
        # Assert
        self.assertIsNotNone(chain)
        # Verificar se a chain tem os componentes esperados

# apps/jobs/tests/test_tasks.py
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.jobs.tasks import process_text_job

class TestJobTasks(TestCase):
    """Unit tests for job tasks."""
    
    @patch('apps.jobs.tasks.TextProcessorService')
    def test_process_text_job_success(self, mock_service_class):
        """Test successful text processing job."""
        # Arrange
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.process.return_value = {
            'success': True,
            'result': 'Processed text'
        }
        
        text = "Test text"
        template = "Test template"
        
        # Act
        result = process_text_job(text, template)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], 'Processed text')
        self.assertIn('start_time', result)
        self.assertIn('end_time', result)
        self.assertIn('duration_seconds', result)
        
        mock_service_class.assert_called_once_with(template=template)
        mock_service.process.assert_called_once_with({'text': text})
    
    @patch('apps.jobs.tasks.TextProcessorService')
    def test_process_text_job_error(self, mock_service_class):
        """Test error handling in text processing job."""
        # Arrange
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.process.side_effect = Exception("Service error")
        
        text = "Test text"
        
        # Act
        result = process_text_job(text)
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('Service error', result['error'])
        self.assertIn('start_time', result)
        self.assertIn('end_time', result)
```

### Integration Tests

```python
# tests/integration/test_scheduler_integration.py
from django.test import TransactionTestCase
from django.test.utils import override_settings
from unittest.mock import patch
import time
from apps.jobs.schedulers import JobSchedulerService

class TestSchedulerIntegration(TransactionTestCase):
    """Integration tests for job scheduler."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        super().setUp()
        self.scheduler_service = JobSchedulerService
    
    def tearDown(self):
        """Clean up after integration tests."""
        self.scheduler_service.shutdown()
        super().tearDown()
    
    def test_scheduler_lifecycle(self):
        """Test complete scheduler lifecycle."""
        # Arrange
        scheduler = self.scheduler_service.get_scheduler()
        
        # Act - Start scheduler
        self.scheduler_service.start()
        
        # Assert
        self.assertTrue(scheduler.running)
        
        # Act - Add job
        job_executed = []
        
        def test_job():
            job_executed.append(True)
        
        self.scheduler_service.add_job(
            func=test_job,
            trigger='date',
            job_id='test_job',
            run_date=time.time() + 1  # Execute in 1 second
        )
        
        # Wait for job execution
        time.sleep(2)
        
        # Assert
        self.assertTrue(job_executed)
        
        # Act - Shutdown
        self.scheduler_service.shutdown()
        
        # Assert
        self.assertFalse(scheduler.running)

# tests/integration/test_langchain_job_integration.py
from django.test import TransactionTestCase
from unittest.mock import patch
from apps.jobs.tasks import process_text_job
from apps.jobs.schedulers import JobSchedulerService

class TestLangChainJobIntegration(TransactionTestCase):
    """Integration tests for LangChain job processing."""
    
    @patch('apps.langchain_integration.services.text_processor.ChatOpenAI')
    def test_end_to_end_text_processing_job(self, mock_chat_openai):
        """Test end-to-end text processing through job system."""
        # Arrange
        mock_llm = mock_chat_openai.return_value
        mock_llm.invoke.return_value.content = "Processed: Test text"
        
        # Act
        result = process_text_job("Test text", "Process: {text}")
        
        # Assert
        self.assertTrue(result['success'])
        self.assertIn('Processed: Test text', result['result'])
        self.assertIsNotNone(result['duration_seconds'])
        
        # Verify LangChain was called
        mock_chat_openai.assert_called_once()
```

---

## � Organização e Separação de Testes Django

### 🧪 Estrutura Recomendada de Testes

#### Organização por Tipo de Teste

```
tests/
├── __init__.py
├── unit/                    # Testes Unitários (isolados)
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_utils.py
│   └── test_tasks.py
├── integration/             # Testes de Integração (componentes)
│   ├── __init__.py
│   ├── test_api_views.py
│   ├── test_scheduler.py
│   └── test_langchain_flows.py
├── functional/              # Testes Funcionais (end-to-end)
│   ├── __init__.py
│   ├── test_workflows.py
│   └── test_user_journeys.py
├── fixtures/                # Dados para testes
│   ├── test_data.json
│   └── sample_files/
├── mocks/                   # Mocks e factories
│   ├── __init__.py
│   ├── factories.py
│   └── mock_services.py
└── conftest.py             # Configurações do pytest (se usado)
```

### 🔬 Testes Unitários - Django TestCase

#### Características dos Testes Unitários:
- **Isolados**: Testam uma única unidade de código
- **Rápidos**: Executam em milissegundos
- **Não dependem**: De banco de dados real, APIs externas, sistema de arquivos
- **Mocking**: Usam mocks para dependências externas

```python
# tests/unit/test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import Mock, patch
from apps.jobs.models import JobExecution

class JobExecutionModelTest(TestCase):
    """Testes unitários para o modelo JobExecution."""
    
    def test_job_execution_str_representation(self):
        """Testa a representação string do modelo."""
        # Arrange
        job = JobExecution(
            job_id='test-job',
            status='completed',
            result={'success': True}
        )
        
        # Act
        str_repr = str(job)
        
        # Assert
        self.assertEqual(str_repr, 'test-job - completed')
    
    def test_duration_property(self):
        """Testa o cálculo da propriedade duration."""
        from datetime import datetime, timedelta
        
        # Arrange
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=10)
        
        job = JobExecution(
            job_id='test-job',
            start_time=start_time,
            end_time=end_time
        )
        
        # Act & Assert
        self.assertEqual(job.duration, timedelta(seconds=10))
    
    def test_validation_error_for_invalid_status(self):
        """Testa validação de status inválido."""
        # Arrange
        job = JobExecution(
            job_id='test-job',
            status='invalid_status'
        )
        
        # Act & Assert
        with self.assertRaises(ValidationError):
            job.full_clean()


# tests/unit/test_services.py
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from apps.langchain_integration.services.text_processor import TextProcessorService

class TextProcessorServiceTest(TestCase):
    """Testes unitários para TextProcessorService."""
    
    @patch('apps.langchain_integration.services.text_processor.ChatOpenAI')
    def test_build_chain_creates_correct_components(self, mock_chat_openai):
        """Testa se a chain é construída corretamente."""
        # Arrange
        service = TextProcessorService(template="Process: {text}")
        
        # Act
        chain = service.build_chain()
        
        # Assert
        self.assertIsNotNone(chain)
        mock_chat_openai.assert_called_once()
    
    @patch('apps.langchain_integration.services.text_processor.ChatOpenAI')
    def test_process_handles_chain_exception(self, mock_chat_openai):
        """Testa tratamento de exceção na chain."""
        # Arrange
        service = TextProcessorService()
        mock_chat_openai.return_value.invoke.side_effect = Exception("Chain error")
        
        input_data = {'text': 'test'}
        
        # Act
        result = service.process(input_data)
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('Chain error', result['error'])
        self.assertEqual(result['input'], input_data)


# tests/unit/test_utils.py
from django.test import SimpleTestCase  # SimpleTestCase para utilitários sem DB
from unittest.mock import patch, mock_open
from core.utils.logging import setup_logger

class LoggingUtilsTest(SimpleTestCase):
    """Testes unitários para utilitários de logging."""
    
    @patch('core.utils.logging.logging.getLogger')
    def test_setup_logger_with_default_config(self, mock_get_logger):
        """Testa configuração padrão do logger."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Act
        logger = setup_logger('test_logger')
        
        # Assert
        self.assertEqual(logger, mock_logger)
        mock_get_logger.assert_called_once_with('test_logger')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('core.utils.logging.os.path.exists')
    def test_setup_logger_creates_log_directory(self, mock_exists, mock_file):
        """Testa criação de diretório de logs."""
        # Arrange
        mock_exists.return_value = False
        
        # Act
        setup_logger('test_logger', log_file='logs/test.log')
        
        # Assert
        mock_exists.assert_called()
```

### 🔧 Testes de Integração - Django TransactionTestCase

#### Características dos Testes de Integração:
- **Múltiplos componentes**: Testam interação entre partes do sistema
- **Banco de dados real**: Usam transações reais quando necessário
- **APIs externas mockadas**: Mantêm controle sobre dependências externas
- **Fluxos completos**: Testam workflows end-to-end

```python
# tests/integration/test_scheduler_integration.py
from django.test import TransactionTestCase
from django.test.utils import override_settings
from unittest.mock import patch, Mock
import time
import threading
from apps.jobs.schedulers import JobSchedulerService
from apps.jobs.models import JobExecution

@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
class SchedulerIntegrationTest(TransactionTestCase):
    """Testes de integração para o sistema de agendamento."""
    
    def setUp(self):
        """Configuração para testes de integração."""
        self.scheduler_service = JobSchedulerService()
    
    def tearDown(self):
        """Limpeza após testes de integração."""
        if hasattr(self, 'scheduler_service'):
            self.scheduler_service.shutdown()
    
    @patch('apps.jobs.tasks.TextProcessorService')
    def test_job_execution_flow_with_database_persistence(self, mock_service):
        """Testa fluxo completo de execução de job com persistência."""
        # Arrange
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.process.return_value = {
            'success': True,
            'result': 'Processed text'
        }
        
        # Act
        scheduler = self.scheduler_service.get_scheduler()
        job_id = 'integration_test_job'
        
        # Adiciona job ao scheduler
        job = scheduler.add_job(
            func='apps.jobs.tasks.process_text_job',
            args=['test text', 'template'],
            trigger='date',
            id=job_id
        )
        
        # Inicia scheduler e aguarda execução
        scheduler.start()
        time.sleep(2)  # Aguarda execução
        
        # Assert
        # Verifica se o job foi persistido no banco
        job_execution = JobExecution.objects.filter(job_id=job_id).first()
        self.assertIsNotNone(job_execution)
        self.assertEqual(job_execution.status, 'completed')
    
    def test_concurrent_job_execution(self):
        """Testa execução concorrente de múltiplos jobs."""
        # Arrange
        scheduler = self.scheduler_service.get_scheduler()
        executed_jobs = []
        
        def test_job(job_name):
            executed_jobs.append(job_name)
            time.sleep(0.1)  # Simula processamento
        
        # Act
        scheduler.start()
        
        # Adiciona múltiplos jobs
        for i in range(5):
            scheduler.add_job(
                func=test_job,
                args=[f'job_{i}'],
                trigger='date',
                id=f'concurrent_job_{i}'
            )
        
        # Aguarda execução de todos os jobs
        time.sleep(2)
        
        # Assert
        self.assertEqual(len(executed_jobs), 5)
        self.assertTrue(all(f'job_{i}' in executed_jobs for i in range(5)))


# tests/integration/test_langchain_job_integration.py
from django.test import TransactionTestCase
from django.test.utils import override_settings
from unittest.mock import patch, Mock
from apps.jobs.tasks import process_text_job
from apps.langchain_integration.models import ProcessingResult

class LangChainJobIntegrationTest(TransactionTestCase):
    """Testes de integração entre LangChain e sistema de jobs."""
    
    @override_settings(
        LANGCHAIN_CONFIG={
            'OPENAI_API_KEY': 'test-key',
            'DEFAULT_MODEL': 'gpt-3.5-turbo',
            'DEFAULT_TEMPERATURE': 0.7,
        }
    )
    @patch('langchain_openai.ChatOpenAI')
    def test_full_text_processing_workflow(self, mock_chat_openai):
        """Testa workflow completo de processamento de texto."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_response = Mock()
        mock_response.content = "Texto processado com sucesso"
        mock_llm.invoke.return_value = mock_response
        
        input_text = "Texto para processar"
        template = "Processe este texto: {text}"
        
        # Act
        result = process_text_job(input_text, template)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertIn('Texto processado com sucesso', result['result'])
        
        # Verifica se o resultado foi persistido (se aplicável)
        # processing_results = ProcessingResult.objects.filter(
        #     input_text=input_text
        # )
        # self.assertTrue(processing_results.exists())
    
    @patch('langchain_openai.ChatOpenAI')
    def test_error_handling_in_integration_flow(self, mock_chat_openai):
        """Testa tratamento de erros no fluxo de integração."""
        # Arrange
        mock_chat_openai.side_effect = Exception("API Error")
        
        # Act
        result = process_text_job("test text")
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('API Error', result['error'])
```

### 🎯 Melhores Práticas para Separação de Testes

#### 1. **Nomenclatura e Organização**

```python
# Convenções de nomenclatura
class TestNomeDoComponente(TestCase):           # Testes unitários
class NomeDoComponenteIntegrationTest(TransactionTestCase):  # Testes de integração
class NomeDoWorkflowE2ETest(LiveServerTestCase):            # Testes funcionais

# Métodos de teste
def test_should_return_success_when_valid_input(self):      # Unitário
def test_integration_between_scheduler_and_database(self):  # Integração
def test_complete_user_workflow_from_api_to_result(self):   # Funcional
```

#### 2. **Tags para Seleção de Testes**

```python
# tests/unit/test_models.py
from django.test import TestCase, tag

@tag('unit', 'models', 'fast')
class JobModelTest(TestCase):
    """Testes unitários rápidos para modelos."""
    pass

@tag('integration', 'scheduler', 'slow')
class SchedulerIntegrationTest(TransactionTestCase):
    """Testes de integração mais lentos."""
    pass

@tag('e2e', 'api', 'slow')
class APIWorkflowTest(LiveServerTestCase):
    """Testes end-to-end completos."""
    pass
```

#### 3. **Comandos para Executar Testes por Categoria**

```bash
# Executar apenas testes unitários (rápidos)
python manage.py test --tag=unit

# Executar testes de integração
python manage.py test --tag=integration

# Executar testes end-to-end
python manage.py test --tag=e2e

# Executar testes rápidos (unitários + alguns de integração)
python manage.py test --tag=fast

# Executar todos exceto os lentos
python manage.py test --exclude-tag=slow

# Executar testes específicos por app
python manage.py test apps.jobs.tests.unit
python manage.py test apps.langchain_integration.tests.integration

# Executar com coverage
coverage run --source='.' manage.py test --tag=unit
coverage run --append --source='.' manage.py test --tag=integration
coverage report -m
coverage html
```

#### 4. **Factories para Criação de Dados de Teste**

```python
# tests/mocks/factories.py
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText, FuzzyChoice
from django.utils import timezone
from apps.jobs.models import JobExecution

class JobExecutionFactory(DjangoModelFactory):
    """Factory para criar instâncias de JobExecution."""
    
    class Meta:
        model = JobExecution
    
    job_id = factory.Sequence(lambda n: f"test-job-{n}")
    status = FuzzyChoice(['pending', 'running', 'completed', 'failed'])
    start_time = factory.LazyFunction(timezone.now)
    end_time = factory.LazyFunction(timezone.now)
    result = factory.Dict({
        'success': True,
        'message': factory.Faker('sentence'),
        'data': factory.Dict({
            'processed_items': factory.Faker('random_int', min=1, max=100),
            'duration': factory.Faker('random_int', min=1, max=3600)
        })
    })
    
    @factory.post_generation
    def set_end_time_after_start(obj, create, extracted, **kwargs):
        """Garante que end_time é posterior ao start_time."""
        if create and obj.start_time:
            from datetime import timedelta
            obj.end_time = obj.start_time + timedelta(seconds=30)
            obj.save()

# Uso nas tests
class JobModelIntegrationTest(TransactionTestCase):
    def test_job_execution_with_factory(self):
        # Arrange
        job = JobExecutionFactory(status='completed')
        
        # Act & Assert
        self.assertEqual(job.status, 'completed')
        self.assertTrue(job.end_time > job.start_time)
```

#### 5. **Configurações de Teste Específicas**

```python
# config/settings/testing.py
from .base import *

# Banco de dados mais rápido para testes
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Desabilitar migrações desnecessárias
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

# Apenas para testes rápidos - cuidado com testes que dependem de migrações
MIGRATION_MODULES = DisableMigrations()

# Configurações específicas para testes
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # Mais rápido para testes
]

# Desabilitar logs desnecessários em testes
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
        },
    },
}

# Cache em memória para testes
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Configurações LangChain para testes
LANGCHAIN_CONFIG = {
    'OPENAI_API_KEY': 'test-key-not-real',
    'DEFAULT_MODEL': 'gpt-3.5-turbo',
    'DEFAULT_TEMPERATURE': 0.0,  # Determinístico para testes
    'MAX_TOKENS': 100,  # Limitar para testes
    'TIMEOUT': 5,  # Timeout mais curto
}
```

#### 6. **CI/CD Pipeline para Testes**

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
        django-version: [4.2, 5.0]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements/testing.txt
        pip install Django==${{ matrix.django-version }}
    
    - name: Run unit tests
      run: |
        coverage run --source='.' manage.py test --tag=unit --settings=config.settings.testing
    
    - name: Run integration tests
      run: |
        coverage run --append --source='.' manage.py test --tag=integration --settings=config.settings.testing
    
    - name: Generate coverage report
      run: |
        coverage report -m
        coverage xml
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 📈 Métricas e Cobertura de Testes

```python
# pytest.ini (se usar pytest)
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
python_files = tests.py test_*.py *_tests.py
addopts = 
    --cov=apps
    --cov=core
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=90
    --maxfail=5
    --tb=short
markers =
    unit: marks tests as unit tests
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    slow: marks tests as slow
    fast: marks tests as fast
```

---

## �🔒 Boas Práticas de Segurança

### Environment Variables (.env)

```bash
# .env.example

# Django Configuration
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
# Para desenvolvimento (SQLite)
DATABASE_URL=sqlite:///db.sqlite3

# Para produção (PostgreSQL)
# DATABASE_URL=postgresql://user:password@host:port/database

# LangChain Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: LangSmith for monitoring and debugging
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your-langsmith-api-key-here
# LANGCHAIN_PROJECT=feedscraper-langchain
# LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# LangChain Settings
LANGCHAIN_TEMPERATURE=0.7
LANGCHAIN_MODEL=gpt-4-turbo-preview
LANGCHAIN_MAX_TOKENS=4096
LANGCHAIN_TIMEOUT=30

# APScheduler Configuration
SCHEDULER_MAX_WORKERS=10
SCHEDULER_PROCESS_WORKERS=5

# Redis Configuration (for production job store)
REDIS_URL=redis://localhost:6379/0

# Email Configuration (for production)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000

# Logging
LOG_LEVEL=INFO

# Security (production only)
SECURE_SSL_REDIRECT=false
SECURE_HSTS_SECONDS=0
```

### Security Middleware

```python
# core/middleware/security.py
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

class JobSecurityMiddleware(MiddlewareMixin):
    """Middleware for job-related security checks."""
    
    def process_request(self, request):
        """Process incoming requests for security checks."""
        if request.path.startswith('/admin/jobs/'):
            # Implementar verificações de segurança para admin de jobs
            pass
        
        return None
    
    def process_exception(self, request, exception):
        """Handle security-related exceptions."""
        if isinstance(exception, PermissionDenied):
            logger.warning(f"Permission denied for user {request.user} on {request.path}")
        
        return None
```

---

## 📊 Monitoramento e Logging

### Custom Logging Handler

```python
# core/utils/logging.py
import logging
from django.db import transaction
from apps.jobs.models import JobExecutionLog

class DatabaseLogHandler(logging.Handler):
    """Custom log handler for database logging."""
    
    def emit(self, record):
        """Emit log record to database."""
        try:
            if hasattr(record, 'job_id'):
                with transaction.atomic():
                    # Implementar logging personalizado para jobs
                    pass
        except Exception:
            # Não deve quebrar a aplicação se logging falhar
            pass

class JobMetricsCollector:
    """Collector for job execution metrics."""
    
    @staticmethod
    def record_job_execution(job_id: str, duration: float, status: str):
        """Record job execution metrics."""
        try:
            JobExecutionLog.objects.create(
                job_id=job_id,
                duration_seconds=duration,
                status=status
            )
        except Exception as e:
            logger.error(f"Failed to record job metrics: {str(e)}")
```

---

## 🚀 Deployment e Production

### Production Settings

```python
# config/settings/production.py
from .base import *
import dj_database_url

DEBUG = False

# Database
DATABASES['default'] = dj_database_url.parse(get_env_variable('DATABASE_URL'))

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# APScheduler for production
SCHEDULER_CONFIG.update({
    'apscheduler.jobstores.default': {
        'type': 'redis',
        'url': get_env_variable('REDIS_URL'),
    },
})

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 86400
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/ requirements/
RUN pip install -r requirements/production.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations and start services
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

---

## 📋 Design Patterns Recomendados

### 1. Factory Pattern para LangChain Chains

```python
# apps/langchain_integration/factories/chain_factory.py
from enum import Enum
from typing import Dict, Any
from langchain_core.runnables import Runnable

class ChainType(Enum):
    TEXT_PROCESSOR = "text_processor"
    SUMMARIZER = "summarizer"
    QA_CHAIN = "qa_chain"

class ChainFactory:
    """Factory for creating different types of LangChain chains."""
    
    @staticmethod
    def create_chain(chain_type: ChainType, **kwargs) -> Runnable:
        """Create chain based on type."""
        if chain_type == ChainType.TEXT_PROCESSOR:
            from apps.langchain_integration.services.text_processor import TextProcessorService
            service = TextProcessorService(**kwargs)
            return service.build_chain()
        
        elif chain_type == ChainType.SUMMARIZER:
            # Implementar outros tipos de chains
            pass
        
        else:
            raise ValueError(f"Unknown chain type: {chain_type}")
```

### 2. Observer Pattern para Job Events

```python
# apps/jobs/observers.py
from abc import ABC, abstractmethod
from typing import List

class JobEventObserver(ABC):
    """Base observer for job events."""
    
    @abstractmethod
    def on_job_started(self, job_id: str, **kwargs):
        pass
    
    @abstractmethod
    def on_job_completed(self, job_id: str, result: Dict, **kwargs):
        pass
    
    @abstractmethod
    def on_job_failed(self, job_id: str, error: str, **kwargs):
        pass

class JobEventPublisher:
    """Publisher for job events."""
    
    def __init__(self):
        self._observers: List[JobEventObserver] = []
    
    def add_observer(self, observer: JobEventObserver):
        self._observers.append(observer)
    
    def remove_observer(self, observer: JobEventObserver):
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_job_started(self, job_id: str, **kwargs):
        for observer in self._observers:
            observer.on_job_started(job_id, **kwargs)
    
    def notify_job_completed(self, job_id: str, result: Dict, **kwargs):
        for observer in self._observers:
            observer.on_job_completed(job_id, result, **kwargs)
    
    def notify_job_failed(self, job_id: str, error: str, **kwargs):
        for observer in self._observers:
            observer.on_job_failed(job_id, error, **kwargs)
```

---

## 🎯 Checklist de Implementação

### ✅ Setup Inicial
- [ ] Configurar estrutura de diretórios
- [ ] Configurar settings por ambiente
- [ ] Configurar variáveis de ambiente
- [ ] Instalar e configurar django-apscheduler
- [ ] Instalar e configurar LangChain

### ✅ Arquitetura
- [ ] Implementar modelos base
- [ ] Implementar repository pattern
- [ ] Implementar service layer para LangChain
- [ ] Configurar sistema de jobs quando necessário
- [ ] Implementar observers para eventos

### ✅ Testes
- [ ] Configurar estrutura de testes (unit/integration/functional)
- [ ] Implementar base classes de teste (BaseTestCase, LangChainTestCase)
- [ ] Criar factories para dados de teste (factory_boy)
- [ ] Implementar testes unitários com mocking apropriado
  - [ ] Testes de modelos (Django TestCase)
  - [ ] Testes de services (mocking de dependências externas)
  - [ ] Testes de utils (SimpleTestCase para código sem DB)
- [ ] Implementar testes de integração
  - [ ] Fluxos entre múltiplos componentes (TransactionTestCase)
  - [ ] Testes de scheduler com persistência
  - [ ] Integrações LangChain + Jobs + Database
- [ ] Configurar tags para categorização (@tag decorator)
- [ ] Implementar testes funcionais/E2E quando necessário
- [ ] Configurar coverage reports (meta: >90%)
- [ ] Configurar CI/CD pipeline para testes
- [ ] Criar configurações específicas para ambiente de teste

### ✅ Segurança
- [ ] Implementar middleware de segurança
- [ ] Configurar logging adequado
- [ ] Implementar validação de inputs
- [ ] Configurar rate limiting
- [ ] Implementar autenticação/autorização

### ✅ Monitoramento
- [ ] Configurar logging estruturado
- [ ] Implementar coleta de métricas
- [ ] Configurar alertas
- [ ] Implementar health checks
- [ ] Configurar dashboard de monitoramento

### ✅ Deploy
- [ ] Configurar Docker
- [ ] Configurar CI/CD
- [ ] Configurar ambiente de produção
- [ ] Implementar backup strategy
- [ ] Configurar monitoring em produção

---

## 📚 Referências e Recursos

### Documentação Oficial
- [Django Documentation](https://docs.djangoproject.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [django-apscheduler](https://github.com/jcass77/django-apscheduler)

### Boas Práticas
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [Clean Architecture in Python](https://github.com/cosmicpython/book)
- [Testing Best Practices](https://docs.python.org/3/library/unittest.html)

### Design Patterns
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)
- [Observer Pattern](https://refactoring.guru/design-patterns/observer)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

---

## � Exemplo de Uso

### Script de Demonstração (exemplo_uso.py)

Para facilitar o teste e demonstração das funcionalidades, recomenda-se criar um arquivo `exemplo_uso.py` na raiz do projeto:

```python
#!/usr/bin/env python
"""
Exemplo de uso do projeto Django + LangChain + Jobs

Este script demonstra como usar os services e agendar jobs.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.langchain_integration.services.text_processor import TextProcessorService, TextSummarizerService
from apps.jobs.schedulers import JobSchedulerService
from apps.jobs.tasks import process_text_job, summarize_text_job
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def exemplo_processamento_texto():
    """Exemplo de processamento de texto com LangChain."""
    logger.info("=== Exemplo: Processamento de Texto ===")
    
    service = TextProcessorService(
        template="Analise o seguinte texto e extraia os pontos principais: {text}"
    )
    
    texto = "Texto de exemplo para processamento..."
    resultado = service.process({'text': texto})
    
    if resultado['success']:
        logger.info(f"Resultado: {resultado['result']}")
    else:
        logger.error(f"Erro: {resultado['error']}")

def exemplo_job_agendado():
    """Exemplo de agendamento de job."""
    logger.info("=== Exemplo: Job Agendado ===")
    
    try:
        JobSchedulerService.start()
        
        # Agendar job para processar texto a cada 5 minutos
        JobSchedulerService.add_job(
            func='apps.jobs.tasks.process_text_job',  # Referência textual
            trigger='interval',
            job_id='exemplo_processamento',
            minutes=5,
            args=["Texto de exemplo", "Template de exemplo"]
        )
        
        jobs = JobSchedulerService.list_jobs()
        logger.info(f"Jobs agendados: {len(jobs)}")
        
    except Exception as e:
        logger.error(f"Erro ao agendar jobs: {str(e)}")

if __name__ == "__main__":
    exemplo_processamento_texto()
    exemplo_job_agendado()
```

### Comandos de Teste

```bash
# Executar exemplo de uso
python docs/exemplo_uso.py

# Testar configurações Django
python manage.py check

# Executar testes
python manage.py test

# Iniciar servidor de desenvolvimento
python manage.py runserver
```

---

## �📝 Notas Finais

Este PRP template serve como guia base para projetos Django + LangChain + Jobs agendados. Adapte conforme as necessidades específicas do seu projeto, mantendo sempre os princípios de arquitetura limpa, testabilidade e manutenibilidade.

### Próximos Passos
1. **Configurar ambiente**: Copiar `.env.example` para `.env` e configurar variáveis
2. **Executar exemplo**: Testar funcionalidades com `python exemplo_uso.py`
3. **Criar README.md**: Documentar instruções específicas do projeto
4. Personalizar configurações conforme necessidade
5. Implementar casos de uso específicos
6. Adicionar integrações adicionais
7. Configurar pipeline de deploy
8. Implementar monitoramento avançado

---

**Versão**: 1.1  
**Data**: 20 de setembro de 2025  
**Autor**: Sistema de IA  
**Licença**: MIT  
**Status**: Atualizado com implementação real
