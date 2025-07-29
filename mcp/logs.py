import requests
import os
import sys
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from colorama import Fore

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_loader import get_requests_verify

# Load environment variables
load_dotenv()
DD_API_KEY = os.getenv('DD_API_KEY')
DD_APP_KEY = os.getenv('DD_APP_KEY')
DD_SITE = os.getenv('DD_SITE', 'api.datadoghq.com')

# Cache configuration
CACHE_FILE = 'services_cache.json'
CACHE_DURATION_HOURS = 4  # Cache expires after 4 hours

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
        print(f"🌐 API URL: {url}")
        
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
        
        print(f"📋 API Payload: {payload}")
        
        response = requests.post(url, headers=headers, json=payload, verify=get_requests_verify())
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('data', [])
            print(f"📥 API Response: {response.status_code} - {len(logs)} logs received")
            print(f"🔍 Raw response keys: {list(data.keys())}")
            
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

def get_available_services_mcp(time_range="1 day", limit=50, force_refresh=False, **kwargs):
    """
    MCP Function to discover available services with recent activity (with intelligent caching)
    
    Args:
        time_range (str): Time range to look for active services
        limit (int): Maximum number of services to return
        force_refresh (bool): Force refresh cache even if valid
    """
    
    # VERIFY KEYS
    if not all([DD_API_KEY, DD_APP_KEY]):
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": []
        }
    
    try:
        print(f"🔍 MCP: Discovering available services with activity in {time_range}")
        
        # Check cache first (unless force refresh)
        if not force_refresh and os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                
                cache_age_hours = (datetime.now() - datetime.fromtimestamp(cache_data['timestamp'])).total_seconds() / 3600
                
                # Check if cache is fresh
                if 'timestamp' in cache_data and cache_age_hours < CACHE_DURATION_HOURS:
                    print(f"✅ Using cached services from {datetime.fromtimestamp(cache_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')} (age: {cache_age_hours:.1f}h)")
                    
                    # Apply limit to cached data
                    limited_services = cache_data['services'][:limit]
                    
                    return {
                        "success": True,
                        "error": None,
                        "data": limited_services,
                        "discovery_info": {
                            "total_services_found": len(cache_data['services']),
                            "returned_services": len(limited_services),
                            "time_range": time_range,
                            "logs_analyzed": cache_data.get('total_logs', 0),
                            "discovery_method": "cache",
                            "cache_age_hours": round(cache_age_hours, 1)
                        }
                    }
                else:
                    print(f"⚠️ Cache expired ({cache_age_hours:.1f}h old, max {CACHE_DURATION_HOURS}h). Refreshing from API.")
            except Exception as e:
                print(f"⚠️ Error loading cache: {e}. Refreshing from API.")
        elif force_refresh:
            print(f"🔄 Force refresh requested. Fetching fresh data from API.")
        
        # Parse time range
        time_range_seconds = parse_time_range(time_range)
        now = int(time.time())
        time_ago = now - time_range_seconds
        
        # Get services from logs (most comprehensive)
        url = f"https://{DD_SITE}/api/v2/logs/events/search"
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Content-Type': 'application/json'
        }
        
        # Query to get logs and extract services
        payload = {
            "filter": {
                "from": time_ago * 1000,  # Convert to milliseconds
                "to": now * 1000,
                "query": "*"  # Get all logs
            },
            "page": {
                "limit": 1000  # Get many logs to find services
            },
            "sort": "timestamp:desc"
        }
        
        response = requests.post(url, headers=headers, json=payload, verify=get_requests_verify())
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('data', [])
            print(f"📥 API Response: {response.status_code} - {len(logs)} logs received for service discovery")
            
            # Extract services from logs
            services_count = {}
            services_info = {}
            
            for log in logs:
                # Get service from log attributes
                service = None
                attributes = log.get('attributes', {})
                
                # Try different ways to get service name
                if 'service' in attributes:
                    service = attributes['service']
                elif 'tags' in attributes:
                    # Look for service tag
                    for tag in attributes['tags']:
                        if tag.startswith('service:'):
                            service = tag.replace('service:', '')
                            break
                
                if service and service.strip():
                    service = service.strip()
                    services_count[service] = services_count.get(service, 0) + 1
                    
                    # Store additional info about the service
                    if service not in services_info:
                        services_info[service] = {
                            'name': service,
                            'log_count': 0,
                            'hosts': set(),
                            'last_seen': None,
                            'environments': set()
                        }
                    
                    services_info[service]['log_count'] += 1
                    
                    # Add host info
                    host = attributes.get('host', '')
                    if host:
                        services_info[service]['hosts'].add(host)
                    
                    # Add environment info
                    env = attributes.get('env', '')
                    if env:
                        services_info[service]['environments'].add(env)
                    
                    # Update last seen
                    timestamp = log.get('timestamp')
                    if timestamp and (not services_info[service]['last_seen'] or timestamp > services_info[service]['last_seen']):
                        services_info[service]['last_seen'] = timestamp
            
            # Convert sets to lists for JSON serialization and sort by activity
            sorted_services = sorted(services_count.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            service_list = []
            for service_name, count in sorted_services:
                info = services_info[service_name]
                service_data = {
                    'name': service_name,
                    'log_count': count,
                    'host_count': len(info['hosts']),
                    'hosts': list(info['hosts'])[:5],  # Limit hosts shown
                    'environments': list(info['environments']),
                    'last_seen': info['last_seen'],
                    'activity_level': 'high' if count > 1000 else 'medium' if count > 100 else 'low'
                }
                service_list.append(service_data)
            
            # Save to cache
            cache_data = {
                'timestamp': int(time.time()),
                'services': service_list,
                'total_logs': len(logs)
            }
            try:
                with open(CACHE_FILE, 'w') as f:
                    json.dump(cache_data, f, indent=4)
                print(f"✅ Services cached to {CACHE_FILE}")
            except Exception as e:
                print(f"⚠️ Error saving cache: {e}")

            return {
                "success": True,
                "error": None,
                "data": service_list,
                "discovery_info": {
                    "total_services_found": len(services_count),
                    "returned_services": len(service_list),
                    "time_range": time_range,
                    "logs_analyzed": len(logs),
                    "discovery_method": "logs_analysis"
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
            "error": f"Exception during service discovery: {str(e)}",
            "data": []
        } 

def find_similar_service_mcp(user_input, threshold=0.6, **kwargs):
    """
    MCP Function to find similar service names using fuzzy matching
    
    Args:
        user_input (str): Service name provided by user (possibly with typos)
        threshold (float): Similarity threshold (0.0 to 1.0)
    """
    
    try:
        # Get available services from cache first
        services_result = get_available_services_mcp(**kwargs)
        
        if not services_result['success']:
            return {
                "success": False,
                "error": "Could not get available services for matching",
                "data": []
            }
        
        available_services = services_result['data']
        service_names = [s['name'] for s in available_services]
        
        user_input_lower = user_input.lower().strip()
        
        # Exact match first
        for service in available_services:
            if service['name'].lower() == user_input_lower:
                return {
                    "success": True,
                    "error": None,
                    "exact_match": True,
                    "service": service,
                    "user_input": user_input,
                    "suggestions": []
                }
        
        # Fuzzy matching using simple similarity
        def similarity(s1, s2):
            """Simple similarity function"""
            s1, s2 = s1.lower(), s2.lower()
            
            # Direct substring match
            if s1 in s2 or s2 in s1:
                return 0.8
            
            # Character overlap ratio
            s1_chars = set(s1)
            s2_chars = set(s2)
            common = len(s1_chars & s2_chars)
            total = len(s1_chars | s2_chars)
            
            if total == 0:
                return 0.0
            
            return common / total
        
        # Find similar services
        similarities = []
        for service in available_services:
            service_name = service['name']
            sim_score = similarity(user_input_lower, service_name)
            
            if sim_score >= threshold:
                similarities.append({
                    'service': service,
                    'similarity': sim_score,
                    'name': service_name
                })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            "success": True,
            "error": None,
            "exact_match": False,
            "user_input": user_input,
            "suggestions": similarities[:5],  # Top 5 suggestions
            "available_services": service_names,
            "similarity_threshold": threshold
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in similarity matching: {str(e)}",
            "data": []
        } 