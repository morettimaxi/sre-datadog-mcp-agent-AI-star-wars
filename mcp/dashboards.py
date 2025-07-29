import requests
import os
import time
import json
import re
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

def _detect_unit(query_text):
    """
    Detect the appropriate unit for a metric query
    """
    query_lower = query_text.lower()
    if any(word in query_lower for word in ['latency', 'duration', 'time', 'trace.']):
        return 'ms'
    elif any(word in query_lower for word in ['error', 'count', 'reqs', 'requests']):
        return 'count'
    elif any(word in query_lower for word in ['rate', 'percent', '%']):
        return 'rate'
    elif any(word in query_lower for word in ['memory', 'cpu', 'disk']):
        return 'percent'
    else:
        return 'value'

def parse_time_range(time_range_str="1 week"):
    """
    Parse time range string and return seconds ago from now.
    
    Examples:
    - "1 hour" -> 3600 seconds
    - "4 hours" -> 14400 seconds  
    - "1 day" -> 86400 seconds
    - "3 days" -> 259200 seconds
    - "1 week" -> 604800 seconds
    - "1 month" -> 2592000 seconds (30 days)
    """
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
        'months': 2592000
    }
    
    # Try to match pattern like "1 hour", "3 days", "2 weeks"
    match = re.match(r'(\d+)\s+(hour|hours|day|days|week|weeks|month|months)', time_range_str)
    
    if match:
        number = int(match.group(1))
        unit = match.group(2)
        return number * multipliers[unit]
    
    # Default fallback patterns
    if 'hour' in time_range_str:
        return 3600
    elif 'day' in time_range_str:
        return 86400
    elif 'week' in time_range_str:
        return 604800
    elif 'month' in time_range_str:
        return 2592000
    else:
        # Default to 1 week
        return 604800

def list_dashboards_mcp(name=None, tags=None, **kwargs):
    """
    MCP Function to list Datadog dashboards
    Supports filtering by name and tags
    """
    
    # VERIFY KEYS
    if not all([DD_API_KEY, DD_APP_KEY]):
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": []
        }
    
    # DATADOG API CALL
    try:
        url = f"https://{DD_SITE}/api/v1/dashboard"
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json'
        }
        
        filters_applied = []
        if name:
            filters_applied.append(f"name='{name}'")
        if tags:
            filters_applied.append(f"tags={tags}")
        filter_info = ", ".join(filters_applied) if filters_applied else "no filters"
        
        print(f"🔄 MCP: Calling Datadog Dashboards API with {filter_info}")
        print(f"🌐 API URL: {url}")
        response = requests.get(url, headers=headers, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            dashboards = data.get('dashboards', [])
            print(f"📥 API Response: {response.status_code} - {len(dashboards)} dashboards received")
            print(f"🔍 Raw response keys: {list(data.keys())}")
            
            filtered_dashboards = []
            skipped_by_name = 0
            skipped_by_tags = 0
            
            for dashboard in dashboards:
                # Apply name filter if provided
                if name:
                    dashboard_title = dashboard.get('title', '').lower()
                    if name.lower() not in dashboard_title:
                        skipped_by_name += 1
                        continue
                
                # Apply tags filter if provided
                if tags:
                    dashboard_description = dashboard.get('description', '')
                    dashboard_tags = [tag.strip() for tag in dashboard_description.split(',') if tag.strip()]
                    if not all(tag in dashboard_tags for tag in tags):
                        skipped_by_tags += 1
                        continue
                
                dashboard_info = {
                    "id": dashboard.get('id'),
                    "title": dashboard.get('title'),
                    "description": dashboard.get('description'),
                    "layout_type": dashboard.get('layout_type'),
                    "created_at": dashboard.get('created_at'),
                    "modified_at": dashboard.get('modified_at'),
                    "author_handle": dashboard.get('author_handle'),
                    "url": f"https://app.datadoghq.com/dashboard/{dashboard.get('id')}"
                }
                filtered_dashboards.append(dashboard_info)
            
            # Debug summary
            total_received = len(dashboards)
            total_returned = len(filtered_dashboards)
            print(f"🎯 Filtering Summary:")
            print(f"   📊 Total received: {total_received}")
            print(f"   🚫 Skipped by name filter: {skipped_by_name}")
            print(f"   🚫 Skipped by tags filter: {skipped_by_tags}")
            print(f"   ✅ Final results: {total_returned}")
            
            return {
                "success": True,
                "error": None,
                "data": filtered_dashboards,
                "total_dashboards": len(dashboards),
                "filtered_dashboards": len(filtered_dashboards)
            }
            
        else:
            return {
                "success": False,
                "error": f"Datadog API error: {response.status_code} - {response.text}",
                "data": []
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "data": []
        }

def get_dashboard_mcp(dashboard_id, **kwargs):
    """
    MCP Function to get a specific Datadog dashboard by ID
    """
    
    # VERIFY KEYS
    if not all([DD_API_KEY, DD_APP_KEY]):
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": None
        }
    
    if not dashboard_id:
        return {
            "success": False,
            "error": "dashboard_id is required",
            "data": None
        }
    
    # DATADOG API CALL
    try:
        url = f"https://{DD_SITE}/api/v1/dashboard/{dashboard_id}"
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json'
        }
        
        print(f"🔄 MCP: Getting dashboard {dashboard_id} from Datadog API...")
        response = requests.get(url, headers=headers, verify=False)
        
        if response.status_code == 200:
            dashboard = response.json()
            
            dashboard_info = {
                "id": dashboard.get('id'),
                "title": dashboard.get('title'),
                "description": dashboard.get('description'),
                "layout_type": dashboard.get('layout_type'),
                "created_at": dashboard.get('created_at'),
                "modified_at": dashboard.get('modified_at'),
                "author_handle": dashboard.get('author_handle'),
                "widgets": dashboard.get('widgets', []),
                "template_variables": dashboard.get('template_variables', []),
                "url": f"https://app.datadoghq.com/dashboard/{dashboard.get('id')}"
            }
            
            return {
                "success": True,
                "error": None,
                "data": dashboard_info
            }
            
        elif response.status_code == 404:
            return {
                "success": False,
                "error": f"Dashboard {dashboard_id} not found",
                "data": None
            }
        else:
            return {
                "success": False,
                "error": f"Datadog API error: {response.status_code} - {response.text}",
                "data": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "data": None
        }

def get_widget_data_mcp(dashboard_id, time_range="1 week", **kwargs):
    """
    MCP Function to get actual data from dashboard widgets with REAL metric values
    
    Args:
        dashboard_id (str): Dashboard ID to fetch data from
        time_range (str): Time range for data (e.g., "1 hour", "1 day", "1 week", "1 month")
    """
    
    # VERIFY KEYS
    if not all([DD_API_KEY, DD_APP_KEY]):
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": None
        }
    
    try:
        print(f"🔄 MCP: Getting REAL widget data for dashboard {dashboard_id} (time_range: {time_range})...")
        
        # Parse time range
        time_range_seconds = parse_time_range(time_range)
        print(f"📅 Time range: {time_range} = {time_range_seconds} seconds")
        
        # Get dashboard configuration first
        dashboard_result = get_dashboard_mcp(dashboard_id)
        if not dashboard_result['success']:
            return dashboard_result
        
        dashboard = dashboard_result['data']
        widgets = dashboard.get('widgets', [])
        widget_data_results = []
        
        # Headers for metric queries
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json'
        }
        
        # Calculate time range using parsed time_range  
        now = int(time.time())
        time_ago = now - time_range_seconds
        
        print(f"🕒 Query time range: {datetime.fromtimestamp(time_ago)} to {datetime.fromtimestamp(now)}")
        
        # Process each widget using the WORKING logic from test_dashboard_direct.py
        for i, widget in enumerate(widgets):
            widget_def = widget.get('definition', {})
            widget_type = widget_def.get('type', 'unknown')
            widget_title = widget_def.get('title', f'Widget {i+1}')
            
            print(f"📊 Processing widget {i+1}: {widget_title} (type: {widget_type})")
            
            widget_current_data = {
                'widget_index': i,
                'widget_title': widget_title,
                'widget_type': widget_type,
                'data_points': [],
                'queries_executed': [],
                'current_values': []
            }
            
            # WORKING LOGIC: Handle group widgets (most dashboard widgets are groups)
            if widget_type == 'group':
                sub_widgets = widget_def.get('widgets', [])
                print(f"   🔍 Group widget has {len(sub_widgets)} sub-widgets")
                
                for j, sub_widget in enumerate(sub_widgets):
                    sub_def = sub_widget.get('definition', {})
                    sub_title = sub_def.get('title', f'Sub-widget {j+1}')
                    sub_requests = sub_def.get('requests', [])
                    
                    print(f"      📊 Sub-widget: {sub_title} - {len(sub_requests)} requests")
                    
                    for req in sub_requests:
                        queries_array = req.get('queries', [])
                        for query_obj in queries_array:
                            query_text = query_obj.get('query', '')
                            if query_text:  # Execute ALL queries, not just trace
                                print(f"🚀 EXECUTING: {query_text}")
                                
                                # Use correct metrics API endpoint
                                query_url = f"https://{DD_SITE}/api/v1/query"
                                query_params = {
                                    'query': query_text,
                                    'from': time_ago,
                                    'to': now
                                }
                                
                                try:
                                    response = requests.get(query_url, headers=headers, params=query_params, verify=False)
                                    print(f"📈 Response: {response.status_code}")
                                    
                                    if response.status_code == 200:
                                        query_data = response.json()
                                        series = query_data.get('series', [])
                                        print(f"📊 Found {len(series)} series")
                                        
                                        if series:
                                            for serie in series:
                                                pointlist = serie.get('pointlist', [])
                                                scope = serie.get('scope', 'unknown')
                                                print(f"   📈 Series: {scope} - {len(pointlist)} points")
                                                
                                                if pointlist:
                                                    # Get latest value - THIS IS THE WORKING LOGIC
                                                    latest_point = pointlist[-1]
                                                    latest_value = latest_point[1] if len(latest_point) > 1 else None
                                                    latest_time = latest_point[0] if len(latest_point) > 0 else None
                                                    
                                                    if latest_value is not None:
                                                        widget_current_data['current_values'].append({
                                                            'query': query_text,
                                                            'metric': serie.get('metric', ''),
                                                            'scope': scope,
                                                            'latest_value': latest_value,
                                                            'timestamp': latest_time,
                                                            'unit': _detect_unit(query_text),
                                                            'data_points_count': len(pointlist)
                                                        })
                                                        
                                                        print(f"✅ SUCCESS: {latest_value:.2f} at {datetime.fromtimestamp(latest_time/1000)}")
                                                    else:
                                                        print(f"⚠️ No valid latest value")
                                                else:
                                                    print(f"⚠️ No data points for series")
                                        else:
                                            print(f"⚠️ No series data")
                                        
                                        widget_current_data['queries_executed'].append({
                                            'query': query_text,
                                            'status': 'success',
                                            'series_count': len(series),
                                            'has_data': len(series) > 0 and any(len(s.get('pointlist', [])) > 0 for s in series)
                                        })
                                    else:
                                        error_msg = f"API Error {response.status_code}: {response.text}"
                                        print(f"❌ {error_msg}")
                                        widget_current_data['queries_executed'].append({
                                            'query': query_text,
                                            'status': 'error',
                                            'error': error_msg
                                        })
                                        
                                except Exception as e:
                                    error_msg = f"Exception: {str(e)}"
                                    print(f"❌ {error_msg}")
                                    widget_current_data['queries_executed'].append({
                                        'query': query_text,
                                        'status': 'error',
                                        'error': error_msg
                                    })
            else:
                # Handle non-group widgets (less common but still support them)
                requests_data = widget_def.get('requests', [])
                print(f"   📊 Non-group widget has {len(requests_data)} requests")
                
                for req in requests_data:
                    queries_array = req.get('queries', [])
                    for query_obj in queries_array:
                        query_text = query_obj.get('query', '')
                        if query_text:
                            print(f"🚀 EXECUTING: {query_text}")
                            
                            query_url = f"https://{DD_SITE}/api/v1/query"
                            query_params = {
                                'query': query_text,
                                'from': time_ago,
                                'to': now
                            }
                            
                            try:
                                response = requests.get(query_url, headers=headers, params=query_params, verify=False)
                                if response.status_code == 200:
                                    query_data = response.json()
                                    series = query_data.get('series', [])
                                    
                                    if series:
                                        for serie in series:
                                            pointlist = serie.get('pointlist', [])
                                            if pointlist:
                                                latest_point = pointlist[-1]
                                                latest_value = latest_point[1] if len(latest_point) > 1 else None
                                                latest_time = latest_point[0] if len(latest_point) > 0 else None
                                                
                                                if latest_value is not None:
                                                    widget_current_data['current_values'].append({
                                                        'query': query_text,
                                                        'metric': serie.get('metric', ''),
                                                        'latest_value': latest_value,
                                                        'timestamp': latest_time,
                                                        'unit': _detect_unit(query_text),
                                                        'data_points_count': len(pointlist)
                                                    })
                                                    
                                                    print(f"✅ SUCCESS: {latest_value}")
                                
                                widget_current_data['queries_executed'].append({
                                    'query': query_text,
                                    'status': 'success' if response.status_code == 200 else 'error'
                                })
                                
                            except Exception as e:
                                print(f"❌ Error: {str(e)}")
                                widget_current_data['queries_executed'].append({
                                    'query': query_text,
                                    'status': 'error',
                                    'error': str(e)
                                })
            
            widget_data_results.append(widget_current_data)
        
        return {
            "success": True,
            "error": None,
            "data": {
                'dashboard_info': dashboard,
                'widgets_current_data': widget_data_results
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception getting widget data: {str(e)}",
            "data": None
        }

def analyze_dashboard_mcp(dashboard_id, time_range="1 week", **kwargs):
    """
    MCP Function to analyze a Datadog dashboard and extract detailed information
    
    Args:
        dashboard_id (str): Dashboard ID to analyze
        time_range (str): Time range for analysis (e.g., "1 hour", "1 day", "1 week", "1 month")
    """
    
    # Get the dashboard first
    dashboard_result = get_dashboard_mcp(dashboard_id)
    
    if not dashboard_result['success']:
        return dashboard_result
    
    dashboard = dashboard_result['data']
    widgets = dashboard.get('widgets', [])
    
    # Analyze widgets
    widget_analysis = {
        'total_widgets': len(widgets),
        'widget_types': {},
        'metrics_tracked': [],
        'queries': [],
        'widget_details': []
    }
    
    for i, widget in enumerate(widgets):
        widget_def = widget.get('definition', {})
        widget_type = widget_def.get('type', 'unknown')
        
        # Count widget types
        widget_analysis['widget_types'][widget_type] = widget_analysis['widget_types'].get(widget_type, 0) + 1
        
        # Extract widget details
        widget_info = {
            'index': i,
            'type': widget_type,
            'title': widget_def.get('title', f'Widget {i+1}'),
            'has_legend': widget_def.get('legend', {}).get('enabled', False),
            'time_range': widget_def.get('time', {}),
            'raw_definition_size': len(str(widget_def))  # To gauge complexity
        }
        
        # Extract queries and metrics based on widget type
        requests_data = widget_def.get('requests', [])
        if requests_data:
            for req_index, req in enumerate(requests_data):
                if isinstance(req, dict):
                    # Extract queries from the 'queries' array (new Datadog format)
                    queries_array = req.get('queries', [])
                    for query_index, query_obj in enumerate(queries_array):
                        if isinstance(query_obj, dict):
                            query_text = query_obj.get('query', '')
                            if query_text:
                                widget_analysis['queries'].append({
                                    'widget_index': i,
                                    'widget_title': widget_info['title'],
                                    'query': query_text,
                                    'request_index': req_index,
                                    'query_index': query_index,
                                    'query_name': query_obj.get('name', f'query{query_index+1}'),
                                    'query_type': query_obj.get('data_source', 'metrics'),
                                    'aggregator': query_obj.get('aggregator', 'avg')
                                })
                    
                    # Also check for direct query (legacy format)
                    direct_query = req.get('q') or req.get('query', '') or req.get('apm_query', '') or req.get('log_query', '')
                    if direct_query and not queries_array:
                        widget_analysis['queries'].append({
                            'widget_index': i,
                            'widget_title': widget_info['title'],
                            'query': direct_query,
                            'request_index': req_index,
                            'query_index': 0,
                            'query_name': 'direct_query',
                            'query_type': req.get('data_source', 'metrics'),
                            'aggregator': req.get('aggregator', 'avg')
                        })
                    
                    # Extract formulas that reference the queries
                    formulas = req.get('formulas', [])
                    for formula_index, formula in enumerate(formulas):
                        if isinstance(formula, dict):
                            formula_text = formula.get('formula', '')
                            if formula_text:
                                # Map formula to actual query if possible
                                actual_query = ''
                                for query_obj in queries_array:
                                    if query_obj.get('name') == formula_text:
                                        actual_query = query_obj.get('query', '')
                                        break
                                
                                widget_analysis['metrics_tracked'].append({
                                    'widget_index': i,
                                    'widget_title': widget_info['title'],
                                    'formula': formula_text,
                                    'actual_query': actual_query,
                                    'formula_index': formula_index,
                                    'alias': formula.get('alias', 'No alias'),
                                    'cell_display_mode': formula.get('cell_display_mode', 'number')
                                })
                    
                    # Extract sort and response format information
                    if req.get('sort'):
                        sort_info = req.get('sort', {})
                        widget_analysis['queries'].append({
                            'widget_index': i,
                            'widget_title': widget_info['title'],
                            'query': f"Sort configuration: {sort_info}",
                            'request_index': req_index,
                            'query_index': -1,
                            'query_name': 'sort_config',
                            'query_type': 'configuration',
                            'aggregator': 'none'
                        })
        
        # For query_table widgets, extract columns information
        if widget_type == 'query_table':
            widget_info['has_search'] = widget_def.get('has_search', False)
            widget_info['title_size'] = widget_def.get('title_size', 'default')
            widget_info['title_align'] = widget_def.get('title_align', 'left')
        
        # Add custom fields based on widget type
        if widget_type == 'timeseries':
            widget_info['yaxis'] = widget_def.get('yaxis', {})
            widget_info['show_legend'] = widget_def.get('show_legend', False)
        elif widget_type == 'query_value':
            widget_info['precision'] = widget_def.get('precision', 2)
            widget_info['autoscale'] = widget_def.get('autoscale', True)
        elif widget_type == 'toplist':
            widget_info['style'] = widget_def.get('style', {})
        
        widget_analysis['widget_details'].append(widget_info)
        
        # If no queries were extracted but widget has content, add raw content
        if not requests_data and widget_def:
            widget_analysis['queries'].append({
                'widget_index': i,
                'widget_title': widget_info['title'],
                'query': f"Raw widget definition (no standard queries found): {str(widget_def)[:500]}...",
                'request_index': 0,
                'query_type': 'raw_content'
            })
    
    # Get actual current data from widgets
    print(f"🔄 MCP: Getting current data from widgets...")
    widget_data_result = get_widget_data_mcp(dashboard_id, time_range=time_range)
    
    current_data_summary = {
        'data_available': widget_data_result['success'],
        'widgets_with_data': [],
        'data_insights': []
    }
    
    if widget_data_result['success']:
        widgets_current_data = widget_data_result['data']['widgets_current_data']
        for widget_data in widgets_current_data:
            widget_summary = {
                'title': widget_data['widget_title'],
                'type': widget_data['widget_type'],
                'queries_successful': len([q for q in widget_data['queries_executed'] if q['status'] == 'success']),
                'queries_failed': len([q for q in widget_data['queries_executed'] if q['status'] == 'error']),
                'data_points_count': len(widget_data['data_points']),
                'current_values': []
            }
            
            # Extract current values from data points
            for series in widget_data['data_points']:
                if 'pointlist' in series and series['pointlist']:
                    latest_point = series['pointlist'][-1]  # Get latest data point
                    widget_summary['current_values'].append({
                        'metric': series.get('metric', 'unknown'),
                        'scope': series.get('scope', {}),
                        'latest_timestamp': latest_point[0] if len(latest_point) > 0 else None,
                        'latest_value': latest_point[1] if len(latest_point) > 1 else None
                    })
            
            current_data_summary['widgets_with_data'].append(widget_summary)
            
            # Generate insights based on current data
            if widget_summary['queries_failed'] > 0:
                current_data_summary['data_insights'].append(f"⚠️ {widget_data['widget_title']}: {widget_summary['queries_failed']} queries failed")
            
            if widget_summary['data_points_count'] == 0:
                current_data_summary['data_insights'].append(f"❌ {widget_data['widget_title']}: No data returned")
            elif widget_summary['data_points_count'] > 0:
                # Analyze current values for anomalies
                for value_info in widget_summary['current_values']:
                    if value_info['latest_value'] is not None:
                        if value_info['latest_value'] == 0:
                            current_data_summary['data_insights'].append(f"🔴 {widget_data['widget_title']}: {value_info['metric']} shows 0 containers running")
                        elif value_info['latest_value'] < 1:
                            current_data_summary['data_insights'].append(f"🟡 {widget_data['widget_title']}: {value_info['metric']} shows low value: {value_info['latest_value']}")

    # Dashboard summary
    dashboard_summary = {
        'basic_info': {
            'id': dashboard['id'],
            'title': dashboard['title'],
            'description': dashboard['description'],
            'layout_type': dashboard['layout_type'],
            'author': dashboard['author_handle'],
            'created': dashboard['created_at'],
            'modified': dashboard['modified_at'],
            'url': dashboard['url']
        },
        'template_variables': {
            'count': len(dashboard.get('template_variables', [])),
            'variables': [tv.get('name', 'unnamed') for tv in dashboard.get('template_variables', [])]
        },
        'widget_analysis': widget_analysis,
        'current_data': current_data_summary,
        'unique_metrics': len(set([m['formula'] for m in widget_analysis['metrics_tracked']] + 
                                [q['query'] for q in widget_analysis['queries']])),
        'complexity_score': len(widgets) + len(dashboard.get('template_variables', []))
    }
    
    return {
        "success": True,
        "error": None,
        "data": dashboard_summary
    } 