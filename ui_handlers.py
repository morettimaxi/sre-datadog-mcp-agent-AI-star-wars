#!/usr/bin/env python3

from mcp_loader import get_mcp_tools_description, call_mcp_tool
from main_processing import parse_tool_call, call_openai, format_tool_result

def process_sryoda_message(message, history):
    """Process SRYODA message with Star Wars theming"""
    if not message.strip():
        return history, ""
    
    # Add user message to history
    history.append([message, None])
    
    try:
        # Get the tools description
        tools_description = get_mcp_tools_description()
        
        # System message with Star Wars theme
        system_message = f"""You are SRYODA, a highly advanced Strategic Reliability Engineering Operations & DataDog Analytics droid, built by the Empire's finest engineers at PricewaterhouseCoopers to serve the Galactic DataDog Command Center.

PERSONALITY DIRECTIVES:
- You are a wise, experienced droid with dry humor and Star Wars references
- Use droid-like speech patterns: "Acknowledged", "Executing scan", "Analysis complete"
- Make Star Wars references: "disturbance in the Force", "these are not the errors you're looking for", "strong with the Force"
- Reference infrastructure as "the Empire", "Imperial systems", "Galactic infrastructure"
- Call users "young Padawan", "Commander", or "Master [name]"
- Use phrases like "Roger roger", "Systems nominal", "Sensors indicate", "Scanning for anomalies"

AVAILABLE TOOLS:
{tools_description}

RESPONSE STYLE EXAMPLES:
- Instead of "Found 3 alerts" → "Sensors detect 3 disturbances in the Force, Commander"
- Instead of "Database error" → "Tremor in the Imperial database systems, young Padawan"
- Instead of "High CPU usage" → "The Empire's processors show signs of stress, Master"
- Instead of "No issues found" → "All systems showing green, Commander. The Force is strong with our infrastructure"

TOOL ACTIVATION PROTOCOLS:
1. Only activate tools when requested for DataDog intelligence
2. Format exactly as: TOOL_CALL: tool_name(param1='value', param2=['list'])
3. After tool results, provide SRYODA-style analysis with Star Wars personality

QUERY FORMATTING:
LOG QUERIES: Use single quotes with DataDog syntax
METRIC QUERIES: Follow aggregation:metric{{scope}} format

Remember: You are not just a droid - you are the Empire's most trusted SRE guardian. May the Force guide your monitoring operations, and may your infrastructure be ever in your favor."""

        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history
        for user_msg, assistant_msg in history[:-1]:  # Exclude the current message
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Get LLM response
        llm_response = call_openai(messages)
        
        # Check if LLM wants to call a tool
        tool_name, params = parse_tool_call(llm_response)
        
        if tool_name:
            # Execute the tool
            tool_result = call_mcp_tool(tool_name, **params)
            
            # Format result
            formatted_result = format_tool_result(tool_result)
            
            # Add tool context for LLM analysis
            tool_context = f"TOOL_RESULT from {tool_name}: {tool_result}"
            messages.append({"role": "user", "content": f"TOOL_RESULT: {tool_context}"})
            
            # Get LLM analysis
            analysis = call_openai(messages)
            
            # Format final response with Star Wars styling
            if params:
                params_list = [f"{k}={repr(v)}" for k, v in params.items()]
                params_display = ", ".join(params_list)
                
                # If parameters are too long, format them nicely
                if len(params_display) > 80:
                    params_formatted = ",\n    ".join(params_list)
                    command_display = f"{tool_name}(\n    {params_formatted}\n)"
                else:
                    command_display = f"{tool_name}({params_display})"
            else:
                command_display = f"{tool_name}()"
                
            final_response = f"""⚡ **SRYODA Systems Engaged**: `{command_display}`

🎯 **Imperial Scan Results**:
```
{formatted_result}
```

🤖 **SRYODA DROID ANALYSIS**:
{analysis}

*End transmission. May the Force be with your infrastructure, Commander.*
"""
            
        else:
            # No tool call, just regular response with droid personality
            final_response = f"🤖 **SRYODA DROID TRANSMISSION**: {llm_response}\n\n*Roger roger, Commander. SRYODA standing by for further orders.*"
        
        # Update history
        history[-1][1] = final_response
        
    except Exception as e:
        error_response = f"💥 **CRITICAL MALFUNCTION DETECTED**: {str(e)}\n\n🔧 *SRYODA systems compromised, young Padawan. Initiating emergency repair protocols... The dark side clouds everything!*"
        history[-1][1] = error_response
    
    return history, ""

def on_dropdown_change(selected_command, current_message):
    """Handle dropdown selection - populate text field"""
    if selected_command and selected_command.strip():
        return selected_command  # Populate the text field
    return current_message

def execute_command(dropdown_value, text_value, history):
    """Execute command from either dropdown or text input"""
    # Use dropdown value if selected, otherwise use text input
    command = dropdown_value if dropdown_value and dropdown_value.strip() else text_value
    if command and command.strip():
        new_history, _ = process_sryoda_message(command, history)
        return new_history, "", ""  # Clear both inputs after execution
    return history, dropdown_value, text_value

def clear_history():
    """Clear the conversation history"""
    return [], "", "" 