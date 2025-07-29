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

Your `.env` only needs these 5 variables to work:
```env
DD_API_KEY=your_datadog_api_key
DD_APP_KEY=your_datadog_app_key  
OPENAI_API_KEY=your_openai_key
PRELOAD_CACHES=true
SSL_VERIFY=true
```

## Features

- ✅ **Cache Warm-up**: Fast responses with `PRELOAD_CACHES=true`
- ✅ **Smart Validation**: Real service/environment discovery
- ✅ **SSL Flexibility**: Disable with `SSL_VERIFY=false` if needed
- ✅ **Custom LLM**: Override with `LLM_API_URL` if needed

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

## May the Force be with your infrastructure! 🌟 