# Langfuse Tracing Setup

Automatic tracing of Perplexity API requests using Langfuse-instrumented OpenAI client.

## Features

- **Automatic instrumentation**: Langfuse OpenAI client automatically traces all API calls
- **Zero-config tracing**: No manual trace wrapping needed
- **Rich metadata**: Operation name, user feeling, and oil preferences tracked
- **Graceful degradation**: Falls back to regular OpenAI SDK if Langfuse unavailable
- **Automatic flush**: Traces flushed on server shutdown

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

### Operation: `perplexity_oil_search`

Each Perplexity API call is automatically traced with:

**Metadata:**
- `user_feeling`: The user's search query/feeling
- `liked_oils`: List of oils user prefers
- `disliked_oils`: List of oils user dislikes

**Automatically captured:**
- Request messages
- Response content
- API latency
- Token usage (if provided by Perplexity)
- Success/failure status

## Optional

Langfuse is optional—if credentials are not provided, the server continues without tracing. No errors will occur.

## Viewing Traces

Visit your Langfuse dashboard to view:
- Request traces with full input/output
- Latency metrics
- Error logs
- API usage patterns

## Implementation Details

### Langfuse-Instrumented OpenAI Client

Automatically traces all OpenAI SDK calls using Langfuse wrapper:

```python
# Import automatically uses Langfuse instrumentation when available
try:
    from langfuse.openai import OpenAI
except ImportError:
    from openai import OpenAI

client = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai",
)

# This call is automatically traced by Langfuse
response = client.chat.completions.create(
    model="sonar",
    messages=[...],
    extra_body={"search_domain_filter": ["doterra.com"]},
    name="perplexity_oil_search",
    metadata={
        "user_feeling": user_feeling,
        "liked_oils": liked_oils,
        "disliked_oils": disliked_oils,
    }
)
```

### Why Langfuse OpenAI Client?

1. **Automatic instrumentation**: No manual trace wrapping needed
2. **Standard API**: Works exactly like regular OpenAI client
3. **Rich tracing**: Captures all request/response details
4. **Zero overhead**: When Langfuse disabled, uses standard SDK
5. **Best practices**: Follows Langfuse documentation recommendations

## Files Modified

- `pyproject.toml`: Added langfuse and openai dependencies
- `config.py`: Added Langfuse configuration
- `backend/main.py`: Simplified tracing using OpenAI SDK
- `.env.example`: Updated documentation
