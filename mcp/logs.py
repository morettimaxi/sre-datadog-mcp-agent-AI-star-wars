import requests
import os
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from colorama import Fore
import urllib3
urllib3.disable_warnings()

# Load environment variables
load_dotenv()
DD_API_KEY = os.getenv('DD_API_KEY')
DD_APP_KEY = os.getenv('DD_APP_KEY')
DD_SITE = os.getenv('DD_SITE', 'api.datadoghq.com')

def parse_time_range(time_range_str="1 hour"):
    """
    Parse time range string and return seconds ago from now.
    
    Examples:
    - "1 hour" -> 3600 seconds
    - "4 hours" -> 14400 seconds  
    - "1 day" -> 86400 seconds
    - "3 days" -> 259200 seconds
    - "1 week" -> 604800 seconds
    """
    import re
    time_range_str = time_range_str.lower().strip()
    
    # Define time multipliers
    multipliers = {
        'hour': 3600,
        'hours': 3600,
        'day': 86400,
        'days': 86400,
        'week': 604800,
        'weeks': 604800,
        'month': 2592000,  # 30 days
        'months': 2592000,
        'minute': 60,
        'minutes': 60
    }
    
    # Try to match pattern like "1 hour", "3 days", "2 weeks"
    match = re.match(r'(\d+)\s+(minute|minutes|hour|hours|day|days|week|weeks|month|months)', time_range_str)
    
    if match:
        number = int(match.group(1))
        unit = match.group(2)
        return number * multipliers[unit]
    
    # Default fallback patterns
    if 'minute' in time_range_str:
        return 60
    elif 'hour' in time_range_str:
        return 3600
    elif 'day' in time_range_str:
        return 86400
    elif 'week' in time_range_str:
        return 604800
    elif 'month' in time_range_str:
        return 2592000
    else:
        # Default to 1 hour for logs
        return 3600

def search_logs_mcp(query="", time_range="1 hour", limit=100, sort="desc", **kwargs):
    """
    MCP Function to search Datadog logs
    
    Args:
        query (str): Log query string (Datadog log search syntax)
        time_range (str): Time range for search (e.g., "15 minutes", "1 hour", "1 day")
        limit (int): Maximum number of log entries to return (max 1000)
        sort (str): Sort order: "asc" or "desc"
    """
    
    # VERIFY KEYS
    if not all([DD_API_KEY, DD_APP_KEY]):
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": []
        }
    
    try:
        print(f"🔄 MCP: Searching logs with query: '{query}' (time_range: {time_range}, limit: {limit})")
        
        # Parse time range
        time_range_seconds = parse_time_range(time_range)
        now = int(time.time())
        time_ago = now - time_range_seconds
        
        # Convert to milliseconds for Datadog API
        time_from = time_ago * 1000
        time_to = now * 1000
        
        print(f"🕒 Query time range: {datetime.fromtimestamp(time_ago)} to {datetime.fromtimestamp(now)}")
        
        # DATADOG LOGS API CALL
        url = f"https://{DD_SITE}/api/v2/logs/events/search"
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Build request payload
        payload = {
            "filter": {
                "from": time_from,
                "to": time_to
            },
            "page": {
                "limit": min(limit, 1000)  # Datadog max is 1000
            },
            "sort": f"timestamp:{sort}"
        }
        
        # Add query if provided
        if query.strip():
            payload["filter"]["query"] = query
        
        response = requests.post(url, headers=headers, json=payload, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('data', [])
            
            # Format log entries for easier reading
            formatted_logs = []
            for log in logs:
                attributes = log.get('attributes', {})
                formatted_log = {
                    "timestamp": attributes.get('timestamp'),
                    "message": attributes.get('message', ''),
                    "status": attributes.get('status', ''),
                    "service": attributes.get('service', ''),
                    "source": attributes.get('source', ''),
                    "host": attributes.get('host', ''),
                    "tags": attributes.get('tags', []),
                    "attributes": {k: v for k, v in attributes.items() 
                                if k not in ['timestamp', 'message', 'status', 'service', 'source', 'host', 'tags']}
                }
                formatted_logs.append(formatted_log)
            
            meta = data.get('meta', {})
            
            return {
                "success": True,
                "error": None,
                "data": formatted_logs,
                "total_logs": len(formatted_logs),
                "meta": meta,
                "query_info": {
                    "query": query,
                    "time_range": time_range,
                    "time_from": datetime.fromtimestamp(time_ago).isoformat(),
                    "time_to": datetime.fromtimestamp(now).isoformat(),
                    "limit": limit,
                    "sort": sort
                }
            }
            
        else:
            return {
                "success": False,
                "error": f"Datadog Logs API error: {response.status_code} - {response.text}",
                "data": []
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "data": []
        }

def get_log_streams_mcp(service=None, source=None, time_range="1 hour", limit=50, **kwargs):
    """
    MCP Function to get log streams by service or source
    
    Args:
        service (str): Filter by service name
        source (str): Filter by source (e.g., 'python', 'nginx', 'docker')
        time_range (str): Time range for logs
        limit (int): Maximum number of log entries to return
    """
    
    # Build query based on filters
    query_parts = []
    if service:
        query_parts.append(f"service:{service}")
    if source:
        query_parts.append(f"source:{source}")
    
    query = " ".join(query_parts)
    
    # Use the search_logs function with the constructed query
    return search_logs_mcp(query=query, time_range=time_range, limit=limit, **kwargs)

def analyze_log_patterns_mcp(query="", time_range="1 hour", **kwargs):
    """
    MCP Function to analyze log patterns and extract insights
    
    Args:
        query (str): Log query string
        time_range (str): Time range for analysis
    """
    
    # Get logs first
    logs_result = search_logs_mcp(query=query, time_range=time_range, limit=1000, **kwargs)
    
    if not logs_result['success']:
        return logs_result
    
    logs = logs_result['data']
    
    if not logs:
        return {
            "success": True,
            "error": None,
            "data": {
                "total_logs": 0,
                "patterns": {},
                "insights": ["No logs found for the specified query and time range."]
            }
        }
    
    # Analyze patterns
    patterns = {
        "status_distribution": {},
        "service_distribution": {},
        "source_distribution": {},
        "host_distribution": {},
        "error_patterns": [],
        "common_messages": {},
        "timeline": {}
    }
    
    insights = []
    
    for log in logs:
        # Status distribution
        status = log.get('status', 'unknown')
        patterns["status_distribution"][status] = patterns["status_distribution"].get(status, 0) + 1
        
        # Service distribution
        service = log.get('service', 'unknown')
        patterns["service_distribution"][service] = patterns["service_distribution"].get(service, 0) + 1
        
        # Source distribution
        source = log.get('source', 'unknown')
        patterns["source_distribution"][source] = patterns["source_distribution"].get(source, 0) + 1
        
        # Host distribution
        host = log.get('host', 'unknown')
        patterns["host_distribution"][host] = patterns["host_distribution"].get(host, 0) + 1
        
        # Error patterns
        message = log.get('message') or ''
        message_lower = message.lower() if message else ''
        if any(error_word in message_lower for error_word in ['error', 'exception', 'failed', 'timeout', 'crash']):
            patterns["error_patterns"].append({
                "timestamp": log.get('timestamp'),
                "service": service,
                "message": message,
                "status": status
            })
        
        # Common messages (first 100 chars)
        message_key = log.get('message', '')[:100]
        patterns["common_messages"][message_key] = patterns["common_messages"].get(message_key, 0) + 1
        
        # Timeline (group by hour)
        if log.get('timestamp'):
            try:
                # Parse timestamp
                if isinstance(log['timestamp'], str):
                    dt = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                else:
                    dt = datetime.fromtimestamp(log['timestamp'] / 1000)
                
                hour_key = dt.strftime('%Y-%m-%d %H:00')
                patterns["timeline"][hour_key] = patterns["timeline"].get(hour_key, 0) + 1
            except:
                pass
    
    # Generate insights
    total_logs = len(logs)
    error_count = len(patterns["error_patterns"])
    
    insights.append(f"📊 Analyzed {total_logs} logs over {time_range}")
    
    if error_count > 0:
        error_percentage = (error_count / total_logs) * 100
        insights.append(f"🔴 Found {error_count} error/exception logs ({error_percentage:.1f}%)")
    else:
        insights.append("✅ No obvious errors found in logs")
    
    # Top services
    if patterns["service_distribution"]:
        top_service = max(patterns["service_distribution"], key=patterns["service_distribution"].get)
        top_service_count = patterns["service_distribution"][top_service]
        insights.append(f"🏆 Top service: {top_service} ({top_service_count} logs)")
    
    # Status insights
    if patterns["status_distribution"]:
        for status, count in patterns["status_distribution"].items():
            percentage = (count / total_logs) * 100
            if status.lower() in ['error', 'critical', 'fatal']:
                insights.append(f"🔴 {status}: {count} logs ({percentage:.1f}%)")
            elif status.lower() in ['warning', 'warn']:
                insights.append(f"🟡 {status}: {count} logs ({percentage:.1f}%)")
            else:
                insights.append(f"ℹ️ {status}: {count} logs ({percentage:.1f}%)")
    
    # Sort patterns by frequency
    for pattern_type in ["status_distribution", "service_distribution", "source_distribution", "host_distribution"]:
        patterns[pattern_type] = dict(sorted(patterns[pattern_type].items(), 
                                           key=lambda x: x[1], reverse=True))
    
    # Sort common messages
    patterns["common_messages"] = dict(sorted(patterns["common_messages"].items(), 
                                            key=lambda x: x[1], reverse=True)[:20])  # Top 20
    
    return {
        "success": True,
        "error": None,
        "data": {
            "total_logs": total_logs,
            "patterns": patterns,
            "insights": insights,
            "query_info": logs_result.get("query_info", {})
        }
    }

def search_error_logs_mcp(time_range="1 hour", limit=100, service=None, **kwargs):
    """
    MCP Function to search for error logs specifically
    
    Args:
        time_range (str): Time range for search
        limit (int): Maximum number of error logs to return
        service (str): Filter by specific service
    """
    
    # Build error query
    error_query = "status:error OR status:critical OR status:fatal OR message:*error* OR message:*exception* OR message:*failed*"
    
    if service:
        error_query = f"({error_query}) AND service:{service}"
    
    return search_logs_mcp(query=error_query, time_range=time_range, limit=limit, **kwargs) 