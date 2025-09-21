"""
Base classes para testes do projeto.
"""

from unittest.mock import Mock, patch

from django.test import tag, TestCase, TransactionTestCase
from django.test.utils import override_settings


class BaseTestCase(TestCase):
    """Base test case with common utilities."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()

    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()


@override_settings(
    LANGCHAIN_CONFIG={
        "OPENAI_API_KEY": "test-key",
        "DEFAULT_MODEL": "gpt-3.5-turbo",
        "DEFAULT_TEMPERATURE": 0.0,
        "MAX_TOKENS": 100,
        "TIMEOUT": 5,
    }
)
class LangChainTestCase(BaseTestCase):
    """Base test case for LangChain tests."""

    def setUp(self):
        super().setUp()
        self.mock_llm_patcher = patch("langchain_openai.ChatOpenAI")
        self.mock_llm = self.mock_llm_patcher.start()
        self.mock_llm.return_value.invoke.return_value = Mock(content="Test response")

    def tearDown(self):
        self.mock_llm_patcher.stop()
        super().tearDown()


class BaseIntegrationTestCase(TransactionTestCase):
    """Base test case for integration tests."""

    def setUp(self):
        """Set up integration test fixtures."""
        super().setUp()

    def tearDown(self):
        """Clean up after integration tests."""
        super().tearDown()


@tag("unit", "fast")
class BaseUnitTestCase(BaseTestCase):
    """Base class for unit tests."""

    pass


@tag("integration", "slow")
class BaseIntegrationTest(BaseIntegrationTestCase):
    """Base class for integration tests."""

    pass
