# LiteLLM Proxy Integration Guide: GLM-4.6 via Z.AI

**Complete guide for using LiteLLM proxy to integrate GLM-4.6 (Z.AI) with Python projects**

---

## Table of Contents
- [Overview](#overview)
- [How Agent Zero Uses LiteLLM](#how-agent-zero-uses-litellm)
- [The Proxy Architecture](#the-proxy-architecture)
- [Python Integration Examples](#python-integration-examples)
- [Standalone Python Projects](#standalone-python-projects)
- [Docker Deployment](#docker-deployment)
- [Configuration Deep Dive](#configuration-deep-dive)
- [Troubleshooting](#troubleshooting)
- [Cost Comparison](#cost-comparison)

---

## Overview

### What is LiteLLM?

LiteLLM is a **Python SDK and Proxy Server** that provides a unified OpenAI-compatible interface to 100+ LLM providers including:
- OpenAI, Anthropic, Google, Azure
- Hugging Face, Ollama, Mistral
- **Custom providers like Z.AI**

### Why Use LiteLLM with GLM-4.6?

**Problem:** Agent Zero expects OpenAI/Anthropic-compatible APIs. Z.AI's GLM Coding Plan uses a different format.

**Solution:** LiteLLM translates API calls between formats:

```
Your Python App → OpenAI format → LiteLLM → Z.AI format → GLM-4.6
                                    ↓
                              Translation happens here
```

**Benefits:**
- **Cost savings:** $3/month (GLM Coding Plan) vs $20/month (Claude Pro)
- **3× more quota:** GLM Coding Plan offers ~3× usage compared to Claude Pro
- **No code changes:** Your app uses standard OpenAI/Anthropic SDK
- **Provider flexibility:** Switch providers without changing code

---

## How Agent Zero Uses LiteLLM

### Current Architecture

Agent Zero integrates LiteLLM through its **built-in model provider system** (not as a separate Docker container):

```
┌─────────────────────────────────────────────┐
│  Agent Zero Container                       │
│  ┌───────────────────────────────────────┐  │
│  │  Agent Zero Python Application        │  │
│  │  ├─ Built-in LiteLLM SDK              │  │
│  │  ├─ model_providers.yaml config       │  │
│  │  └─ API calls via LiteLLM             │  │
│  └───────────────────────────────────────┘  │
│              ↓                               │
│  LiteLLM translates:                         │
│  OpenAI format → Z.AI Anthropic format      │
└─────────────────────────────────────────────┘
              ↓
    https://api.z.ai/api/anthropic
              ↓
         GLM-4.6 Model
```

### Key Configuration Files

#### 1. **model_providers.yaml** - Provider Definition
```yaml
chat:
  zai:
    name: Z.AI (GLM Coding Plan)
    litellm_provider: anthropic  # Use Anthropic format
    kwargs:
      api_base: https://api.z.ai/api/anthropic  # Z.AI endpoint
```

**What this does:**
- Tells Agent Zero to use LiteLLM's `anthropic` provider
- Points to Z.AI's Anthropic-compatible endpoint
- Environment variable `ZAI_API_KEY` is auto-loaded

#### 2. **.env** - API Credentials
```bash
# Z.AI GLM Coding Plan API Key
ZAI_API_KEY=your_api_key_here
```

#### 3. **Settings UI Configuration**
Inside Agent Zero's web interface (http://localhost:3003):
1. Open Settings ⚙️
2. Select Provider: **Z.AI (GLM Coding Plan)**
3. Select Model: **glm-4.6** (or GLM-4.5-Air, GLM-4-Flash)
4. API Key: Auto-loaded from `ZAI_API_KEY`

---

## The Proxy Architecture

### Z.AI Endpoint Discovery (Critical)

**Platform-Specific Endpoints:**

Z.AI provides different API endpoints based on your subscription:

| Subscription | Endpoint | Works? |
|-------------|----------|--------|
| Standard ZhipuAI | `https://open.bigmodel.cn/api/paas/v4` | ❌ Error 1113 |
| **GLM Coding Plan** | `https://api.z.ai/api/anthropic` | ✅ Perfect |

**Key Insight:** The GLM Coding Plan ($3/month) requires the **Z.AI Anthropic endpoint**, not the standard ZhipuAI endpoint.

### API Translation Flow

```python
# Your code makes OpenAI-style call
response = litellm.completion(
    model="anthropic/glm-4.6",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="https://api.z.ai/api/anthropic",
    api_key=os.getenv("ZAI_API_KEY")
)

# LiteLLM translates to Z.AI's Anthropic format
# POST https://api.z.ai/api/anthropic/v1/messages
# {
#   "model": "glm-4.6",
#   "messages": [...],
#   "max_tokens": 1024
# }
```

---

## Python Integration Examples

### Example 1: Basic LiteLLM SDK Usage

```python
# install: pip install litellm

import os
from litellm import completion

# Set credentials
os.environ["ZAI_API_KEY"] = "your_api_key_here"

# Make API call
response = completion(
    model="anthropic/glm-4.6",  # Use Anthropic provider format
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    api_base="https://api.z.ai/api/anthropic",
    api_key=os.getenv("ZAI_API_KEY")
)

print(response.choices[0].message.content)
```

### Example 2: Using OpenAI SDK Format

```python
# install: pip install litellm openai

import os
from litellm import completion

os.environ["ZAI_API_KEY"] = "your_api_key_here"

# OpenAI-style parameters work automatically
response = completion(
    model="anthropic/glm-4.6",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a Python function to reverse a string"}
    ],
    temperature=0.7,
    max_tokens=500,
    api_base="https://api.z.ai/api/anthropic",
    api_key=os.getenv("ZAI_API_KEY")
)

print(response.choices[0].message.content)
```

### Example 3: Streaming Responses

```python
import os
from litellm import completion

os.environ["ZAI_API_KEY"] = "your_api_key_here"

response = completion(
    model="anthropic/glm-4.6",
    messages=[{"role": "user", "content": "Write a story about AI"}],
    stream=True,  # Enable streaming
    api_base="https://api.z.ai/api/anthropic",
    api_key=os.getenv("ZAI_API_KEY")
)

# Stream chunks as they arrive
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Example 4: Error Handling

```python
import os
from litellm import completion
from litellm.exceptions import BadRequestError, AuthenticationError

os.environ["ZAI_API_KEY"] = "your_api_key_here"

try:
    response = completion(
        model="anthropic/glm-4.6",
        messages=[{"role": "user", "content": "Hello!"}],
        api_base="https://api.z.ai/api/anthropic",
        api_key=os.getenv("ZAI_API_KEY")
    )
    print(response.choices[0].message.content)

except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    print("Check your ZAI_API_KEY")

except BadRequestError as e:
    print(f"Bad request: {e}")
    print("Check model name and parameters")

except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Standalone Python Projects

### Project Structure

```
my-glm-project/
├── .env                 # API credentials
├── requirements.txt     # Dependencies
├── config.py           # LiteLLM configuration
└── main.py             # Your application
```

### 1. requirements.txt

```txt
litellm>=1.50.0
python-dotenv>=1.0.0
openai>=1.0.0  # Optional: for type hints
```

### 2. .env

```bash
ZAI_API_KEY=your_api_key_here
ZAI_BASE_URL=https://api.z.ai/api/anthropic
GLM_MODEL=glm-4.6
```

### 3. config.py

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LiteLLM configuration
LITELLM_CONFIG = {
    "model": "anthropic/glm-4.6",
    "api_base": os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/anthropic"),
    "api_key": os.getenv("ZAI_API_KEY"),
}

# Model parameters
DEFAULT_PARAMS = {
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 0.9,
}

def validate_config():
    """Validate required configuration"""
    if not LITELLM_CONFIG["api_key"]:
        raise ValueError("ZAI_API_KEY not set in environment")
    return True
```

### 4. main.py

```python
from litellm import completion
from config import LITELLM_CONFIG, DEFAULT_PARAMS, validate_config

def chat(message: str, system_prompt: str = None) -> str:
    """Send message to GLM-4.6 and get response"""

    # Validate configuration
    validate_config()

    # Prepare messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})

    # Call LiteLLM
    response = completion(
        **LITELLM_CONFIG,
        **DEFAULT_PARAMS,
        messages=messages
    )

    return response.choices[0].message.content

def main():
    """Example usage"""

    # Simple query
    result = chat("What is Python?")
    print(f"Response: {result}\n")

    # With system prompt
    result = chat(
        message="Write a hello world program",
        system_prompt="You are a Python expert. Provide code with comments."
    )
    print(f"Code:\n{result}")

if __name__ == "__main__":
    main()
```

### 5. Run the project

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export ZAI_API_KEY="your_api_key_here"

# Run
python main.py
```

---

## Docker Deployment

### Option 1: Embedded LiteLLM (Like Agent Zero)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  my-glm-app:
    build: .
    container_name: my-glm-app
    environment:
      - ZAI_API_KEY=${ZAI_API_KEY}
      - ZAI_BASE_URL=https://api.z.ai/api/anthropic
    env_file:
      - .env
    restart: unless-stopped
```

**Usage:**
```bash
# Build and run
docker compose up -d

# View logs
docker compose logs -f
```

### Option 2: Separate LiteLLM Proxy Server

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  litellm-proxy:
    image: ghcr.io/berriai/litellm:latest
    container_name: litellm-proxy
    ports:
      - "4000:4000"
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    environment:
      - ZAI_API_KEY=${ZAI_API_KEY}
    command: --config /app/config.yaml
    restart: unless-stopped

  my-app:
    build: .
    depends_on:
      - litellm-proxy
    environment:
      - LITELLM_PROXY_URL=http://litellm-proxy:4000
```

**litellm_config.yaml:**
```yaml
model_list:
  - model_name: glm-4.6
    litellm_params:
      model: anthropic/glm-4.6
      api_base: https://api.z.ai/api/anthropic
      api_key: os.environ/ZAI_API_KEY

  - model_name: glm-4.5-air
    litellm_params:
      model: anthropic/glm-4.5-air
      api_base: https://api.z.ai/api/anthropic
      api_key: os.environ/ZAI_API_KEY

general_settings:
  master_key: "sk-1234"  # Proxy authentication key

litellm_settings:
  drop_params: true
  success_callback: []
```

**Python code to use proxy:**
```python
import os
from litellm import completion

# Point to LiteLLM proxy instead of Z.AI directly
response = completion(
    model="glm-4.6",  # No "anthropic/" prefix when using proxy
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://localhost:4000",  # LiteLLM proxy URL
    api_key="sk-1234"  # Proxy master key
)
```

---

## Configuration Deep Dive

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ZAI_API_KEY` | Z.AI authentication | `02d6d0...599000.0Ms...` |
| `ZAI_BASE_URL` | API endpoint | `https://api.z.ai/api/anthropic` |
| `LITELLM_PROXY_URL` | Proxy server URL | `http://localhost:4000` |

### Available GLM Models via Z.AI

| Model | Description | Use Case |
|-------|-------------|----------|
| `glm-4.6` | Latest, most capable | Complex reasoning, coding |
| `glm-4.5-air` | Faster, lighter | Quick responses, chat |
| `glm-4-flash` | Ultra-fast | Simple queries, high volume |
| `glm-4-plus` | Enhanced version | Advanced tasks |

### Model Parameters

```python
# Comprehensive parameter example
response = completion(
    model="anthropic/glm-4.6",
    messages=[...],

    # Generation parameters
    temperature=0.7,      # Randomness (0.0-1.0)
    max_tokens=2000,      # Max response length
    top_p=0.9,            # Nucleus sampling

    # API configuration
    api_base="https://api.z.ai/api/anthropic",
    api_key=os.getenv("ZAI_API_KEY"),

    # LiteLLM features
    timeout=30,           # Request timeout (seconds)
    stream=False,         # Enable/disable streaming

    # Optional metadata
    metadata={
        "user_id": "user123",
        "tags": ["production"]
    }
)
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Error

**Error:**
```
AuthenticationError: litellm.AuthenticationError: AuthenticationError: 401
```

**Solution:**
```bash
# Verify API key
echo $ZAI_API_KEY

# Set correctly
export ZAI_API_KEY="your_actual_key_here"

# Test with curl
curl -X POST https://api.z.ai/api/anthropic/v1/messages \
  -H "x-api-key: $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-4.6","max_tokens":100,"messages":[{"role":"user","content":"hi"}]}'
```

#### 2. Wrong Endpoint Error (1113)

**Error:**
```
BadRequestError: error code: 1113
```

**Solution:** You're using the wrong endpoint. GLM Coding Plan requires Z.AI endpoint:
```python
# ❌ WRONG - Standard ZhipuAI endpoint
api_base="https://open.bigmodel.cn/api/paas/v4"

# ✅ CORRECT - Z.AI Anthropic endpoint
api_base="https://api.z.ai/api/anthropic"
```

#### 3. Model Not Found

**Error:**
```
litellm.NotFoundError: model glm-4.6 not found
```

**Solution:** Use correct model format:
```python
# ❌ WRONG
model="glm-4.6"

# ✅ CORRECT
model="anthropic/glm-4.6"  # Prefix with provider
```

#### 4. Import Error

**Error:**
```
ModuleNotFoundError: No module named 'litellm'
```

**Solution:**
```bash
pip install litellm
# or
pip install -r requirements.txt
```

#### 5. Connection Timeout

**Error:**
```
requests.exceptions.Timeout: HTTPSConnectionPool
```

**Solution:**
```python
# Increase timeout
response = completion(
    model="anthropic/glm-4.6",
    messages=[...],
    timeout=60,  # Increase from default 30s
    api_base="https://api.z.ai/api/anthropic",
    api_key=os.getenv("ZAI_API_KEY")
)
```

### Debug Mode

Enable verbose logging:

```python
import litellm

# Enable debug mode
litellm.set_verbose = True

# Now all API calls will show detailed logs
response = completion(
    model="anthropic/glm-4.6",
    messages=[{"role": "user", "content": "test"}],
    api_base="https://api.z.ai/api/anthropic",
    api_key=os.getenv("ZAI_API_KEY")
)
```

### Test Script

```python
#!/usr/bin/env python3
"""Test GLM-4.6 connection via LiteLLM"""

import os
import sys
from litellm import completion

def test_connection():
    """Test Z.AI GLM-4.6 connection"""

    # Check API key
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        print("❌ ZAI_API_KEY not set")
        return False

    print("✅ API key found")

    # Test API call
    try:
        print("Testing GLM-4.6 connection...")
        response = completion(
            model="anthropic/glm-4.6",
            messages=[{"role": "user", "content": "Say 'connection successful'"}],
            api_base="https://api.z.ai/api/anthropic",
            api_key=api_key,
            timeout=10
        )

        print(f"✅ Response: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
```

**Run:**
```bash
chmod +x test_glm.py
export ZAI_API_KEY="your_key_here"
python test_glm.py
```

---

## Cost Comparison

### GLM Coding Plan vs Claude Pro

| Feature | GLM Coding Plan | Claude Pro |
|---------|----------------|------------|
| **Cost** | $3/month | $20/month |
| **Savings** | - | **85% cheaper** |
| **Quota** | ~3× Claude Pro | 1× baseline |
| **Models** | GLM-4.6, GLM-4.5-Air, GLM-4-Flash | Claude 3.5 Sonnet |
| **API Access** | ✅ Yes | ✅ Yes |
| **Integration** | Via LiteLLM | Native |

### Token Pricing (Approximate)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| GLM-4.6 | ~$0.50 | ~$1.50 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| **Savings** | **83% cheaper** | **90% cheaper** |

---

## Advanced Usage

### Multi-Provider Failover

```python
from litellm import completion

def robust_completion(message: str):
    """Try GLM-4.6 first, fallback to GPT-4"""

    providers = [
        {
            "model": "anthropic/glm-4.6",
            "api_base": "https://api.z.ai/api/anthropic",
            "api_key": os.getenv("ZAI_API_KEY")
        },
        {
            "model": "gpt-4",
            "api_key": os.getenv("OPENAI_API_KEY")
        }
    ]

    for provider in providers:
        try:
            response = completion(
                **provider,
                messages=[{"role": "user", "content": message}],
                timeout=10
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Provider failed: {e}")
            continue

    raise Exception("All providers failed")
```

### Rate Limiting

```python
import time
from functools import wraps

def rate_limit(calls_per_minute=60):
    """Decorator to rate limit API calls"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

@rate_limit(calls_per_minute=30)
def call_glm(message):
    return completion(
        model="anthropic/glm-4.6",
        messages=[{"role": "user", "content": message}],
        api_base="https://api.z.ai/api/anthropic",
        api_key=os.getenv("ZAI_API_KEY")
    )
```

### Caching Responses

```python
import hashlib
import json
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_completion(message_hash: str, message: str):
    """Cache identical requests"""
    response = completion(
        model="anthropic/glm-4.6",
        messages=[{"role": "user", "content": message}],
        api_base="https://api.z.ai/api/anthropic",
        api_key=os.getenv("ZAI_API_KEY")
    )
    return response.choices[0].message.content

def chat_with_cache(message: str):
    """Use cached responses when possible"""
    message_hash = hashlib.md5(message.encode()).hexdigest()
    return cached_completion(message_hash, message)
```

---

## Summary

**Key Takeaways:**

1. **LiteLLM acts as a translation layer** between your OpenAI-style code and Z.AI's GLM-4.6
2. **Agent Zero uses embedded LiteLLM**, not a separate proxy container
3. **Critical configuration:** Use `https://api.z.ai/api/anthropic` endpoint for GLM Coding Plan
4. **Model format:** Always use `anthropic/glm-4.6` prefix
5. **Environment variable:** Set `ZAI_API_KEY` for authentication
6. **85% cost savings** compared to Claude Pro with 3× more quota

**Next Steps:**

- Clone Agent Zero to see working implementation
- Test with provided Python examples
- Deploy your own projects using standalone guides
- Experiment with different GLM models (4.6, 4.5-Air, 4-Flash)

---

**Repository:** https://github.com/bludiesel/agent-zero-glm46
**Documentation:** See `/docs/` folder for more guides
