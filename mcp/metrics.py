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
        print(f"🌐 API URL: {url}")
        
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json'
        }
        
        params = {
            'query': query,
            'from': time_ago,
            'to': now
        }
        
        print(f"📋 API Params: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            series = data.get('series', [])
            print(f"📥 API Response: {response.status_code} - {len(series)} metrics series received")
            print(f"🔍 Raw response keys: {list(data.keys())}")
            
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

def get_kubernetes_metrics_mcp(service=None, time_range="1 hour", **kwargs):
    """
    MCP Function to get Kubernetes metrics (CPU, memory, pods)
    
    Args:
        service (str): Kubernetes service/deployment name (e.g., 'front-prod', 'api-service')
        time_range (str): Time range for metrics
    """
    
    # Build service filter for Kubernetes
    if service:
        service_filter = f"{{kube_deployment:{service}}}"
    else:
        service_filter = "{*}"
    
    # Kubernetes metrics queries
    k8s_queries = [
        f"avg:kubernetes.cpu.usage.total{service_filter}",
        f"avg:kubernetes.memory.usage{service_filter}",
        f"avg:kubernetes.memory.working_set{service_filter}",
        f"sum:kubernetes.containers.running{service_filter}",
        f"avg:kubernetes.cpu.limits{service_filter}",
        f"avg:kubernetes.memory.limits{service_filter}"
    ]
    
    results = []
    for query in k8s_queries:
        result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
        if result['success']:
            results.extend(result['data'])
    
    return {
        "success": True,
        "error": None,
        "data": results,
        "service_filter": service,
        "time_range": time_range,
        "metrics_queried": k8s_queries,
        "deployment_name": service
    } 

def get_apm_metrics_mcp(service=None, time_range="1 hour", metric_types=None, limit=20, **kwargs):
    """
    MCP Function to get APM metrics using auto-discovery (NO hardcoding)
    
    Args:
        service (str): Filter by service name (will search in metric names)
        time_range (str): Time range for metrics
        metric_types (list): Types of metrics to fetch (auto-discovered if not provided)
        limit (int): Maximum number of metrics to analyze
    """
    
    # Step 1: Get ALL trace metrics (auto-discovery)
    trace_search = search_metrics_mcp(metric_name='trace')
    
    if not trace_search['success']:
        return {
            "success": False,
            "error": "Failed to search for trace metrics",
            "data": []
        }
    
    available_metrics = trace_search['data']
    metric_names = [m['name'] for m in available_metrics]
    
    print(f"🔍 Auto-discovery: Found {len(metric_names)} trace metrics")
    
    # Step 2: AUTO-DISCOVER metric types by analyzing suffixes
    discovered_types = {}
    service_patterns = {}
    operation_patterns = {}
    
    for metric_name in metric_names:
        # Extract metric type (everything after last dot)
        if '.' in metric_name:
            metric_type = metric_name.split('.')[-1]
            discovered_types[metric_type] = discovered_types.get(metric_type, 0) + 1
        
        # Extract service patterns (trace.SERVICE.operation.type)
        parts = metric_name.replace('trace.', '').split('.')
        if len(parts) >= 2:
            service_part = parts[0]
            operation_part = '.'.join(parts[1:-1]) if len(parts) > 2 else parts[0]
            
            service_patterns[service_part] = service_patterns.get(service_part, 0) + 1
            operation_patterns[operation_part] = operation_patterns.get(operation_part, 0) + 1
    
    # Step 3: Use discovered types or provided ones
    if not metric_types:
        # Use top discovered types
        metric_types = sorted(discovered_types.keys(), key=lambda x: discovered_types[x], reverse=True)[:5]
        print(f"📊 Auto-discovered metric types: {metric_types}")
    
    # Step 4: Smart filtering based on service
    filtered_metrics = []
    
    if service:
        print(f"🎯 Filtering for service: '{service}'")
        # Multiple strategies for service matching
        for metric_name in metric_names:
            service_lower = service.lower()
            metric_lower = metric_name.lower()
            
            # Strategy 1: Direct service name match
            if service_lower in metric_lower:
                filtered_metrics.append(metric_name)
                continue
            
            # Strategy 2: Service as part of operation
            parts = metric_name.replace('trace.', '').split('.')
            if any(service_lower in part.lower() for part in parts):
                filtered_metrics.append(metric_name)
                continue
    else:
        filtered_metrics = metric_names
    
    # Step 5: Filter by metric types
    type_filtered_metrics = []
    for metric_name in filtered_metrics:
        for metric_type in metric_types:
            if metric_name.endswith(f'.{metric_type}'):
                type_filtered_metrics.append(metric_name)
                break
    
    # Step 6: Smart sampling (no hardcoded patterns)
    if len(type_filtered_metrics) > limit:
        # Prioritize by frequency of operation patterns
        scored_metrics = []
        for metric_name in type_filtered_metrics:
            parts = metric_name.replace('trace.', '').split('.')
            operation = '.'.join(parts[:-1]) if len(parts) > 1 else parts[0]
            frequency_score = operation_patterns.get(operation, 0)
            scored_metrics.append((metric_name, frequency_score))
        
        # Sort by frequency and take top ones
        scored_metrics.sort(key=lambda x: x[1], reverse=True)
        final_metrics = [m[0] for m in scored_metrics[:limit]]
    else:
        final_metrics = type_filtered_metrics
    
    print(f"📈 Querying {len(final_metrics)} metrics out of {len(type_filtered_metrics)} candidates")
    
    # Step 7: Query actual metrics
    results = []
    queries_made = []
    
    for metric_name in final_metrics:
        query = f"avg:{metric_name}{{*}}"
        queries_made.append(query)
        
        result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
        if result['success'] and result['data']:
            # Auto-detect metric type and operation from name
            parts = metric_name.replace('trace.', '').split('.')
            metric_type = parts[-1] if parts else 'unknown'
            operation = '.'.join(parts[:-1]) if len(parts) > 1 else parts[0] if parts else 'unknown'
            
            for data_point in result['data']:
                data_point['metric_type'] = metric_type
                data_point['operation'] = operation
                data_point['full_metric_name'] = metric_name
                
            results.extend(result['data'])
    
    return {
        "success": True,
        "error": None,
        "data": results,
        "autodiscovery_info": {
            "total_trace_metrics": len(available_metrics),
            "discovered_metric_types": dict(sorted(discovered_types.items(), key=lambda x: x[1], reverse=True)),
            "discovered_services": dict(sorted(service_patterns.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_operations": dict(sorted(operation_patterns.items(), key=lambda x: x[1], reverse=True)[:10]),
            "used_metric_types": metric_types,
            "service_filter": service,
            "filtered_metrics_count": len(type_filtered_metrics),
            "queried_metrics_count": len(final_metrics),
            "metrics_with_data": len(results)
        },
        "time_range": time_range,
        "queries_executed": queries_made
    } 