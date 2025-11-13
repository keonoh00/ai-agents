# Ollama

A unified wrapper for Ollama LLM that provides framework-specific adapters for multiple AI frameworks.

## Features

- **CrewAI** support - Returns model string
- **OpenAI SDK** support - Returns configured OpenAI client
- **Google ADK** support - Returns LiteLlm instance
- **LangGraph** support - Returns LangChain LLM instance

## Installation

This package is part of the workspace and can be used by other projects in the workspace.

## Usage

```python
from ollama import OllamaLLM

# Create OllamaLLM instance
llm = OllamaLLM(model="ollama/llama3.2")

# Use with different frameworks
agent = Agent(llm=llm.crewai())      # CrewAI
client = llm.openai()                 # OpenAI SDK
agent = Agent(model=llm.googleAdk()) # Google ADK
langchain_llm = llm.langgraph()      # LangGraph
```

## Configuration

The wrapper supports configuration via environment variables or constructor arguments:

- `OLLAMA_BASE_URL`: Ollama server URL (default: `http://localhost:11434`)
- `LOCAL_LLM_API_KEY`: Optional API key
- `LOCAL_LLM_TIMEOUT`: Request timeout in seconds (default: 60.0)
