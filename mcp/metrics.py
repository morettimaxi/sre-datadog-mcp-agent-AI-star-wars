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
        
        response = requests.get(url, headers=headers, params=params, timeout=30, verify=get_requests_verify())
        
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
        
        response = requests.get(url, headers=headers, params=params, verify=get_requests_verify())
        
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
        
        response = requests.get(url, headers=headers, verify=get_requests_verify())
        
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

def get_redis_metrics_mcp(service=None, time_range="1 hour", cloud_provider="auto", resource_group=None, **kwargs):
    """
    MCP Function to get Redis metrics - Azure Redis Cache + AWS ElastiCache
    
    Args:
        service (str): Cache cluster/instance name
        time_range (str): Time range for metrics  
        cloud_provider (str): "aws", "azure", or "auto"
        resource_group (str): Azure resource group
    """
    
    print(f"🔍 Getting Redis metrics for: {service or 'all'}")
    
    # Auto-detect cloud provider if needed
    if cloud_provider == "auto":
        cloud_provider = "azure" if resource_group else "aws"
    
    if cloud_provider.lower() == "aws":
        # AWS ElastiCache - optimized queries
        service_filter = f"{{cacheclusterid:{service}}}" if service else "{*}"
        cache_queries = [
            f"avg:aws.elasticache.cpucredit_usage{service_filter}",
            f"avg:aws.elasticache.cpuutilization{service_filter}",
            f"avg:aws.elasticache.database_memory_usage_percentage{service_filter}",
            f"sum:aws.elasticache.cache_hits{service_filter}",
            f"sum:aws.elasticache.cache_misses{service_filter}",
            f"avg:aws.elasticache.curr_connections{service_filter}",
            f"avg:aws.elasticache.freeable_memory{service_filter}",
            f"avg:aws.elasticache.network_bytes_in{service_filter}",
            f"avg:aws.elasticache.network_bytes_out{service_filter}"
        ]
        provider_name = f"AWS ElastiCache ({service or 'all clusters'})"
        
    elif cloud_provider.lower() == "azure":
        # Azure Redis Cache - optimized queries
        if resource_group:
            service_filter = f"{{name:{service},resource_group:{resource_group}}}" if service else f"{{resource_group:{resource_group}}}"
            provider_name = f"Azure Redis Cache ({service or 'all'} in {resource_group})"
        else:
            service_filter = f"{{name:{service}}}" if service else "{*}"
            provider_name = f"Azure Redis Cache ({service or 'all'})"
            
        cache_queries = [
            f"avg:azure.redis_cache.percentprocessortime{service_filter}",
            f"avg:azure.redis_cache.usedmemorypercentage{service_filter}",
            f"avg:azure.redis_cache.serverload{service_filter}",
            f"sum:azure.redis_cache.cachehits{service_filter}",
            f"sum:azure.redis_cache.cachemisses{service_filter}",
            f"avg:azure.redis_cache.connectedclients{service_filter}",
            f"sum:azure.redis_cache.cachereads{service_filter}",
            f"sum:azure.redis_cache.cachewrites{service_filter}"
        ]
    else:
        return {
            "success": False,
            "error": f"Unsupported cloud provider: {cloud_provider}. Use 'aws' or 'azure'",
            "data": []
        }
    
    # Execute queries
    results = []
    successful_queries = []
    failed_queries = []
    
    print(f"🚀 Executing {len(cache_queries)} Redis metric queries...")
    
    for query in cache_queries:
        result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
        if result['success'] and result['data']:
            results.extend(result['data'])
            successful_queries.append(query)
        else:
            failed_queries.append(query)
    
    return {
        "success": True,
        "error": None,
        "data": results,
        "cloud_provider": provider_name,
        "service": service,
        "resource_group": resource_group,
        "time_range": time_range,
        "successful_queries": successful_queries,
        "failed_queries": failed_queries,
        "metrics_with_data": len(results)
    }

def get_sql_metrics_mcp(service=None, time_range="1 hour", cloud_provider="auto", resource_group=None, **kwargs):
    """
    MCP Function to get SQL metrics - Azure SQL Database + AWS RDS
    
    Args:
        service (str): Database instance name
        time_range (str): Time range for metrics
        cloud_provider (str): "aws", "azure", or "auto" 
        resource_group (str): Azure resource group
    """
    
    print(f"🔍 Getting SQL metrics for: {service or 'all'}")
    
    # Auto-detect cloud provider if needed
    if cloud_provider == "auto":
        cloud_provider = "azure" if resource_group else "aws"
    
    if cloud_provider.lower() == "aws":
        # AWS RDS - optimized queries
        service_filter = f"{{dbinstanceidentifier:{service}}}" if service else "{*}"
        sql_queries = [
            f"avg:aws.rds.cpuutilization{service_filter}",
            f"avg:aws.rds.database_connections{service_filter}",
            f"avg:aws.rds.freeable_memory{service_filter}",
            f"avg:aws.rds.read_latency{service_filter}",
            f"avg:aws.rds.write_latency{service_filter}",
            f"sum:aws.rds.read_iops{service_filter}",
            f"sum:aws.rds.write_iops{service_filter}",
            f"avg:aws.rds.free_storage_space{service_filter}"
        ]
        provider_name = f"AWS RDS ({service or 'all databases'})"
        
    elif cloud_provider.lower() == "azure":
        # Azure SQL Database - optimized queries  
        if resource_group:
            service_filter = f"{{name:{service},resource_group:{resource_group}}}" if service else f"{{resource_group:{resource_group}}}"
            provider_name = f"Azure SQL Database ({service or 'all'} in {resource_group})"
        else:
            service_filter = f"{{name:{service}}}" if service else "{*}"
            provider_name = f"Azure SQL Database ({service or 'all'})"
            
        sql_queries = [
            f"avg:azure.sql_database.cpu_percent{service_filter}",
            f"avg:azure.sql_database.dtu_consumption_percent{service_filter}",
            f"avg:azure.sql_database.storage_percent{service_filter}",
            f"sum:azure.sql_database.connection_successful{service_filter}",
            f"sum:azure.sql_database.connection_failed{service_filter}",
            f"avg:azure.sql_database.deadlock{service_filter}",
            f"sum:azure.sql_database.blocked_by_firewall{service_filter}"
        ]
    else:
        return {
            "success": False,
            "error": f"Unsupported cloud provider: {cloud_provider}. Use 'aws' or 'azure'",
            "data": []
        }
    
    # Execute queries
    results = []
    successful_queries = []
    failed_queries = []
    
    print(f"🚀 Executing {len(sql_queries)} SQL metric queries...")
    
    for query in sql_queries:
        result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
        if result['success'] and result['data']:
            results.extend(result['data'])
            successful_queries.append(query)
        else:
            failed_queries.append(query)
    
    return {
        "success": True,
        "error": None,
        "data": results,
        "cloud_provider": provider_name,
        "service": service,
        "resource_group": resource_group,
        "time_range": time_range,
        "successful_queries": successful_queries,
        "failed_queries": failed_queries,
        "metrics_with_data": len(results)
    }

def get_compute_metrics_mcp(service=None, time_range="1 hour", compute_type="auto", resource_group=None, **kwargs):
    """
    MCP Function to get Compute metrics - Kubernetes + AWS EC2
    
    Args:
        service (str): Deployment/instance name
        time_range (str): Time range for metrics
        compute_type (str): "k8s", "ec2", or "auto"
        resource_group (str): For filtering
    """
    
    print(f"🔍 Getting Compute metrics for: {service or 'all'}")
    
    # Auto-detect compute type
    if compute_type == "auto":
        # Simple heuristic: if resource_group or service contains k8s/kube keywords
        service_lower = (service or '').lower()
        if any(keyword in service_lower for keyword in ['k8s', 'kube', 'deployment', 'pod']):
            compute_type = "k8s"
        else:
            compute_type = "ec2"  # Default to EC2
    
    if compute_type.lower() == "k8s":
        # Kubernetes - optimized queries
        if service:
            service_filter = f"{{kube_deployment:{service}}}"
        else:
            service_filter = "{*}"
            
        compute_queries = [
            f"avg:kubernetes.cpu.usage.total{service_filter}",
            f"avg:kubernetes.memory.usage{service_filter}",
            f"avg:kubernetes.memory.working_set{service_filter}",
            f"sum:kubernetes.containers.running{service_filter}",
            f"sum:kubernetes.containers.terminated{service_filter}",
            f"avg:kubernetes.cpu.limits{service_filter}",
            f"avg:kubernetes.memory.limits{service_filter}",
            f"sum:kubernetes.pods.running{service_filter}"
        ]
        provider_name = f"Kubernetes ({service or 'all deployments'})"
        
    elif compute_type.lower() == "ec2":
        # AWS EC2 - optimized queries
        service_filter = f"{{instanceid:{service}}}" if service else "{*}"
        compute_queries = [
            f"avg:aws.ec2.cpuutilization{service_filter}",
            f"avg:aws.ec2.cpucredit_usage{service_filter}",
            f"avg:aws.ec2.cpucredit_balance{service_filter}",
            f"avg:aws.ec2.disk_read_bytes{service_filter}",
            f"avg:aws.ec2.disk_write_bytes{service_filter}",
            f"avg:aws.ec2.network_in{service_filter}",
            f"avg:aws.ec2.network_out{service_filter}",
            f"sum:aws.ec2.status_check_failed{service_filter}"
        ]
        provider_name = f"AWS EC2 ({service or 'all instances'})"
        
    else:
        return {
            "success": False,
            "error": f"Unsupported compute type: {compute_type}. Use 'k8s' or 'ec2'",
            "data": []
        }
    
    # Execute queries
    results = []
    successful_queries = []
    failed_queries = []
    
    print(f"🚀 Executing {len(compute_queries)} Compute metric queries...")
    
    for query in compute_queries:
        result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
        if result['success'] and result['data']:
            results.extend(result['data'])
            successful_queries.append(query)
        else:
            failed_queries.append(query)
    
    return {
        "success": True,
        "error": None,
        "data": results,
        "compute_type": compute_type,
        "cloud_provider": provider_name,
        "service": service,
        "time_range": time_range,
        "successful_queries": successful_queries,
        "failed_queries": failed_queries,
        "metrics_with_data": len(results)
    }

def get_service_health_mcp(service_name, service_type="auto", time_range="1 hour", resource_group=None, cloud_provider=None, **kwargs):
    """
    MCP Function to get a comprehensive health report of a cloud resource or service
    
    Args:
        service_name (str): Name of the resource/service/cluster to analyze
        service_type (str): Type of resource ("redis", "k8s", "app", "system", "auto")
        time_range (str): Time range for analysis
        resource_group (str): Azure resource group or AWS tag filter
        cloud_provider (str): "aws", "azure", or "auto" for auto-detection
    """
    
    # Auto-detect service type if not specified
    if service_type == "auto":
        service_name_lower = service_name.lower()
        if any(keyword in service_name_lower for keyword in ['redis', 'elasticache', 'cache']):
            service_type = "redis"
        elif any(keyword in service_name_lower for keyword in ['k8s', 'kubernetes', 'pod', 'deployment']):
            service_type = "k8s"
        elif any(keyword in service_name_lower for keyword in ['api', 'web', 'app', 'service']):
            service_type = "app"
        else:
            service_type = "system"
    
    print(f"🔍 Analyzing {service_type} service: {service_name}")
    
    # Get metrics based on service type and cloud provider
    if service_type == "redis":
        if cloud_provider == "aws" or (cloud_provider == "auto" and not resource_group):
            # AWS ElastiCache - use cacheclusterid or cache node filters
            service_filter = f"{{cacheclusterid:{service_name}}}" if service_name else "{*}"
            if resource_group:  # AWS uses tags for grouping
                service_filter = f"{{cacheclusterid:{service_name},tag_group:{resource_group}}}"
            
            aws_queries = [
                f"avg:aws.elasticache.cpucredit_usage{service_filter}",
                f"avg:aws.elasticache.cpu_utilization{service_filter}",
                f"avg:aws.elasticache.database_memory_usage_percentage{service_filter}",
                f"sum:aws.elasticache.cache_hits{service_filter}",
                f"sum:aws.elasticache.cache_misses{service_filter}",
                f"avg:aws.elasticache.curr_connections{service_filter}"
            ]
            provider = f"AWS ElastiCache ({service_name})"
            
        elif cloud_provider == "azure" or (cloud_provider == "auto" and resource_group):
            # Azure Redis Cache - use name and resource_group filters
            if resource_group:
                service_filter = f"{{name:{service_name},resource_group:{resource_group}}}"
                provider = f"Azure Redis Cache ({service_name} in {resource_group})"
            else:
                service_filter = f"{{name:{service_name}}}" if service_name else "{*}"
                provider = f"Azure Redis Cache ({service_name})"
            
            azure_queries = [
                f"avg:azure.redis_cache.percentprocessortime{service_filter}",
                f"avg:azure.redis_cache.usedmemorypercentage{service_filter}",
                f"avg:azure.redis_cache.serverload{service_filter}",
                f"sum:azure.redis_cache.cachehits{service_filter}",
                f"sum:azure.redis_cache.cachemisses{service_filter}",
                f"avg:azure.redis_cache.connectedclients{service_filter}"
            ]
        
        else:
            # Try both if auto-detection
            aws_result = get_redis_cache_metrics_mcp(
                service=service_name, 
                time_range=time_range, 
                cloud_provider="aws", 
                **kwargs
            )
            azure_result = get_redis_cache_metrics_mcp(
                service=service_name, 
                time_range=time_range, 
                cloud_provider="azure", 
                **kwargs
            )
            
            # Use whichever has data
            if aws_result['metrics_with_data'] > 0:
                metrics_result = aws_result
                provider = "AWS ElastiCache"
            elif azure_result['metrics_with_data'] > 0:
                metrics_result = azure_result
                provider = "Azure Redis Cache"
            else:
                return {
                    "success": False,
                    "error": f"No Redis metrics found for resource '{service_name}' in AWS or Azure",
                    "data": {}
                }
        
        # Execute queries if we have specific cloud provider
        if 'aws_queries' in locals():
            results = []
            for query in aws_queries:
                result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
                if result['success'] and result['data']:
                    results.extend(result['data'])
            metrics_result = {"success": True, "data": results}
            
        elif 'azure_queries' in locals():
            results = []
            for query in azure_queries:
                result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
                if result['success'] and result['data']:
                    results.extend(result['data'])
            metrics_result = {"success": True, "data": results}
            
    elif service_type == "k8s":
        metrics_result = get_kubernetes_metrics_mcp(
            service=service_name, 
            time_range=time_range, 
            **kwargs
        )
        provider = "Kubernetes"
        
    elif service_type == "app":
        metrics_result = get_application_metrics_mcp(
            service=service_name, 
            time_range=time_range, 
            **kwargs
        )
        provider = "Application/APM"
        
    else:  # system
        metrics_result = get_system_metrics_mcp(
            time_range=time_range, 
            host=service_name, 
            **kwargs
        )
        provider = "System"
    
    if not metrics_result['success'] or not metrics_result['data']:
        return {
            "success": False,
            "error": f"No metrics data found for {service_type} service '{service_name}'",
            "data": {}
        }
    
    # Analyze the health
    metrics_data = metrics_result['data']
    health_analysis = {
        "resource_name": service_name,
        "resource_type": service_type,
        "cloud_provider": provider,
        "resource_group": resource_group,
        "status": "unknown",
        "summary": {},
        "alerts": [],
        "recommendations": [],
        "key_metrics": [],
        "time_range": time_range
    }
    
    # Analyze key metrics
    cpu_metrics = []
    memory_metrics = []
    performance_metrics = []
    error_metrics = []
    
    for metric in metrics_data:
        metric_name = metric.get('metric', '').lower()
        latest_value = metric.get('latest_value')
        avg_value = metric.get('avg_value')
        
        if latest_value is None:
            continue
            
        # Categorize metrics
        if any(term in metric_name for term in ['cpu', 'processor']):
            cpu_metrics.append({
                "name": metric['metric'],
                "value": latest_value,
                "avg": avg_value,
                "scope": metric.get('scope', {})
            })
        elif any(term in metric_name for term in ['memory', 'mem']):
            memory_metrics.append({
                "name": metric['metric'],
                "value": latest_value,
                "avg": avg_value,
                "scope": metric.get('scope', {})
            })
        elif any(term in metric_name for term in ['response_time', 'latency', 'duration']):
            performance_metrics.append({
                "name": metric['metric'],
                "value": latest_value,
                "avg": avg_value,
                "scope": metric.get('scope', {})
            })
        elif any(term in metric_name for term in ['error', 'miss']):
            error_metrics.append({
                "name": metric['metric'],
                "value": latest_value,
                "avg": avg_value,
                "scope": metric.get('scope', {})
            })
    
    # Generate health status and alerts
    status_score = 100
    
    # CPU Analysis
    if cpu_metrics:
        avg_cpu = sum(m['value'] for m in cpu_metrics) / len(cpu_metrics)
        health_analysis["summary"]["cpu_usage"] = f"{avg_cpu:.1f}%"
        
        if avg_cpu > 90:
            health_analysis["alerts"].append("🔴 CRITICAL: CPU usage very high (>90%)")
            health_analysis["recommendations"].append("Scale up resources or optimize CPU usage")
            status_score -= 30
        elif avg_cpu > 75:
            health_analysis["alerts"].append("🟡 WARNING: CPU usage high (>75%)")
            health_analysis["recommendations"].append("Monitor CPU usage closely")
            status_score -= 15
        else:
            health_analysis["alerts"].append("✅ CPU usage is healthy")
    
    # Memory Analysis
    if memory_metrics:
        avg_memory = sum(m['value'] for m in memory_metrics) / len(memory_metrics)
        health_analysis["summary"]["memory_usage"] = f"{avg_memory:.1f}%"
        
        if avg_memory > 95:
            health_analysis["alerts"].append("🔴 CRITICAL: Memory usage very high (>95%)")
            health_analysis["recommendations"].append("Increase memory or check for memory leaks")
            status_score -= 30
        elif avg_memory > 80:
            health_analysis["alerts"].append("🟡 WARNING: Memory usage high (>80%)")
            health_analysis["recommendations"].append("Monitor memory usage")
            status_score -= 15
        else:
            health_analysis["alerts"].append("✅ Memory usage is healthy")
    
    # Performance Analysis (for Redis/App services)
    if performance_metrics and service_type in ['redis', 'app']:
        avg_response = sum(m['value'] for m in performance_metrics) / len(performance_metrics)
        health_analysis["summary"]["avg_response_time"] = f"{avg_response:.2f}ms"
        
        if avg_response > 1000:  # >1 second
            health_analysis["alerts"].append("🔴 CRITICAL: High response time (>1s)")
            health_analysis["recommendations"].append("Optimize queries or increase cache size")
            status_score -= 25
        elif avg_response > 500:  # >500ms
            health_analysis["alerts"].append("🟡 WARNING: Elevated response time (>500ms)")
            status_score -= 10
        else:
            health_analysis["alerts"].append("✅ Response time is good")
    
    # Error Analysis
    if error_metrics:
        total_errors = sum(m['value'] for m in error_metrics)
        health_analysis["summary"]["errors"] = f"{total_errors:.0f}"
        
        if total_errors > 100:
            health_analysis["alerts"].append("🔴 CRITICAL: High error count")
            health_analysis["recommendations"].append("Investigate error sources immediately")
            status_score -= 20
        elif total_errors > 10:
            health_analysis["alerts"].append("🟡 WARNING: Some errors detected")
            status_score -= 10
        else:
            health_analysis["alerts"].append("✅ Error rate is low")
    
    # Set overall status
    if status_score >= 80:
        health_analysis["status"] = "🟢 HEALTHY"
    elif status_score >= 60:
        health_analysis["status"] = "🟡 WARNING"
    else:
        health_analysis["status"] = "🔴 CRITICAL"
    
    # Add key metrics for detailed view
    health_analysis["key_metrics"] = metrics_data[:10]  # First 10 metrics
    
    # Add summary message
    metric_count = len(metrics_data)
    health_analysis["summary"]["total_metrics"] = metric_count
    health_analysis["summary"]["status_score"] = status_score
    
    return {
        "success": True,
        "error": None,
        "data": health_analysis
    }

def get_cloud_resource_health_mcp(resource_name, resource_type, cloud_provider, resource_group=None, time_range="1 hour", **kwargs):
    """
    MCP Function specifically for cloud resources with proper naming conventions
    
    Args:
        resource_name (str): Exact name of the cloud resource
        resource_type (str): Type of resource ("redis", "vm", "sql", "storage", "lb")
        cloud_provider (str): "aws" or "azure"
        resource_group (str): Azure resource group or AWS tag/region filter
        time_range (str): Time range for analysis
    """
    
    print(f"🔍 Analyzing {cloud_provider.upper()} {resource_type} resource: {resource_name}")
    if resource_group:
        print(f"📁 Resource group/filter: {resource_group}")
    
    # Build cloud-specific filters
    if cloud_provider.lower() == "azure":
        if resource_group:
            base_filter = f"{{name:{resource_name},resource_group:{resource_group}}}"
        else:
            base_filter = f"{{name:{resource_name}}}"
        provider_display = f"Azure {resource_type.upper()}"
        
        # Azure resource type mappings
        if resource_type == "redis":
            metric_queries = [
                f"avg:azure.redis_cache.percentprocessortime{base_filter}",
                f"avg:azure.redis_cache.usedmemorypercentage{base_filter}",
                f"avg:azure.redis_cache.serverload{base_filter}",
                f"sum:azure.redis_cache.cachehits{base_filter}",
                f"sum:azure.redis_cache.cachemisses{base_filter}",
                f"avg:azure.redis_cache.connectedclients{base_filter}",
                f"sum:azure.redis_cache.cachereads{base_filter}",
                f"sum:azure.redis_cache.cachewrites{base_filter}"
            ]
        elif resource_type == "vm":
            metric_queries = [
                f"avg:azure.vm.percentage_cpu{base_filter}",
                f"avg:azure.vm.available_memory_bytes{base_filter}",
                f"avg:azure.vm.disk_read_bytes{base_filter}",
                f"avg:azure.vm.disk_write_bytes{base_filter}",
                f"avg:azure.vm.network_in{base_filter}",
                f"avg:azure.vm.network_out{base_filter}"
            ]
        elif resource_type == "sql":
            metric_queries = [
                f"avg:azure.sql_database.cpu_percent{base_filter}",
                f"avg:azure.sql_database.dtu_consumption_percent{base_filter}",
                f"avg:azure.sql_database.storage_percent{base_filter}",
                f"sum:azure.sql_database.connection_failed{base_filter}",
                f"sum:azure.sql_database.connection_successful{base_filter}"
            ]
        else:
            return {
                "success": False,
                "error": f"Azure resource type '{resource_type}' not supported yet",
                "data": {}
            }
    
    elif cloud_provider.lower() == "aws":
        if resource_group:  # AWS uses tags
            base_filter = f"{{tag_group:{resource_group}}}"
        else:
            base_filter = "{*}"
        provider_display = f"AWS {resource_type.upper()}"
        
        # AWS resource type mappings
        if resource_type == "redis":
            cache_filter = f"{{cacheclusterid:{resource_name}}}" if not resource_group else f"{{cacheclusterid:{resource_name},tag_group:{resource_group}}}"
            metric_queries = [
                f"avg:aws.elasticache.cpucredit_usage{cache_filter}",
                f"avg:aws.elasticache.cpu_utilization{cache_filter}",
                f"avg:aws.elasticache.database_memory_usage_percentage{cache_filter}",
                f"sum:aws.elasticache.cache_hits{cache_filter}",
                f"sum:aws.elasticache.cache_misses{cache_filter}",
                f"avg:aws.elasticache.curr_connections{cache_filter}",
                f"avg:aws.elasticache.network_bytes_in{cache_filter}",
                f"avg:aws.elasticache.network_bytes_out{cache_filter}"
            ]
        elif resource_type == "ec2":
            instance_filter = f"{{instanceid:{resource_name}}}" if not resource_group else f"{{instanceid:{resource_name},tag_group:{resource_group}}}"
            metric_queries = [
                f"avg:aws.ec2.cpu_utilization{instance_filter}",
                f"avg:aws.ec2.disk_read_bytes{instance_filter}",
                f"avg:aws.ec2.disk_write_bytes{instance_filter}",
                f"avg:aws.ec2.network_in{instance_filter}",
                f"avg:aws.ec2.network_out{instance_filter}"
            ]
        elif resource_type == "rds":
            db_filter = f"{{dbinstanceidentifier:{resource_name}}}" if not resource_group else f"{{dbinstanceidentifier:{resource_name},tag_group:{resource_group}}}"
            metric_queries = [
                f"avg:aws.rds.cpu_utilization{db_filter}",
                f"avg:aws.rds.database_connections{db_filter}",
                f"avg:aws.rds.freeable_memory{db_filter}",
                f"avg:aws.rds.read_latency{db_filter}",
                f"avg:aws.rds.write_latency{db_filter}"
            ]
        else:
            return {
                "success": False,
                "error": f"AWS resource type '{resource_type}' not supported yet",
                "data": {}
            }
    
    else:
        return {
            "success": False,
            "error": f"Cloud provider '{cloud_provider}' not supported. Use 'aws' or 'azure'",
            "data": {}
        }
    
    # Execute queries
    results = []
    successful_queries = []
    failed_queries = []
    
    for query in metric_queries:
        result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
        if result['success'] and result['data']:
            results.extend(result['data'])
            successful_queries.append(query)
        else:
            failed_queries.append(query)
    
    if not results:
        return {
            "success": False,
            "error": f"No metrics found for {cloud_provider} {resource_type} '{resource_name}'",
            "data": {},
            "failed_queries": failed_queries
        }
    
    # Analyze health (reuse the analysis logic)
    health_analysis = {
        "resource_name": resource_name,
        "resource_type": resource_type,
        "cloud_provider": provider_display,
        "resource_group": resource_group,
        "status": "unknown",
        "summary": {},
        "alerts": [],
        "recommendations": [],
        "raw_metrics": results,
        "time_range": time_range,
        "successful_queries": len(successful_queries),
        "failed_queries": len(failed_queries)
    }
    
    # Quick health scoring
    total_metrics = len(results)
    health_score = 100
    
    for metric in results:
        if metric.get('latest_value') is not None:
            value = metric['latest_value']
            metric_name = metric.get('metric', '').lower()
            
            # CPU analysis
            if 'cpu' in metric_name:
                if value > 90:
                    health_analysis["alerts"].append(f"🔴 High CPU: {value:.1f}%")
                    health_score -= 25
                elif value > 75:
                    health_analysis["alerts"].append(f"🟡 Elevated CPU: {value:.1f}%")
                    health_score -= 10
                else:
                    health_analysis["alerts"].append(f"✅ CPU OK: {value:.1f}%")
            
            # Memory analysis
            elif 'memory' in metric_name or 'mem' in metric_name:
                if value > 90:
                    health_analysis["alerts"].append(f"🔴 High Memory: {value:.1f}%")
                    health_score -= 25
                elif value > 80:
                    health_analysis["alerts"].append(f"🟡 Elevated Memory: {value:.1f}%")
                    health_score -= 10
                else:
                    health_analysis["alerts"].append(f"✅ Memory OK: {value:.1f}%")
    
    # Set overall status
    if health_score >= 80:
        health_analysis["status"] = "🟢 HEALTHY"
    elif health_score >= 60:
        health_analysis["status"] = "🟡 WARNING"
    else:
        health_analysis["status"] = "🔴 CRITICAL"
    
    health_analysis["summary"]["health_score"] = health_score
    health_analysis["summary"]["total_metrics"] = total_metrics
    
    return {
        "success": True,
        "error": None,
        "data": health_analysis
    }

def get_dynamic_resource_metrics_mcp(resource_pattern, cloud_provider=None, time_range="1 hour", max_metrics=20, **kwargs):
    """
    MCP Function to get metrics for ANY resource type using dynamic discovery - NO HARDCODING!
    
    Args:
        resource_pattern (str): Pattern to search for (e.g., "redis", "elasticache", "vm", "sql")
        cloud_provider (str): "aws", "azure", "gcp", or None for all
        time_range (str): Time range for metrics
        max_metrics (int): Maximum number of metrics to query
    """
    
    print(f"🔍 Dynamic discovery for pattern: '{resource_pattern}'")
    
    # Step 1: Auto-discover all metrics matching the pattern
    search_result = search_metrics_mcp(metric_name=resource_pattern)
    if not search_result['success']:
        return {
            "success": False,
            "error": f"Failed to search for '{resource_pattern}' metrics: {search_result['error']}",
            "data": []
        }
    
    all_metrics = [m['name'] for m in search_result['data']]
    print(f"📊 Found {len(all_metrics)} metrics matching '{resource_pattern}'")
    
    # Step 2: Filter by cloud provider if specified
    if cloud_provider:
        cloud_filtered = [m for m in all_metrics if cloud_provider.lower() in m.lower()]
        print(f"☁️ Filtered to {len(cloud_filtered)} {cloud_provider} metrics")
        all_metrics = cloud_filtered
    
    if not all_metrics:
        return {
            "success": False,
            "error": f"No metrics found for pattern '{resource_pattern}'" + (f" in {cloud_provider}" if cloud_provider else ""),
            "data": []
        }
    
    # Step 3: Intelligent metric prioritization (NO HARDCODING!)
    scoring = {}
    
    # Priority words and their scores
    priority_terms = {
        'cpu': 10, 'processor': 10, 'utilization': 8,
        'memory': 9, 'mem': 9, 'ram': 9,
        'hits': 8, 'misses': 8, 'cache': 7,
        'connections': 7, 'clients': 7, 'conn': 7,
        'network': 6, 'bytes': 6, 'throughput': 6,
        'errors': 9, 'failures': 9, 'exceptions': 9,
        'latency': 8, 'response': 8, 'duration': 8,
        'disk': 7, 'storage': 7, 'io': 7,
        'load': 8, 'usage': 7, 'percent': 7
    }
    
    for metric in all_metrics:
        score = 0
        metric_lower = metric.lower()
        
        # Score based on priority terms
        for term, points in priority_terms.items():
            if term in metric_lower:
                score += points
        
        # Bonus for common aggregatable metrics
        if any(word in metric_lower for word in ['total', 'count', 'rate']):
            score += 3
        
        # Penalty for very specific/niche metrics
        if len(metric.split('.')) > 4:  # Very nested metrics
            score -= 2
        
        scoring[metric] = score
    
    # Step 4: Select top metrics
    sorted_metrics = sorted(scoring.items(), key=lambda x: x[1], reverse=True)
    selected_metrics = [metric for metric, score in sorted_metrics[:max_metrics] if score > 0]
    
    print(f"🎯 Selected top {len(selected_metrics)} metrics by intelligence score")
    
    # Step 5: Smart aggregation detection
    queries = []
    for metric in selected_metrics:
        metric_lower = metric.lower()
        
        # Determine aggregation intelligently
        if any(term in metric_lower for term in ['count', 'total', 'hits', 'misses', 'errors', 'requests']):
            aggregation = "sum"
        elif any(term in metric_lower for term in ['rate', 'percent', 'ratio']):
            aggregation = "avg"
        elif any(term in metric_lower for term in ['latency', 'duration', 'time']):
            aggregation = "avg"
        elif any(term in metric_lower for term in ['max', 'peak']):
            aggregation = "max"
        elif any(term in metric_lower for term in ['min', 'low']):
            aggregation = "min"
        else:
            aggregation = "avg"  # Default safe choice
        
        queries.append(f"{aggregation}:{metric}{{*}}")
    
    # Step 6: Execute queries
    results = []
    successful_queries = []
    failed_queries = []
    
    print(f"🚀 Executing {len(queries)} intelligent queries...")
    
    for query in queries:
        result = query_metrics_mcp(query=query, time_range=time_range, **kwargs)
        if result['success'] and result['data']:
            results.extend(result['data'])
            successful_queries.append(query)
        else:
            failed_queries.append(query)
    
    # Step 7: Intelligent analysis
    analysis = {
        "resource_pattern": resource_pattern,
        "cloud_provider": cloud_provider,
        "metrics_found": len(all_metrics),
        "metrics_selected": len(selected_metrics),
        "metrics_with_data": len(results),
        "top_metrics": selected_metrics[:10],
        "queries_successful": len(successful_queries),
        "queries_failed": len(failed_queries),
        "time_range": time_range
    }
    
    return {
        "success": True,
        "error": None,
        "data": results,
        "analysis": analysis,
        "discovery_method": "Dynamic Intelligence (Zero Hardcoding)",
        "successful_queries": successful_queries,
        "failed_queries": failed_queries
    } 