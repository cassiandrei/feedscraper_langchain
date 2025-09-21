import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from django.conf import settings
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class BaseLangChainService(ABC):
    """Base service class for LangChain operations."""

    def __init__(
        self, model_name: Optional[str] = None, temperature: Optional[float] = None
    ):
        self.model_name = model_name or settings.LANGCHAIN_CONFIG["DEFAULT_MODEL"]
        self.temperature = (
            temperature or settings.LANGCHAIN_CONFIG["DEFAULT_TEMPERATURE"]
        )
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the language model."""
        try:
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=settings.LANGCHAIN_CONFIG["MAX_TOKENS"],
                timeout=settings.LANGCHAIN_CONFIG["TIMEOUT"],
                api_key=settings.LANGCHAIN_CONFIG["OPENAI_API_KEY"],
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            raise

    @abstractmethod
    def build_chain(self) -> Runnable:
        """Build and return the LangChain chain."""
        pass

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data through the chain."""
        pass

    def _handle_error(
        self, error: Exception, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle errors in a consistent way."""
        logger.error(f"LangChain processing error: {str(error)}")
        return {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "input": input_data,
        }
