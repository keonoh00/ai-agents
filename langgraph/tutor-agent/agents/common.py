import os

from dotenv import load_dotenv
from langchain_ollama.chat_models import ChatOllama

load_dotenv(dotenv_path="../../../.env")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL")
OLLAMA_MODEL_NAME = "ollama:gpt-oss:latest"
MODEL = "openai:gpt-4o"
