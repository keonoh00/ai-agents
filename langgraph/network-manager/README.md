# Network Manager

A multi-agent LangGraph system for network infrastructure monitoring and management.

## Prerequisites

This project requires `uv` as the package manager. Make sure you have the following installed:

- Python 3.13+
- `uv` package manager (required)
- Ollama running locally or accessible via network

## Installation

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

## Configuration

### Environment Variables

Create a `.env` file in the project root (`langgraph/network-manager/.env`) with the following variables:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

LANGSMITH_API_KEY=your-api-key-here
```

**Important:** The `.env` file is automatically loaded by `langgraph.json`. Make sure it's in the project root directory.

### Getting a LangSmith API Key

1. Sign up at <https://smith.langchain.com>
2. Navigate to Settings → API Keys
3. Create a new API key
4. Copy the API key and add it to your `.env` file as `LANGSMITH_API_KEY`

   **Note:** The API key should start with `ls__` prefix.

## LangSmith Debugging

### Starting LangSmith Tracing

Once you have configured your `.env` file with LangSmith credentials, tracing is automatically enabled when you run the graph.

1. **Start the graph**:

   ```bash
   uv run langgraph dev
   ```

   Debugging platform will be available in `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

2. **Run your queries** - All traces will automatically be sent to LangSmith

3. **Access the LangSmith Dashboard**:

   Open your browser and navigate to:

   **<https://smith.langchain.com>**

   You'll see all your traces, runs, and debugging information in the dashboard.

## Troubleshooting

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

### LangSmith tracing not working

1. **Verify `.env` file exists:**

   ```bash
   ls -la .env
   ```

2. **Check environment variables are loaded:**

   ```bash
   uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('LANGCHAIN_TRACING_V2'))"
   ```

3. **Ensure you're using `uv run` for all commands**

## Development

For development setup, code structure, advanced debugging techniques, and extending the system, see [DEVELOPMENT.md](DEVELOPMENT.md).
