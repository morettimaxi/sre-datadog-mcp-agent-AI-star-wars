#!/usr/bin/env python3

import re
import requests
import os
import sys
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mcp_loader import get_requests_verify, get_llm_api_url

# Initialize
load_dotenv()

# OpenAI API
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def parse_tool_call(llm_response):
    """
    Parse LLM response for tool calls in multiple formats:
    1. TOOL_CALL: tool_name(param1='value', param2=['list'])
    2. YODA-themed: `tool_name(param1='value')`
    3. Function calls in backticks: `tool_name(params)`
    """
    
    # First try the exact TOOL_CALL format
    pattern = r'TOOL_CALL:\s*(\w+)\((.*?)\)(?:\s|$)'
    match = re.search(pattern, llm_response, re.DOTALL)
    
    if match:
        tool_name = match.group(1)
        params_str = match.group(2)
        print(f"🔍 Tool Parse Result: tool='{tool_name}', params_raw='{params_str[:100]}'")
    else:
        # Try flexible patterns for YODA-themed responses
        # Look for function calls in backticks or after colons
        patterns = [
            r'`(\w+)\((.*?)\)`',  # `function_name(params)`
            r':\s*`(\w+)\((.*?)\)`',  # : `function_name(params)`
            r'(\w+)\((.*?)\)(?:\s|$)',  # Just function_name(params) anywhere
        ]
        
        for pattern in patterns:
            match = re.search(pattern, llm_response, re.DOTALL)
            if match:
                potential_tool = match.group(1)
                params_str = match.group(2)
                
                # Check if this looks like a valid MCP tool name
                # Valid MCP tools typically end with _mcp or contain words like get, search, list, analyze
                if (potential_tool.endswith('_mcp') or 
                    any(word in potential_tool.lower() for word in ['get', 'search', 'list', 'analyze', 'query', 'fetch', 'find'])):
                    tool_name = potential_tool
                    print(f"🔍 Tool Parse Result: tool='{tool_name}', params_raw='{params_str[:100]}'")
                    break
                else:
                    # Keep looking with other patterns
                    continue
        else:
            # No tool call found
            print(f"🔍 Tool Parse Result: tool='None', params=None")
            print(f"   ℹ️ No tool call detected - responding with droid personality")
            return None, None
    
    # Parse parameters
    params = {}
    if params_str.strip():
        try:
            params = parse_function_parameters(params_str)
            print(f"   📋 Parsed params: {params}")
        except Exception as e:
            print(f"❌ Error parsing parameters: {params_str}")
            print(f"❌ Parse error: {str(e)}")
    
    return tool_name, params

def parse_function_parameters(params_str):
    """
    Parse function parameters more robustly
    Handles complex strings, quotes, and nested structures
    """
    params = {}
    params_str = params_str.strip()
    
    if not params_str:
        return params
    
    # Handle simple cases first
    if '=' not in params_str:
        return params
    
    # Split parameters by commas, but respect quoted strings
    param_parts = []
    current_part = ""
    in_quotes = False
    quote_char = None
    paren_depth = 0
    bracket_depth = 0
    
    i = 0
    while i < len(params_str):
        char = params_str[i]
        
        if char in ['"', "'"] and (i == 0 or params_str[i-1] != '\\'):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
        elif not in_quotes:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif char == ',' and paren_depth == 0 and bracket_depth == 0:
                param_parts.append(current_part.strip())
                current_part = ""
                i += 1
                continue
        
        current_part += char
        i += 1
    
    if current_part.strip():
        param_parts.append(current_part.strip())
    
    # Parse each parameter
    for part in param_parts:
        if '=' not in part:
            continue
            
        key, value = part.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Remove quotes from key if present
        if key.startswith('"') and key.endswith('"'):
            key = key[1:-1]
        elif key.startswith("'") and key.endswith("'"):
            key = key[1:-1]
        
        # Parse value
        if value.startswith('"') and value.endswith('"'):
            # Double quoted string
            params[key] = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            # Single quoted string
            params[key] = value[1:-1]
        elif value.startswith('[') and value.endswith(']'):
            # List
            try:
                list_content = value[1:-1].strip()
                if list_content:
                    # Simple list parsing - split by comma and clean quotes
                    items = []
                    for item in list_content.split(','):
                        item = item.strip()
                        if item.startswith('"') and item.endswith('"'):
                            items.append(item[1:-1])
                        elif item.startswith("'") and item.endswith("'"):
                            items.append(item[1:-1])
                        else:
                            items.append(item)
                    params[key] = items
                else:
                    params[key] = []
            except:
                params[key] = value
        elif value.lower() in ['true', 'false']:
            # Boolean
            params[key] = value.lower() == 'true'
        elif value.isdigit():
            # Integer
            params[key] = int(value)
        elif re.match(r'^\d+\.\d+$', value):
            # Float
            params[key] = float(value)
        else:
            # Default to string (unquoted)
            params[key] = value
    
    return params

def call_openai(messages):
    """Call OpenAI API"""
    if not OPENAI_API_KEY:
        return "❌ OpenAI API key not found. Please set OPENAI_API_KEY in .env file."
    
    url = get_llm_api_url()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "max_tokens": 1500,
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=data, verify=get_requests_verify())
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ OpenAI API error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Error calling OpenAI: {str(e)}"

def format_tool_result(result):
    """Format tool result for display"""
    if not result['success']:
        return f"❌ Tool Error: {result['error']}"
    
    data = result['data']
    
    # Format based on result type
    if isinstance(data, list):
        if len(data) == 0:
            return "✅ No results found."
        
        # Format list results
        total_count = len(data)
        show_limit = 50  # Show first 50, then pagination
        
        formatted = f"📊 Found {total_count} results:\n\n"
        
        # Show results up to limit
        display_count = min(total_count, show_limit)
        for i, item in enumerate(data[:display_count], 1):
            if isinstance(item, dict):
                if 'name' in item:  # Monitor/alert format
                    formatted += f"🔴 {i}. {item['name']}\n"
                    formatted += f"   Status: {item.get('status', 'Unknown')}\n"
                    formatted += f"   Priority: {item.get('priority', 'Unknown')}\n"
                elif 'title' in item:  # Dashboard/Event format
                    formatted += f"📈 {i}. {item['title']}\n"
                    formatted += f"   ID: {item.get('id', 'Unknown')}\n"
                    if 'author_handle' in item:
                        formatted += f"   Author: {item.get('author_handle', 'Unknown')}\n"
                    if 'timestamp' in item:
                        formatted += f"   Time: {item.get('timestamp', 'Unknown')}\n"
                elif 'metric' in item:  # Metrics format
                    formatted += f"📊 {i}. {item['metric']}\n"
                    if 'latest_value' in item and item['latest_value'] is not None:
                        formatted += f"   Value: {item['latest_value']:.2f}\n"
                    if 'scope' in item:
                        formatted += f"   Scope: {item.get('scope', 'Unknown')}\n"
                elif 'message' in item:  # Log format
                    formatted += f"📝 {i}. {item.get('message', '')[:100]}...\n"
                    if 'timestamp' in item:
                        formatted += f"   Time: {item.get('timestamp', 'Unknown')}\n"
                    if 'status' in item:
                        formatted += f"   Status: {item.get('status', 'Unknown')}\n"
                else:
                    formatted += f"{i}. {str(item)}\n"
                formatted += "\n"
        
        # Add pagination info if needed
        if total_count > show_limit:
            remaining = total_count - show_limit
            formatted += f"\n📝 **Showing first {show_limit} of {total_count} results**\n"
            formatted += f"⚡ *{remaining} more results available - use filters to narrow down*\n"
        
        return formatted
    
    elif isinstance(data, dict):
        # Format single object
        formatted = "📊 Result:\n"
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                formatted += f"  {key}: {len(value) if isinstance(value, list) else 'object'}\n"
            else:
                formatted += f"  {key}: {value}\n"
        return formatted
    
    else:
        return str(data) 