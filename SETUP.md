# 🤖 YODA Setup Guide

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd mcp-04
```

### 2. Install Dependencies
```bash
pip install -r requirements_ui.txt
```

### 3. Configure Environment
```bash
# Copy the template
cp .env.template .env

# Edit with your values
nano .env  # or use your favorite editor
```

### 4. Required API Keys

#### DataDog API Keys
1. Go to [DataDog API Keys](https://app.datadoghq.com/organization-settings/api-keys)
2. Create/copy your API Key and Application Key
3. Set in `.env`:
   ```
   DD_API_KEY=your_datadog_api_key_here
   DD_APP_KEY=your_datadog_application_key_here
   ```

#### OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create/copy your API key
3. Set in `.env`:
   ```
   OPENAI_API_KEY=sk-abc123def456ghi789...
   ```

### 5. Launch YODA
```bash
python start_ui.py
```

### 6. Access Interface
- Open browser: http://localhost:7860
- YODA is ready! 🚀

## Minimal Configuration

Your `.env` only needs these variables to work:
```env
# Required API Keys
DD_API_KEY=your_datadog_api_key
DD_APP_KEY=your_datadog_app_key  
OPENAI_API_KEY=your_openai_key

# Optional Performance Settings
PRELOAD_CACHES=true          # Cache warm-up (faster responses)
SSL_VERIFY=true              # SSL certificate verification
CONVERSATION_LIMIT=5         # Context memory (1-50 conversations)
```

## Features

- ✅ **Cache Warm-up**: Fast responses with `PRELOAD_CACHES=true`
- ✅ **Smart Validation**: Real service/environment discovery
- ✅ **SSL Flexibility**: Disable with `SSL_VERIFY=false` if needed
- ✅ **Custom LLM**: Override with `LLM_API_URL` if needed
- ✅ **Token Optimization**: Control context size with `CONVERSATION_LIMIT`

## Troubleshooting

### SSL Issues
If you get SSL certificate errors:
```env
SSL_VERIFY=false
```

### Cache Performance
For fastest startup (recommended):
```env
PRELOAD_CACHES=true
```

### Corporate Networks
If behind proxy:
```env
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=https://proxy.company.com:8080
```

### Token Limit Issues
If you get "Request too large" or "rate_limit_exceeded" errors:

#### Problem: Large Conversations
```
Error: Request too large for gpt-4o-mini... Requested 848169 tokens
```

#### Solution: Reduce Conversation History
```env
# Minimal context (recommended for token issues)
CONVERSATION_LIMIT=1   # 1 conversation = 2 messages

# Light context  
CONVERSATION_LIMIT=2   # 2 conversations = 4 messages

# Balanced context (default)
CONVERSATION_LIMIT=5   # 5 conversations = 10 messages

# Heavy context (use with caution)
CONVERSATION_LIMIT=10  # 10 conversations = 20 messages
```

#### Understanding CONVERSATION_LIMIT
- **What it controls**: Number of recent conversation exchanges kept in memory
- **Format**: 1 conversation = 1 user message + 1 assistant response = 2 messages
- **Range**: 1-50 conversations (2-100 messages)
- **Token impact**: Lower values = fewer tokens = better performance
- **Context trade-off**: Lower values = less conversation memory

#### Recommended Settings by Use Case
```env
# Quick queries/commands (saves tokens)
CONVERSATION_LIMIT=1

# Normal usage (balanced)  
CONVERSATION_LIMIT=5

# Complex troubleshooting (needs context)
CONVERSATION_LIMIT=10
```

#### Additional Token Optimization
```env
# Disable cache preloading to reduce startup tokens
PRELOAD_CACHES=false

# Use faster model if available
LLM_API_URL=https://api.openai.com/v1/chat/completions  # gpt-4o-mini
```

## May the Force be with your infrastructure! 🌟 