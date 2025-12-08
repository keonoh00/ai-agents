# Network Manager

A multi-agent LangGraph system for network infrastructure monitoring and management.

## Table of Contents

- [📋 Prerequisites](#-prerequisites)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🧪 Testing Agents](#-testing-agents)
- [🔧 Troubleshooting](#-troubleshooting)

## 📋 Prerequisites

This project requires `uv` as the package manager. Make sure you have the following installed:

- Python 3.13+
- `uv` package manager (required)
- Ollama running locally or accessible via network

## 📦 Installation

1. **Install `uv`** (required):

   ```bash
   # macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   **Verify installation:**

   ```bash
   uv --version
   ```

   You should see a version number. If not, ensure `uv` is in your PATH. You may need to restart your terminal or run:

   ```bash
   source $HOME/.cargo/env  # If installed via the script
   ```

2. **Navigate to project directory**:

   ```bash
   cd langgraph/network-manager
   ```

3. **Install dependencies**:

   ```bash
   uv sync
   ```

   This will:

   - Create a virtual environment automatically
   - Install all project dependencies
   - Lock dependencies in `uv.lock`

   **Verify installation:**

   ```bash
   uv run python --version
   ```

   You should see Python 3.13+.

4. **Verify Ollama is running**:

   ```bash
   ollama list
   ```

   Ensure you have a model available (e.g., `gpt-oss`). If not, pull a model:

   ```bash
   ollama pull gpt-oss
   ```

## ⚙️ Configuration

### Environment Variables Setup

The project uses environment variables stored in a `.env` file for configuration. This file contains runtime settings.

#### Step 1: Create the `.env` file

Create a `.env` file in the **project root** (`langgraph/network-manager/.env`):

```bash
cd langgraph/network-manager
touch .env
```

Then add the following variables:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=ollama:gpt-oss:latest
```

**Important:** The `.env` file must be located in the project root (`langgraph/network-manager/.env`). It is automatically loaded by:

- `langgraph.json`: Loads `.env` from project root for LangGraph CLI
- Python code: Environment variables are accessible via `os.getenv()`

#### Step 2: Verify Configuration

The project uses the following configuration structure:

**Environment variables** (`.env` file in project root):

- `OLLAMA_BASE_URL`: Ollama server URL (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Ollama model to use (default: `ollama:gpt-oss:latest`)

You can verify the configuration is loaded correctly:

```bash
uv run python -c "import os; print(f'OLLAMA_BASE_URL: {os.getenv(\"OLLAMA_BASE_URL\")}'); print(f'OLLAMA_MODEL: {os.getenv(\"OLLAMA_MODEL\")}')"
```

Expected output:

```text
OLLAMA_BASE_URL: http://localhost:11434
OLLAMA_MODEL: ollama:gpt-oss:latest
```

## 🧪 Testing Agents

Start the graph using LangGraph CLI:

```bash
uv run langgraph dev
```

🎨 Enter this URL in your browser: <https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024>

## 🔧 Troubleshooting

### `uv` command not found

If `uv --version` fails:

1. **Check if uv is installed:**

   ```bash
   which uv
   ```

2. **If not found, reinstall and add to PATH:**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.cargo/env
   ```

3. **Or add to your shell profile** (`~/.bashrc`, `~/.zshrc`, etc.):

   ```bash
   export PATH="$HOME/.cargo/bin:$PATH"
   ```

### Dependencies not installing

If `uv sync` fails:

1. **Check Python version:**

   ```bash
   uv run python --version
   ```

   Must be Python 3.13+

2. **Clear cache and retry:**

   ```bash
   uv cache clean
   uv sync
   ```
