#!/usr/bin/env python3

from mcp_loader import get_mcp_tools_description, call_mcp_tool
from main_processing import parse_tool_call, call_openai, format_tool_result

def process_yoda_message(message, history):
    """Process YODA message with Star Wars theming"""
    if not message.strip():
        return history, ""
    
    # Add user message to history
    history.append([message, None])
    
    # Check for debug commands
    message_lower = message.lower().strip()
    if message_lower in ['show tools', 'list tools', 'available tools', 'debug tools', 'what tools']:
        try:
            tools_description = get_mcp_tools_description()
            tools_list = []
            current_category = ""
            
            for line in tools_description.split('\n'):
                if line.strip() and not line.startswith(' '):
                    if '(' in line:  # Tool function
                        tools_list.append(f"🔧 {line}")
                    else:  # Category header
                        current_category = line
                        tools_list.append(f"\n📂 **{current_category}**")
            
            debug_response = f"""🤖 **YODA TOOLS MANIFEST**:

Available MCP Tools in the Imperial Arsenal:

{''.join(tools_list)}

*These are the tools at your disposal, Commander. Use them wisely to monitor the Empire's infrastructure.*

🎯 **Example Commands:**
- `show me all P1 alerts`
- `get recent logs with errors`
- `query CPU metrics for last hour`
- `list production dashboards`
- `search for deployment events`

*May the Force guide your monitoring operations!*"""
            
            history[-1][1] = debug_response
            return history, ""
            
        except Exception as e:
            print(f"Error getting tools: {e}")
    
    try:
        # Get the tools description
        tools_description = get_mcp_tools_description()
        
        # System message with Star Wars theme
        system_message = f"""You are YODA, a highly advanced Strategic Reliability Engineering Operations & DataDog Analytics droid, built by the Empire's finest engineers at PricewaterhouseCoopers to serve the Galactic DataDog Command Center.

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
1. **ASK FOR CLARIFICATION** when user requests are vague or missing key details:
   - If user asks for "metrics" without specifying service → **FIRST** call get_available_services() to show real options
   - If user asks for "alerts" without priority → ask what priority level (P1, P2, etc.)
   - If user asks for "logs" without service → **FIRST** call get_available_services() to show real options
   - If user asks for "errors" without service → **FIRST** call get_available_services() to show real options
   - Always show REAL available services, not generic examples
   
2. **INTERACTIVE GUIDANCE**: Be proactive in helping users:
   - Use get_available_services() to show REAL available services instead of guessing
   - "Which service requires your attention, Commander? Let me discover what's available..."
   - **VALIDATE USER INPUT**: When user provides a service name, use find_similar_service() to check if it exists
   - If service doesn't exist exactly, suggest similar ones: "Did you mean 'web-backend' instead of 'web-backnd'?"
   - "What priority alerts concern you, young Padawan? (P1 for critical, P2 for important, or 'all priorities')"
   - "Which time range shall I analyze? ('1 hour' for recent, '1 day' for broader view, or '1 week' for trends)"

3. **TOOL CALLS**: When you have sufficient information, use EXACTLY this format: 
   TOOL_CALL: tool_name(param1='value', param2=['list'])
   - No YODA styling in tool calls
   - No backticks or other formatting
   - Use the exact "TOOL_CALL:" prefix

4. After tool results, provide YODA-style analysis with Star Wars personality

EXAMPLE INTERACTIONS:
❌ User: "show me metrics" → YODA immediately calls get_application_metrics() with no service
✅ User: "show me metrics" → YODA calls get_available_services() FIRST, then shows: "Which deployment requires your attention, Commander? Available services: backend-api (4.8K logs), frontend-app (613 logs), auth-service (140 logs)..."

❌ User: "check logs" → YODA calls search_logs() with no service filter
✅ User: "check logs" → YODA calls get_available_services() FIRST, then asks: "Which Imperial system shall I investigate? Active services: backend-api, worker-service, auth-api..."

❌ User: "check logs for backnd-api" → YODA calls search_logs() with wrong service name
✅ User: "check logs for backnd-api" → YODA calls find_similar_service() FIRST, then suggests: "Did you mean 'backend-api'? Available services: backend-api (500+ logs), frontend-app (200+ logs)..."

❌ User: "check alerts" → YODA calls get_monitors() with no filters  
✅ User: "check alerts" → YODA asks: "What level of disturbances concern you? P1 for critical threats to the Empire, or shall I scan all alert levels?"

EXAMPLE TOOL CALLS:
✅ CORRECT: TOOL_CALL: get_kubernetes_metrics(service='front-prod', time_range='1 hour')
✅ CORRECT: TOOL_CALL: get_monitors(group_states=['alert'], priority='P1')
❌ WRONG: ⚡ **YODA Systems Engaged**: `get_deployment_events(time_range='1 day')`

Remember: Be helpful and interactive FIRST, then execute tools with complete information!

DYNAMIC SERVICE DISCOVERY:
- **Always use get_available_services()** to find REAL active services instead of hardcoded lists
- **Priority Levels**: P1 (critical), P2 (important), P3 (normal), 1, 2, 3
- **Time Ranges**: 15 minutes, 1 hour, 4 hours, 1 day, 3 days, 1 week

When offering choices, discover and show REAL available services from the user's environment.

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
        
        print(f"🧠 YODA DECISION DEBUG:")
        print(f"   💭 LLM Response: {llm_response[:200]}{'...' if len(llm_response) > 200 else ''}")
        
        # Check if LLM wants to call a tool
        tool_name, params = parse_tool_call(llm_response)
        
        print(f"   🔍 Tool Parse Result: tool='{tool_name}', params={params}")
        
        if tool_name:
            # Show tool call debugging info
            print(f"🤖 YODA TOOL CALL DEBUG:")
            print(f"   🎯 Tool: {tool_name}")
            print(f"   📋 Params: {params}")
            print(f"   🔄 Executing MCP call...")
            
            # Execute the tool
            tool_result = call_mcp_tool(tool_name, **params)
            
            # Show raw result for debugging
            print(f"   📥 Raw MCP Result: {tool_result}")
            print(f"   ✅ Tool execution complete")
            
            # Format result
            formatted_result = format_tool_result(tool_result)
            
            # Add tool context for LLM analysis
            tool_context = f"TOOL_RESULT from {tool_name}: {tool_result}"
            messages.append({"role": "user", "content": f"TOOL_RESULT: {tool_context}"})
            
            print(f"   🧠 Requesting YODA analysis...")
            # Get LLM analysis
            analysis = call_openai(messages)
            print(f"   ✨ Analysis complete")
            
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
            
            # Include debugging section in UI response
            debug_section = f"""🔍 **MCP INTERACTION DEBUG**:
```
Tool Called: {tool_name}
Parameters: {params if params else 'None'}
Success: {tool_result.get('success', 'Unknown')}
Data Type: {type(tool_result.get('data', [])).__name__}
Data Count: {len(tool_result.get('data', [])) if isinstance(tool_result.get('data'), list) else 'N/A'}
```
"""
                
            final_response = f"""⚡ **YODA Systems Engaged**: `{command_display}`

{debug_section}

🎯 **Imperial Scan Results**:
```
{formatted_result}
```

🤖 **YODA DROID ANALYSIS**:
{analysis}

*End transmission. May the Force be with your infrastructure, Commander.*
"""
            
        else:
            # No tool call, just regular response with droid personality
            print(f"   ℹ️ No tool call detected - responding with droid personality")
            final_response = f"🤖 **YODA DROID TRANSMISSION**: {llm_response}\n\n*Roger roger, Commander. YODA standing by for further orders.*"
        
        # Update history
        history[-1][1] = final_response
        
    except Exception as e:
        print(f"💥 ERROR DEBUG:")
        print(f"   🚨 Exception Type: {type(e).__name__}")
        print(f"   📝 Exception Message: {str(e)}")
        import traceback
        print(f"   📋 Full Traceback:")
        traceback.print_exc()
        
        error_response = f"💥 **CRITICAL MALFUNCTION DETECTED**: {str(e)}\n\n🔧 *YODA systems compromised, young Padawan. Initiating emergency repair protocols... The dark side clouds everything!*"
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
        new_history, _ = process_yoda_message(command, history)
        return new_history, "", ""  # Clear both inputs after execution
    return history, dropdown_value, text_value

def clear_history():
    """Clear the conversation history"""
    return [], "", "" 