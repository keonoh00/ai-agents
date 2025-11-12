from __future__ import annotations

import os
from typing import Optional


class OllamaLLM:
    """
    Local LLM wrapper for Ollama with framework-specific methods.

    Example:
        ```python
        from financial_advisor.local_llm import LocalLLM

        llm = LocalLLM(
            model="ollama/llama3.2",
        )

        # Use with different frameworks
        agent = Agent(llm=llm.crewai())      # CrewAI
        client = llm.openai()                 # OpenAI SDK
        agent = Agent(model=llm.googleAdk()) # Google ADK
        langchain_llm = llm.langgraph()      # LangGraph
        ```
    """

    def __init__(
        self,
        model: str,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        """
        Initialize LocalLLM for Ollama.

        Args:
            model: Model name with 'ollama/' prefix (e.g., "ollama/llama3.2", "ollama/gpt-oss:latest")
            api_base: Ollama server URL. Must be provided or set via OLLAMA_BASE_URL env var
            api_key: Optional API key (usually not needed for Ollama)
            timeout: Request timeout in seconds. Defaults to 60.0 or LOCAL_LLM_TIMEOUT env var
        """
        # Store configuration (no validation)
        api_base = api_base or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
        self.api_base = api_base.rstrip("/")
        self.model = model.strip()
        self.api_key = api_key or os.getenv("LOCAL_LLM_API_KEY")
        self.timeout = float(timeout or 60.0)
        self._kwargs = kwargs

    def crewai(self) -> str:
        """Get CrewAI-compatible model string."""
        return self.model

    def openai(self):
        """Get configured OpenAI client for Ollama."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Install it with: pip install openai"
            )

        return OpenAI(
            base_url=f"{self.api_base}/v1",
            api_key=self.api_key or "ollama",
            timeout=self.timeout,
        )

    def googleAdk(self):
        """Get Google ADK LiteLlm instance for Ollama."""
        try:
            from google.adk.models.lite_llm import LiteLlm
        except ImportError:
            raise ImportError(
                "Google ADK not installed. Install it with: pip install google-adk"
            )

        return LiteLlm(
            model=self.model,
            api_base=self.api_base,
            timeout=self.timeout,
        )

    def langgraph(self):
        """Get LangChain LLM instance for LangGraph."""
        try:
            from langchain_community.chat_models import ChatLiteLLM
        except ImportError:
            raise ImportError(
                "LangChain not installed. Install it with: pip install langchain langchain-community"
            )

        return ChatLiteLLM(
            model=self.model,
            api_base=self.api_base,
            api_key=self.api_key,
            timeout=self.timeout,
        )
