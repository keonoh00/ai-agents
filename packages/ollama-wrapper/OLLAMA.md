# OllamaLLM Usage Guide

`OllamaLLM` provides a unified interface for running Ollama models with multiple AI frameworks. Create one instance and use framework-specific methods to get exactly what each framework needs.

## Quick Start

```python
from ollama_wrapper import OllamaLLM

# Create OllamaLLM instance
llm = OllamaLLM(model="ollama/llama3.2")

# Use with any framework
agent = Agent(model=llm.googleAdk())   # Google ADK
agent = Agent(llm=llm.crewai())        # CrewAI
client = llm.openai()                   # OpenAI SDK
langchain_llm = llm.langgraph()         # LangGraph
```

## Installation

Ensure you have Ollama installed and running:

```bash
# Install Ollama (if not already installed)
# Visit https://ollama.ai for installation instructions

# Pull a model
ollama pull llama3.2

# Verify Ollama is running
ollama list
```

## Configuration

### Environment Variables

Set default configuration via environment variables:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"  # Ollama server URL
export LOCAL_LLM_API_KEY="your-key"             # Optional, usually not needed
export LOCAL_LLM_TIMEOUT="60.0"                 # Request timeout in seconds
```

**Note**: Ollama does not require an API key for local usage. The `api_key` parameter is optional and only needed if:

- You're using a remote Ollama server with authentication enabled
- You're using a custom setup that requires authentication

### Basic Configuration

```python
from ollama_wrapper import OllamaLLM

# Minimal configuration (uses defaults)
llm = OllamaLLM(model="ollama/llama3.2")

# With custom api_base
llm = OllamaLLM(
    model="ollama/llama3.2",
    api_base="http://your-server:11434"
)

# With custom timeout
llm = OllamaLLM(
    model="ollama/llama3.2",
    timeout=120.0  # 120 seconds timeout
)

# Full configuration
llm = OllamaLLM(
    model="ollama/llama3.2",
    api_base="http://localhost:11434",
    api_key=None,  # Optional
    timeout=60.0
)
```

### Model Names

Model names should include the provider prefix:

```python
# Correct format
llm = OllamaLLM(model="ollama/llama3.2")
llm = OllamaLLM(model="ollama/gpt-oss:latest")
llm = OllamaLLM(model="ollama/mistral")

# For OpenAI-compatible endpoints, use 'openai/' prefix
llm = OllamaLLM(model="openai/gpt-oss:latest")
```

## Framework-Specific Usage

### Google ADK

```python
from google.adk.agents import Agent
from ollama_wrapper import OllamaLLM

# Create OllamaLLM instance
llm = OllamaLLM(model="ollama/llama3.2")

# Use with Google ADK agent
agent = Agent(
    name="Assistant",
    instruction="You are a helpful assistant.",
    model=llm.googleAdk()
)

# With tools
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"The weather in {city} is sunny."

agent = Agent(
    name="WeatherAgent",
    instruction="You help with weather questions.",
    model=llm.googleAdk(),
    tools=[get_weather]
)
```

### CrewAI

```python
from crewai import Agent
from ollama_wrapper import OllamaLLM

# Create OllamaLLM instance
llm = OllamaLLM(model="ollama/llama3.2")

# Use with CrewAI agent
agent = Agent(
    role="Assistant",
    goal="Help users",
    backstory="A helpful assistant",
    llm=llm.crewai()
)
```

### OpenAI SDK

```python
from ollama_wrapper import OllamaLLM

# Create OllamaLLM instance
llm = OllamaLLM(model="ollama/llama3.2")

# Get configured OpenAI client
client = llm.openai()

# Use like normal OpenAI client
response = client.chat.completions.create(
    model="llama3.2",  # Model name without prefix for /v1 endpoint
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### LangGraph

```python
from ollama_wrapper import OllamaLLM
from langgraph.graph import StateGraph, END

# Create OllamaLLM instance
llm = OllamaLLM(model="ollama/llama3.2")

# Get LangChain LLM
langchain_llm = llm.langgraph()

# Use in LangGraph workflow
from typing import TypedDict

class State(TypedDict):
    message: str

def process(state: State) -> State:
    response = langchain_llm.invoke(state["message"])
    return {"message": response.content}

workflow = StateGraph(State)
workflow.add_node("process", process)
workflow.set_entry_point("process")
workflow.add_edge("process", END)

app = workflow.compile()
```

## Remote GPU Servers

If you're running Ollama on a remote GPU server, configure it as follows:

### On the GPU Server

**Step 1: Make Ollama accessible on the network**

```bash
# Stop Ollama
sudo systemctl stop ollama

# Edit systemd service
sudo systemctl edit --full ollama

# Add the following to the file:
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
# Environment="CUDA_VISIBLE_DEVICES=0" # if you want to use a specific GPU

# Restart Ollama
sudo systemctl daemon-reload
sudo systemctl start ollama
```

**Step 2: Verify the network settings**

```bash
# Should show 0.0.0.0:11434 (not 127.0.0.1:11434)
netstat -tuln | grep 11434
```

**Optional: Configure firewall**

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 11434/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload
```

### On Your Local Machine

Set the remote server URL:

```python
from ollama_wrapper import OllamaLLM

llm = OllamaLLM(
    model="ollama/llama3.2",
    api_base="http://your-gpu-server-ip:11434"
)
```

Or use environment variable:

```bash
export OLLAMA_BASE_URL="http://your-gpu-server-ip:11434"
```

Then in your code:

```python
from ollama_wrapper import OllamaLLM

llm = OllamaLLM(model="ollama/llama3.2")  # Uses OLLAMA_BASE_URL from env
```

## GPU Selection

Ollama automatically uses available GPUs, but you can configure GPU selection:

### Check Available GPUs

```bash
# Check NVIDIA GPUs
nvidia-smi

# Check CUDA availability
ollama show llama3.2 --modelfile | grep -i gpu
```

### Configure GPU Selection

**Option 1: Set `CUDA_VISIBLE_DEVICES` (Recommended for specific GPUs)**

This environment variable restricts Ollama to use only specified GPUs.

```bash
# Stop Ollama
sudo systemctl stop ollama

# Edit systemd service
sudo systemctl edit --full ollama

# Add the following to the file:
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
# Environment="CUDA_VISIBLE_DEVICES=0" # if you want to use a specific GPU
# Environment="CUDA_VISIBLE_DEVICES=0,1" # if you want to use multiple GPUs
# Environment="OLLAMA_NUM_GPU=0" # if you want to use cpu only (Not recommended)

# Restart Ollama
sudo systemctl daemon-reload
sudo systemctl start ollama
```

### Verify GPU Usage

To confirm if Ollama is utilizing your GPU:

```bash
# While running a model, check GPU usage
nvidia-smi

# Or check Ollama logs
journalctl -u ollama -f
```

## Using Different Models

Simply change the model name when creating `OllamaLLM`:

```python
from ollama_wrapper import OllamaLLM

# Popular Ollama models:
llm = OllamaLLM(model="ollama/llama3.2")    # Llama 3.2
llm = OllamaLLM(model="ollama/mistral")     # Mistral 7B
llm = OllamaLLM(model="ollama/codellama")   # Code Llama
llm = OllamaLLM(model="ollama/phi3")        # Phi-3
llm = OllamaLLM(model="ollama/gemma2")      # Gemma 2
llm = OllamaLLM(model="ollama/qwen2")       # Qwen 2
llm = OllamaLLM(model="ollama/gpt-oss:latest")  # GPT-OSS

# Make sure to pull the model first:
# ollama pull mistral
# ollama pull codellama
```

## Testing Ollama Server

### Command Line

Test if Ollama is running and list available models:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Or use Ollama CLI
ollama list
ollama ps  # Show running models

# Test a model directly
ollama run llama3.2 "Hello, how are you?"
```

## Architecture Overview

### How It Works

`OllamaLLM` acts as a configuration wrapper that provides framework-specific adapters for Ollama:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                         │
│  (Google ADK / CrewAI / OpenAI SDK / LangGraph)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    OllamaLLM                                │
│  • Configuration wrapper for Ollama models                  │
│  • Framework-specific methods: crewai(), openai(), etc.     │
│  • Stores configuration (model, api_base, api_key, timeout) │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    LiteLLM                                  │
│  • Unified interface for multiple LLM providers             │
│  • Handles API compatibility and request formatting         │
│  • Routes requests to Ollama                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Ollama Server                                  │
│  • Runs models locally or on remote server                  │
│  • Provides HTTP API endpoint                               │
│  • Handles model inference                                  │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

**Google ADK**:

1. Application calls `agent.run()`
2. Google ADK uses `llm.googleAdk()` which returns an ADK `LiteLlm` instance
3. ADK's `LiteLlm` uses the `litellm` package
4. `litellm` sends request to Ollama API
5. Response flows back through the chain

**CrewAI**:

1. Application calls `agent.kickoff()`
2. CrewAI uses `llm.crewai()` which returns the model string with provider prefix
3. CrewAI's built-in litellm integration processes the request
4. Request is sent to Ollama API
5. Response flows back

**OpenAI SDK**:

1. Application calls `client.chat.completions.create()`
2. OpenAI client uses `llm.openai()` which returns a configured OpenAI client
3. Client sends request to Ollama's `/v1` endpoint
4. Response flows back

**LangGraph**:

1. Application calls workflow node
2. LangGraph uses `llm.langgraph()` which returns a LangChain LLM instance
3. LangChain sends request through litellm to Ollama
4. Response flows back

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Ollama server

**Solutions**:

1. Verify Ollama is running: `ollama list`
2. Check the server URL is correct
3. For remote servers, ensure firewall allows port 11434
4. Verify `OLLAMA_HOST` is set to `0.0.0.0:11434` on the server

### Model Not Found

**Problem**: Model not available on server

**Solutions**:

1. Pull the model: `ollama pull model-name`
2. List available models: `ollama list`
3. Verify model name includes correct prefix (e.g., `ollama/llama3.2`)

### Timeout Issues

**Problem**: Requests timing out

**Solutions**:

1. Increase timeout: `OllamaLLM(model="...", timeout=120.0)`
2. Check server performance and GPU availability
3. Verify network connectivity for remote servers

### No Response from Agent

**Problem**: Agent runs but doesn't return responses

**Solutions**:

1. Check if model supports function calling (if using tools)
2. Verify model is responding: `ollama run model-name "test"`
3. Check logs for errors
4. Try a different model that's known to work

## Available Methods

- **`crewai()`** → Returns model string with provider prefix for CrewAI
- **`openai()`** → Returns configured OpenAI client
- **`googleAdk()`** → Returns Google ADK `LiteLlm` instance
- **`langgraph()`** → Returns LangChain `ChatLiteLLM` instance

## Examples

### Complete Google ADK Example

```python
import os
import dotenv
from google.adk.agents import Agent
from ollama_wrapper import OllamaLLM

dotenv.load_dotenv()

# Create OllamaLLM instance
MODEL = OllamaLLM(model="ollama/llama3.2")

# Define tools
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"The weather in {city} is sunny."

# Create agent
agent = Agent(
    name="WeatherAgent",
    instruction="You help with weather questions. Use the get_weather tool when needed.",
    model=MODEL.googleAdk(),
    tools=[get_weather],
)

root_agent = agent
```

### Multiple Models Example

```python
from ollama_wrapper import OllamaLLM

# Different models for different purposes
coding_llm = OllamaLLM(model="ollama/codellama")
general_llm = OllamaLLM(model="ollama/llama3.2")
small_llm = OllamaLLM(model="ollama/phi3")

# Use each for different agents
coding_agent = Agent(model=coding_llm.googleAdk())
general_agent = Agent(model=general_llm.googleAdk())
```
