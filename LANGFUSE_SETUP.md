# Langfuse Tracing Setup

Langfuse integration for Perplexity API requests using OpenAI SDK.

## Features

- **Simplified tracing**: Perplexity search requests traced with minimal overhead
- **OpenAI SDK**: Uses OpenAI-compatible client for Perplexity API
- **Context manager pattern**: Clean trace initialization and cleanup
- **Automatic flush**: Traces flushed on server shutdown
- **Optional**: Works without Langfuse credentials

## Configuration

### 1. Get Langfuse Credentials

Visit [Langfuse Cloud](https://cloud.langfuse.com) to create an account and get:
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

### 2. Add to `.env`

```bash
LANGFUSE_PUBLIC_KEY=your_public_key_here
LANGFUSE_SECRET_KEY=your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com  # optional, defaults to cloud
```

### 3. Start Server

The Langfuse client initializes automatically on server startup if credentials are provided.

```bash
uv run uvicorn backend.main:app --reload
```

## What Gets Traced

### Trace: `search_oils_perplexity`

The entire Perplexity search operation is traced as a single operation with:

**Input:**
- `query`: Search query
- `liked_oils`: List of liked oils

**Automatically tracked:**
- Execution time
- Success/failure
- Any exceptions during processing

## Optional

Langfuse is optional—if credentials are not provided, the server continues without tracing. No errors will occur.

## Viewing Traces

Visit your Langfuse dashboard to view:
- Request traces with full input/output
- Latency metrics
- Error logs
- API usage patterns

## Implementation Details

### OpenAI SDK Usage

Uses OpenAI-compatible API for Perplexity:

```python
client = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)
response = client.chat.completions.create(
    model="sonar-pro",
    messages=[...]
)
```

Benefits over raw HTTP requests:
- Type-safe interface
- Automatic error handling
- Built-in retry logic
- Better logging

### Langfuse Context Manager

Traces are wrapped in a context manager for clean initialization/cleanup:

```python
trace_ctx = langfuse.trace(...) if langfuse else nullcontext()
with trace_ctx:
    # operation code
```

## Files Modified

- `pyproject.toml`: Added langfuse and openai dependencies
- `config.py`: Added Langfuse configuration
- `backend/main.py`: Simplified tracing using OpenAI SDK
- `.env.example`: Updated documentation
