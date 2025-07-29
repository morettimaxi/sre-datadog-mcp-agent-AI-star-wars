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
        # Default to 1 day for events
        return 86400

def search_events_mcp(query="", time_range="1 day", priority=None, sources=None, tags=None, limit=100, **kwargs):
    """
    MCP Function to search Datadog events
    
    Args:
        query (str): Event search query (text search in event titles and text)
        time_range (str): Time range for search (e.g., "1 hour", "1 day", "1 week")
        priority (str): Event priority filter ("low", "normal", "high")
        sources (list): List of source filters (e.g., ["my apps", "chef", "puppet"])
        tags (list): List of tags to filter by
        limit (int): Maximum number of events to return
    """
    
    # VERIFY KEYS
    if not all([DD_API_KEY, DD_APP_KEY]):
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": []
        }
    
    try:
        print(f"🔄 MCP: Searching events with query: '{query}' (time_range: {time_range}, limit: {limit})")
        
        # Parse time range
        time_range_seconds = parse_time_range(time_range)
        now = int(time.time())
        time_ago = now - time_range_seconds
        
        print(f"🕒 Query time range: {datetime.fromtimestamp(time_ago)} to {datetime.fromtimestamp(now)}")
        
        # DATADOG EVENTS API CALL
        url = f"https://{DD_SITE}/api/v1/events"
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json'
        }
        
        # Build query parameters
        params = {
            'start': time_ago,
            'end': now
        }
        
        if priority:
            params['priority'] = priority
        
        if sources:
            params['sources'] = ','.join(sources)
        
        if tags:
            params['tags'] = ','.join(tags)
        
        response = requests.get(url, headers=headers, params=params, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"📥 API Response: {response.status_code} - {len(events)} events received")
            print(f"🔍 Raw response keys: {list(data.keys())}")
            
            # Filter by text query if provided
            if query.strip():
                print(f"🔍 Applying text filter for query: '{query}'")
                filtered_events = []
                query_lower = query.lower()
                for event in events:
                    title = event.get('title') or ''
                    text = event.get('text') or ''
                    title = title.lower() if title else ''
                    text = text.lower() if text else ''
                    if query_lower in title or query_lower in text:
                        filtered_events.append(event)
                events = filtered_events
                print(f"🎯 After text filtering: {len(events)} events remain")
            
            # Limit results
            events = events[:limit]
            print(f"📊 Final result: {len(events)} events (after limit={limit})")
            
            # Format events for easier reading
            formatted_events = []
            for event in events:
                formatted_event = {
                    "id": event.get('id'),
                    "title": event.get('title', ''),
                    "text": event.get('text', ''),
                    "date_happened": event.get('date_happened'),
                    "timestamp": datetime.fromtimestamp(event.get('date_happened', 0)).isoformat() if event.get('date_happened') else None,
                    "priority": event.get('priority', 'normal'),
                    "source_type_name": event.get('source_type_name', ''),
                    "host": event.get('host', ''),
                    "tags": event.get('tags', []),
                    "url": event.get('url', ''),
                    "alert_type": event.get('alert_type', ''),
                    "aggregation_key": event.get('aggregation_key', ''),
                    "source": event.get('source', '')
                }
                formatted_events.append(formatted_event)
            
            return {
                "success": True,
                "error": None,
                "data": formatted_events,
                "total_events": len(formatted_events),
                "query_info": {
                    "query": query,
                    "time_range": time_range,
                    "time_from": datetime.fromtimestamp(time_ago).isoformat(),
                    "time_to": datetime.fromtimestamp(now).isoformat(),
                    "priority": priority,
                    "sources": sources,
                    "tags": tags,
                    "limit": limit
                }
            }
            
        else:
            return {
                "success": False,
                "error": f"Datadog Events API error: {response.status_code} - {response.text}",
                "data": []
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "data": []
        }

def get_recent_events_mcp(time_range="4 hours", limit=50, priority=None, **kwargs):
    """
    MCP Function to get recent events with optional priority filtering
    
    Args:
        time_range (str): Time range for events
        limit (int): Maximum number of events to return
        priority (str): Filter by priority ("low", "normal", "high")
    """
    
    return search_events_mcp(
        query="",
        time_range=time_range,
        priority=priority,
        limit=limit,
        **kwargs
    )

def get_deployment_events_mcp(time_range="1 day", service=None, limit=50, **kwargs):
    """
    MCP Function to get deployment-related events
    
    Args:
        time_range (str): Time range for deployment events
        service (str): Filter by specific service name
        limit (int): Maximum number of events to return
    """
    
    # Try multiple deployment-related searches and combine results
    deployment_queries = []
    
    if service:
        # Service-specific queries
        deployment_queries = [
            f"deployment {service}",
            f"deploy {service}", 
            f"{service} deployment",
            f"{service} updated"
        ]
    else:
        # General deployment queries
        deployment_queries = [
            "deployment updated",
            "kubernetes deployment", 
            "service updated",
            "deploy",
            "release"
        ]
    
    all_events = []
    seen_event_ids = set()
    
    # Search with each query and combine unique results
    for query in deployment_queries:
        result = search_events_mcp(
            query=query,
            time_range=time_range,
            limit=limit,
            **kwargs
        )
        
        if result['success'] and result['data']:
            for event in result['data']:
                event_id = event.get('id')
                if event_id and event_id not in seen_event_ids:
                    all_events.append(event)
                    seen_event_ids.add(event_id)
    
    # Sort by timestamp (newest first)
    all_events.sort(key=lambda x: x.get('date_happened', 0), reverse=True)
    
    # Limit final results
    final_events = all_events[:limit]
    
    return {
        "success": True,
        "error": None,
        "data": final_events,
        "total_events": len(final_events),
        "deployment_queries_used": deployment_queries,
        "service_filter": service,
        "time_range": time_range
    }

def analyze_event_patterns_mcp(time_range="1 day", **kwargs):
    """
    MCP Function to analyze event patterns and extract insights
    
    Args:
        time_range (str): Time range for analysis
    """
    
    # Get events first
    events_result = search_events_mcp(query="", time_range=time_range, limit=1000, **kwargs)
    
    if not events_result['success']:
        return events_result
    
    events = events_result['data']
    
    if not events:
        return {
            "success": True,
            "error": None,
            "data": {
                "total_events": 0,
                "patterns": {},
                "insights": ["No events found for the specified time range."]
            }
        }
    
    # Analyze patterns
    patterns = {
        "priority_distribution": {},
        "source_distribution": {},
        "alert_type_distribution": {},
        "host_distribution": {},
        "deployment_events": [],
        "error_events": [],
        "timeline": {},
        "tags_analysis": {}
    }
    
    insights = []
    
    for event in events:
        # Priority distribution
        priority = event.get('priority', 'normal')
        patterns["priority_distribution"][priority] = patterns["priority_distribution"].get(priority, 0) + 1
        
        # Source distribution
        source = event.get('source_type_name', 'unknown')
        if not source:
            source = event.get('source', 'unknown')
        patterns["source_distribution"][source] = patterns["source_distribution"].get(source, 0) + 1
        
        # Alert type distribution
        alert_type = event.get('alert_type', 'info')
        patterns["alert_type_distribution"][alert_type] = patterns["alert_type_distribution"].get(alert_type, 0) + 1
        
        # Host distribution
        host = event.get('host', 'unknown')
        if host and host != 'unknown':
            patterns["host_distribution"][host] = patterns["host_distribution"].get(host, 0) + 1
        
        # Deployment events
        title = event.get('title') or ''
        text = event.get('text') or ''
        title_lower = title.lower() if title else ''
        text_lower = text.lower() if text else ''
        if any(term in title_lower or term in text_lower for term in ['deploy', 'deployment', 'release', 'version']):
            patterns["deployment_events"].append({
                "timestamp": event.get('timestamp'),
                "title": title,
                "host": event.get('host', ''),
                "priority": priority,
                "source": source
            })
        
        # Error events
        if any(term in title_lower or term in text_lower for term in ['error', 'failed', 'exception', 'crash', 'down']):
            patterns["error_events"].append({
                "timestamp": event.get('timestamp'),
                "title": title,
                "priority": priority,
                "alert_type": alert_type,
                "host": event.get('host', '')
            })
        
        # Timeline (group by hour)
        if event.get('date_happened'):
            try:
                dt = datetime.fromtimestamp(event['date_happened'])
                hour_key = dt.strftime('%Y-%m-%d %H:00')
                patterns["timeline"][hour_key] = patterns["timeline"].get(hour_key, 0) + 1
            except:
                pass
        
        # Tags analysis
        tags = event.get('tags', [])
        for tag in tags:
            if ':' in tag:
                tag_key, tag_value = tag.split(':', 1)
                if tag_key not in patterns["tags_analysis"]:
                    patterns["tags_analysis"][tag_key] = {}
                patterns["tags_analysis"][tag_key][tag_value] = patterns["tags_analysis"][tag_key].get(tag_value, 0) + 1
    
    # Generate insights
    total_events = len(events)
    deployment_count = len(patterns["deployment_events"])
    error_count = len(patterns["error_events"])
    
    insights.append(f"📊 Analyzed {total_events} events over {time_range}")
    
    if deployment_count > 0:
        insights.append(f"🚀 Found {deployment_count} deployment-related events")
    
    if error_count > 0:
        error_percentage = (error_count / total_events) * 100
        insights.append(f"🔴 Found {error_count} error/failure events ({error_percentage:.1f}%)")
    else:
        insights.append("✅ No obvious error events found")
    
    # Priority insights
    if patterns["priority_distribution"]:
        for priority, count in patterns["priority_distribution"].items():
            percentage = (count / total_events) * 100
            if priority == 'high':
                insights.append(f"🔴 High priority: {count} events ({percentage:.1f}%)")
            elif priority == 'normal':
                insights.append(f"🟡 Normal priority: {count} events ({percentage:.1f}%)")
            else:
                insights.append(f"ℹ️ {priority} priority: {count} events ({percentage:.1f}%)")
    
    # Top sources
    if patterns["source_distribution"]:
        top_source = max(patterns["source_distribution"], key=patterns["source_distribution"].get)
        top_source_count = patterns["source_distribution"][top_source]
        insights.append(f"🏆 Top event source: {top_source} ({top_source_count} events)")
    
    # Sort patterns by frequency
    for pattern_type in ["priority_distribution", "source_distribution", "alert_type_distribution", "host_distribution"]:
        if patterns[pattern_type]:
            patterns[pattern_type] = dict(sorted(patterns[pattern_type].items(), 
                                               key=lambda x: x[1], reverse=True))
    
    # Sort timeline
    if patterns["timeline"]:
        patterns["timeline"] = dict(sorted(patterns["timeline"].items()))
    
    return {
        "success": True,
        "error": None,
        "data": {
            "total_events": total_events,
            "patterns": patterns,
            "insights": insights,
            "query_info": events_result.get("query_info", {})
        }
    }

def get_alert_events_mcp(time_range="4 hours", limit=100, **kwargs):
    """
    MCP Function to get alert and monitoring events specifically
    
    Args:
        time_range (str): Time range for alert events
        limit (int): Maximum number of alert events to return
    """
    
    # Search for events with alert-related terms
    alert_query = "alert OR monitor OR triggered OR warning OR critical"
    
    return search_events_mcp(
        query=alert_query,
        time_range=time_range,
        limit=limit,
        **kwargs
    ) 