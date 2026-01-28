# Langfuse Tracing Setup

Langfuse integration has been added to trace Perplexity API requests and the overall search flow.

## Features

- **Trace tracking**: Each Perplexity search request is traced with full input/output
- **Span tracking**: Perplexity API calls are captured as spans
- **Error tracking**: API errors are logged as events
- **Automatic flush**: Traces are flushed on server shutdown

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

Captured inputs:
- `query`: Search query
- `liked_oils`: List of liked oils
- `disliked_oils`: List of disliked oils
- `limit`: Result limit

Captured outputs:
- `results_count`: Total results
- `perplexity_results_count`: Results from Perplexity
- `embedding_results_count`: Results from embeddings
- `results`: List of returned results with metadata

### Span: `perplexity_api_call`

Captures:
- **Input**: Messages sent to Perplexity
- **Output**: Parsed oil names from response

### Events

- **perplexity_error**: Logged if Perplexity API call fails

## Optional

Langfuse is optional—if credentials are not provided, the server continues without tracing. No errors will occur.

## Viewing Traces

Visit your Langfuse dashboard to view:
- Request traces with full input/output
- Latency metrics
- Error logs
- API usage patterns

## Files Modified

- `pyproject.toml`: Added langfuse dependency
- `config.py`: Added Langfuse configuration
- `backend/main.py`: Added tracing to perplexity endpoint
- `.env.example`: Added Langfuse credentials template
