import logging
from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .base import BaseLangChainService

logger = logging.getLogger(__name__)


class TextProcessorService(BaseLangChainService):
    """Service for text processing using LangChain."""

    def __init__(self, template: str = None, **kwargs):
        super().__init__(**kwargs)
        self.template = template or "Process the following text: {text}"

    def build_chain(self):
        """Build the text processing chain."""
        try:
            prompt = ChatPromptTemplate.from_template(self.template)
            output_parser = StrOutputParser()
            return prompt | self.llm | output_parser
        except Exception as e:
            logger.error(f"Failed to build text processing chain: {str(e)}")
            raise

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process text input."""
        try:
            logger.info(f"Processing text with template: {self.template}")
            chain = self.build_chain()
            result = chain.invoke(input_data)

            return {
                "success": True,
                "result": result,
                "input": input_data,
                "model_used": self.model_name,
                "template_used": self.template,
            }
        except Exception as e:
            return self._handle_error(e, input_data)

    def batch_process(self, inputs: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Process multiple texts in batch."""
        results = []
        for input_data in inputs:
            result = self.process(input_data)
            results.append(result)
        return results


class TextSummarizerService(BaseLangChainService):
    """Service for text summarization using LangChain."""

    def __init__(self, max_length: int = 150, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.template = f"""
        Summarize the following text in no more than {max_length} words. 
        Be concise and capture the main points:
        
        {{text}}
        
        Summary:
        """

    def build_chain(self):
        """Build the summarization chain."""
        try:
            prompt = ChatPromptTemplate.from_template(self.template)
            output_parser = StrOutputParser()
            return prompt | self.llm | output_parser
        except Exception as e:
            logger.error(f"Failed to build summarization chain: {str(e)}")
            raise

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize text input."""
        try:
            logger.info(f"Summarizing text with max length: {self.max_length}")
            chain = self.build_chain()
            result = chain.invoke(input_data)

            return {
                "success": True,
                "result": result,
                "input": input_data,
                "model_used": self.model_name,
                "max_length": self.max_length,
            }
        except Exception as e:
            return self._handle_error(e, input_data)
