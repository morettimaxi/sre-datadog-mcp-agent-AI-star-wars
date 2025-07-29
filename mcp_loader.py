#!/usr/bin/env python3

import os
import json
import importlib
import urllib3
import requests
from colorama import Fore, Style, init
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# SSL CONFIGURATION BASED ON ENVIRONMENT VARIABLE
SSL_VERIFY = os.getenv('SSL_VERIFY', 'true').lower() in ('true', '1', 'yes', 'on')

# LLM API CONFIGURATION BASED ON ENVIRONMENT VARIABLE
LLM_API_URL = os.getenv('LLM_API_URL', 'https://api.openai.com/v1/chat/completions')

def get_ssl_verify():
    """
    Get SSL verification setting from environment variable
    
    Returns:
        bool: True to verify SSL certificates, False to skip verification
        
    Environment Variable:
        SSL_VERIFY: 'true'/'false', '1'/'0', 'yes'/'no', 'on'/'off'
        Default: 'true' (secure by default)
    """
    return SSL_VERIFY

def configure_ssl_warnings():
    """Configure SSL warnings based on SSL_VERIFY setting"""
    if not SSL_VERIFY:
        # Only disable warnings if SSL verification is disabled
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        if hasattr(requests.packages, 'urllib3'):
            requests.packages.urllib3.disable_warnings()
        print(f"🔒 SSL verification: DISABLED (SSL_VERIFY={os.getenv('SSL_VERIFY', 'true')})")
    else:
        print(f"🔒 SSL verification: ENABLED (SSL_VERIFY={os.getenv('SSL_VERIFY', 'true')})")
    
    # Show LLM API configuration
    llm_env_value = os.getenv('LLM_API_URL')
    if llm_env_value:
        print(f"🤖 LLM API: CUSTOM ({LLM_API_URL})")
    else:
        print(f"🤖 LLM API: DEFAULT (https://api.openai.com/v1/chat/completions)")

# Initialize SSL configuration
configure_ssl_warnings()

# Initialize colorama
init(autoreset=True)

# Export SSL configuration for other modules
def get_requests_verify():
    """
    Get the verify parameter for requests calls
    
    Returns:
        bool: SSL verification setting for requests.get/post calls
    """
    return SSL_VERIFY

def get_llm_api_url():
    """
    Get the LLM API URL from environment variable
    
    Returns:
        str: LLM API URL for chat completions
        
    Environment Variable:
        LLM_API_URL: Custom LLM API endpoint URL
        Default: 'https://api.openai.com/v1/chat/completions'
    """
    return LLM_API_URL

class MCPLoader:
    """
    Dynamic MCP (Model Control Protocol) Loader
    Automatically discovers and loads all available tools from schema files
    """
    
    def __init__(self, schemas_dir="schemas"):
        self.schemas_dir = Path(schemas_dir)
        self.tools = {}
        self.tool_functions = {}
        self.load_all_schemas()
        self.register_functions()
    
    def load_all_schemas(self):
        """Load all JSON schemas from the schemas directory"""
        if not self.schemas_dir.exists():
            print(f"❌ Schemas directory {self.schemas_dir} not found")
            return
        
        schema_files = list(self.schemas_dir.glob("*_schema.json"))
        print(f"🔍 Found {len(schema_files)} schema files")
        
        for schema_file in schema_files:
            try:
                with open(schema_file, 'r') as f:
                    schema = json.load(f)
                    mcp_name = schema['name']
                    self.tools[mcp_name] = schema
                    print(f"✅ Loaded {mcp_name} MCP with {len(schema['tools'])} tools")
            except Exception as e:
                print(f"❌ Error loading {schema_file}: {e}")
    
    def register_functions(self):
        """Register actual Python functions for each tool using dynamic imports"""
        self.tool_functions = {}
        
        for mcp_name, schema in self.tools.items():
            for tool in schema['tools']:
                tool_name = tool['name']
                handler = tool.get('handler')
                
                if not handler:
                    print(f"⚠️ No handler specified for tool: {tool_name}")
                    continue
                
                try:
                    # Parse handler format: "module:function"
                    module_name, function_name = handler.split(':')
                    
                    # Dynamic import
                    module = importlib.import_module(module_name)
                    function = getattr(module, function_name)
                    
                    # Register the function
                    self.tool_functions[tool_name] = function
                    print(f"🔧 Registered {tool_name} → {handler}")
                    
                except Exception as e:
                    print(f"❌ Error registering {tool_name} from {handler}: {e}")
        
        print(f"✅ Successfully registered {len(self.tool_functions)} tool functions")
    
    def get_all_tools_for_llm(self):
        """
        Generate the complete tools description for LLM
        This is what gets sent to the LLM so it knows what tools are available
        """
        tools_description = "# AVAILABLE MCP TOOLS\n\n"
        tools_description += "You have access to the following Datadog MCP tools:\n\n"
        
        for mcp_name, schema in self.tools.items():
            tools_description += f"## {mcp_name.upper()} MCP\n"
            tools_description += f"{schema['description']}\n\n"
            
            for tool in schema['tools']:
                tools_description += f"### {tool['name']}\n"
                tools_description += f"**Description:** {tool['description']}\n\n"
                
                if 'parameters' in tool:
                    tools_description += "**Parameters:**\n"
                    for param_name, param_info in tool['parameters'].items():
                        required = "❌ Optional" if param_info.get('optional', False) else "✅ Required"
                        tools_description += f"- `{param_name}` ({param_info['type']}): {param_info['description']} - {required}\n"
                    tools_description += "\n"
                
                if 'examples' in tool:
                    tools_description += "**Examples:**\n"
                    for example in tool['examples']:
                        tools_description += f"- {example['description']}: `{example['call']}`\n"
                    tools_description += "\n"
                
                tools_description += "---\n\n"
        
        tools_description += "\n## HOW TO USE TOOLS\n"
        tools_description += "When the user asks for something, analyze their request and call the appropriate tool with the correct parameters.\n"
        tools_description += "Format your tool calls as: TOOL_CALL: tool_name(param1='value', param2=['list'])\n"
        tools_description += "Always return the result in a user-friendly format.\n"
        
        return tools_description
    
    def call_tool(self, tool_name, **kwargs):
        """
        Call a tool function dynamically
        """
        if tool_name not in self.tool_functions:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found. Available tools: {list(self.tool_functions.keys())}"
            }
        
        try:
            function = self.tool_functions[tool_name]
            result = function(**kwargs)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Error calling {tool_name}: {str(e)}"
            }
    
    def get_available_tools(self):
        """Get list of all available tool names"""
        return list(self.tool_functions.keys())
    
    def get_tool_info(self, tool_name):
        """Get detailed information about a specific tool"""
        for mcp_name, schema in self.tools.items():
            for tool in schema['tools']:
                if tool['name'] == tool_name:
                    return tool
        return None

# Global loader instance
mcp_loader = MCPLoader()

def get_mcp_tools_description():
    """Get the complete tools description for LLM"""
    return mcp_loader.get_all_tools_for_llm()

def call_mcp_tool(tool_name, **kwargs):
    """Call an MCP tool"""
    return mcp_loader.call_tool(tool_name, **kwargs)

def get_available_mcp_tools():
    """Get list of available tools"""
    return mcp_loader.get_available_tools()

if __name__ == "__main__":
    # Test the loader
    print("🧪 Testing MCP Loader...")
    print(f"Available tools: {get_available_mcp_tools()}")
    print("\n" + "="*50)
    print("TOOLS DESCRIPTION FOR LLM:")
    print("="*50)
    print(get_mcp_tools_description()) 