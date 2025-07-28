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
        # Default to 1 hour for metrics
        return 3600

def query_metrics_mcp(query, time_range="1 hour", **kwargs):
    """
    MCP Function to query Datadog metrics
    
    Args:
        query (str): Metric query string (e.g., "avg:system.cpu.user{*}", "sum:aws.elb.request_count{*}")
        time_range (str): Time range for query (e.g., "1 hour", "1 day", "1 week")
    """
    
    # VERIFY KEYS
    if not all([DD_API_KEY, DD_APP_KEY]):
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": []
        }
    
    if not query.strip():
        return {
            "success": False,
            "error": "Query parameter is required",
            "data": []
        }
    
    try:
        print(f"🔄 MCP: Querying metrics: '{query}' (time_range: {time_range})")
        
        # Parse time range
        time_range_seconds = parse_time_range(time_range)
        now = int(time.time())
        time_ago = now - time_range_seconds
        
        print(f"🕒 Query time range: {datetime.fromtimestamp(time_ago)} to {datetime.fromtimestamp(now)}")
        
        # DATADOG METRICS API CALL
        url = f"https://{DD_SITE}/api/v1/query"
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json'
        }
        
        # Build query parameters
        params = {
            'query': query,
            'from': time_ago,
            'to': now
        }
        
        response = requests.get(url, headers=headers, params=params, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            series = data.get('series', [])
            
            # Format metrics data for easier reading
            formatted_metrics = []
            for serie in series:
                metric_data = {
                    "metric": serie.get('metric', ''),
                    "scope": serie.get('scope', {}),
                    "pointlist": serie.get('pointlist', []),
                    "data_points_count": len(serie.get('pointlist', [])),
                    "latest_value": None,
                    "latest_timestamp": None,
                    "min_value": None,
                    "max_value": None,
                    "avg_value": None
                }
                
                # Calculate statistics
                pointlist = serie.get('pointlist', [])
                if pointlist:
                    values = [point[1] for point in pointlist if point[1] is not None]
                    if values:
                        metric_data["latest_value"] = pointlist[-1][1]
                        metric_data["latest_timestamp"] = datetime.fromtimestamp(pointlist[-1][0] / 1000).isoformat()
                        metric_data["min_value"] = min(values)
                        metric_data["max_value"] = max(values)
                        metric_data["avg_value"] = sum(values) / len(values)
                
                formatted_metrics.append(metric_data)
            
            return {
                "success": True,
                "error": None,
                "data": formatted_metrics,
                "total_series": len(formatted_metrics),
                "query_info": {
                    "query": query,
                    "time_range": time_range,
                    "time_from": datetime.fromtimestamp(time_ago).isoformat(),
                    "time_to": datetime.fromtimestamp(now).isoformat()
                }
            }
            
        else:
            return {
                "success": False,
                "error": f"Datadog Metrics API error: {response.status_code} - {response.text}",
                "data": []
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "data": []
        }

def search_metrics_mcp(metric_name="", **kwargs):
    """
    MCP Function to search for available metrics
    
    Args:
        metric_name (str): Partial metric name to search for (e.g., "cpu", "memory", "aws.elb")
    """
    
    # VERIFY KEYS
    if not all([DD_API_KEY, DD_APP_KEY]):
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": []
        }
    
    try:
        print(f"🔄 MCP: Searching metrics with name filter: '{metric_name}'")
        
        # DATADOG METRICS SEARCH API CALL
        url = f"https://{DD_SITE}/api/v1/search"
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json'
        }
        
        # Build query parameters
        params = {}
        if metric_name.strip():
            params['q'] = f"metrics:{metric_name}"
        else:
            params['q'] = "metrics:*"
        
        response = requests.get(url, headers=headers, params=params, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            metrics = data.get('results', {}).get('metrics', [])
            
            # Format metrics list
            formatted_metrics = []
            for metric in metrics:
                formatted_metrics.append({
                    "name": metric,
                    "type": "metric"
                })
            
            return {
                "success": True,
                "error": None,
                "data": formatted_metrics,
                "total_metrics": len(formatted_metrics),
                "search_term": metric_name
            }
            
        else:
            return {
                "success": False,
                "error": f"Datadog Metrics Search API error: {response.status_code} - {response.text}",
                "data": []
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "data": []
        }

def get_metric_metadata_mcp(metric_name, **kwargs):
    """
    MCP Function to get metadata for a specific metric
    
    Args:
        metric_name (str): Name of the metric (e.g., "system.cpu.user", "aws.elb.request_count")
    """
    
    # VERIFY KEYS
    if not all([DD_API_KEY, DD_APP_KEY]):
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": None
        }
    
    if not metric_name.strip():
        return {
            "success": False,
            "error": "metric_name parameter is required",
            "data": None
        }
    
    try:
        print(f"🔄 MCP: Getting metadata for metric: '{metric_name}'")
        
        # DATADOG METRICS METADATA API CALL
        url = f"https://{DD_SITE}/api/v1/metrics/{metric_name}"
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            
            return {
                "success": True,
                "error": None,
                "data": data
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "error": f"Metric '{metric_name}' not found",
                "data": None
            }
        else:
            return {
                "success": False,
                "error": f"Datadog Metrics Metadata API error: {response.status_code} - {response.text}",
                "data": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "data": None
        }

def analyze_metric_trends_mcp(query, time_range="4 hours", **kwargs):
    """
    MCP Function to analyze metric trends and extract insights
    
    Args:
        query (str): Metric query string
        time_range (str): Time range for analysis
    """
    
    # Get metrics data first
    metrics_result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
    
    if not metrics_result['success']:
        return metrics_result
    
    metrics_data = metrics_result['data']
    
    if not metrics_data:
        return {
            "success": True,
            "error": None,
            "data": {
                "total_series": 0,
                "trends": {},
                "insights": ["No metric data found for the specified query and time range."]
            }
        }
    
    # Analyze trends
    trends = {
        "summary": {
            "total_series": len(metrics_data),
            "series_with_data": 0,
            "latest_values": [],
            "value_ranges": []
        },
        "anomalies": [],
        "patterns": []
    }
    
    insights = []
    
    for metric in metrics_data:
        if metric['data_points_count'] > 0:
            trends["summary"]["series_with_data"] += 1
            
            if metric['latest_value'] is not None:
                trends["summary"]["latest_values"].append({
                    "metric": metric['metric'],
                    "scope": metric['scope'],
                    "value": metric['latest_value'],
                    "timestamp": metric['latest_timestamp']
                })
            
            # Value range analysis
            if metric['min_value'] is not None and metric['max_value'] is not None:
                value_range = metric['max_value'] - metric['min_value']
                variance_ratio = value_range / metric['avg_value'] if metric['avg_value'] != 0 else 0
                
                trends["summary"]["value_ranges"].append({
                    "metric": metric['metric'],
                    "min": metric['min_value'],
                    "max": metric['max_value'],
                    "avg": metric['avg_value'],
                    "range": value_range,
                    "variance_ratio": variance_ratio
                })
                
                # Detect anomalies
                if variance_ratio > 2.0:  # High variance
                    trends["anomalies"].append({
                        "type": "high_variance",
                        "metric": metric['metric'],
                        "variance_ratio": variance_ratio,
                        "description": f"High variance detected (ratio: {variance_ratio:.2f})"
                    })
                
                # Detect patterns
                pointlist = metric['pointlist']
                if len(pointlist) >= 3:
                    # Simple trend detection
                    recent_values = [point[1] for point in pointlist[-3:] if point[1] is not None]
                    if len(recent_values) == 3:
                        if recent_values[2] > recent_values[1] > recent_values[0]:
                            trends["patterns"].append({
                                "type": "increasing_trend",
                                "metric": metric['metric'],
                                "description": "Increasing trend detected in recent values"
                            })
                        elif recent_values[2] < recent_values[1] < recent_values[0]:
                            trends["patterns"].append({
                                "type": "decreasing_trend",
                                "metric": metric['metric'],
                                "description": "Decreasing trend detected in recent values"
                            })
    
    # Generate insights
    total_series = trends["summary"]["total_series"]
    series_with_data = trends["summary"]["series_with_data"]
    
    insights.append(f"📊 Analyzed {total_series} metric series over {time_range}")
    insights.append(f"📈 {series_with_data} series have data points")
    
    if trends["anomalies"]:
        insights.append(f"⚠️ Found {len(trends['anomalies'])} anomalies:")
        for anomaly in trends["anomalies"]:
            insights.append(f"  • {anomaly['metric']}: {anomaly['description']}")
    
    if trends["patterns"]:
        insights.append(f"📈 Found {len(trends['patterns'])} patterns:")
        for pattern in trends["patterns"]:
            insights.append(f"  • {pattern['metric']}: {pattern['description']}")
    
    # Latest values summary
    latest_values = trends["summary"]["latest_values"]
    if latest_values:
        insights.append(f"🔢 Latest values:")
        for value_info in latest_values[:5]:  # Show first 5
            scope_str = f" ({value_info['scope']})" if value_info['scope'] else ""
            insights.append(f"  • {value_info['metric']}{scope_str}: {value_info['value']:.2f}")
    
    return {
        "success": True,
        "error": None,
        "data": {
            "trends": trends,
            "insights": insights,
            "query_info": metrics_result.get("query_info", {})
        }
    }

def get_system_metrics_mcp(time_range="1 hour", host=None, **kwargs):
    """
    MCP Function to get common system metrics (CPU, memory, disk)
    
    Args:
        time_range (str): Time range for metrics
        host (str): Filter by specific host
    """
    
    # Build host filter
    host_filter = f"{{host:{host}}}" if host else "{*}"
    
    # Common system metrics
    system_queries = [
        f"avg:system.cpu.user{host_filter}",
        f"avg:system.mem.used{host_filter}",
        f"avg:system.disk.used{host_filter}",
        f"avg:system.load.1{host_filter}"
    ]
    
    results = []
    for query in system_queries:
        result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
        if result['success']:
            results.extend(result['data'])
    
    return {
        "success": True,
        "error": None,
        "data": results,
        "host_filter": host,
        "time_range": time_range,
        "metrics_queried": system_queries
    }

def get_application_metrics_mcp(service=None, time_range="1 hour", **kwargs):
    """
    MCP Function to get application metrics (requests, errors, latency)
    
    Args:
        service (str): Filter by specific service name
        time_range (str): Time range for metrics
    """
    
    # Build service filter
    service_filter = f"{{service:{service}}}" if service else "{*}"
    
    # Common application metrics
    app_queries = [
        f"sum:trace.requests{service_filter}",
        f"avg:trace.response_time{service_filter}",
        f"sum:trace.errors{service_filter}",
        f"avg:runtime.python.cpu.percent{service_filter}" if not service or "python" in service.lower() else f"avg:jvm.cpu.load{service_filter}"
    ]
    
    results = []
    for query in app_queries:
        result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
        if result['success']:
            results.extend(result['data'])
    
    return {
        "success": True,
        "error": None,
        "data": results,
        "service_filter": service,
        "time_range": time_range,
        "metrics_queried": app_queries
    } 