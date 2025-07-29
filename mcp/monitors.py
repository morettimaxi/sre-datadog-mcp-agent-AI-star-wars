import requests
import os
import sys
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

def get_monitors(group_states=None, priority=None, names=None, tags=None, monitor_tags=None):
    """
    Get monitors from Datadog with optional filtering.
    
    Args:
        group_states: List of states to filter by (e.g., ['alert', 'warn'])
        priority: Priority to filter by (e.g., 'P1', 'P2', etc.)
        names: List of monitor names to filter by
        tags: List of tags to filter by
        monitor_tags: List of monitor tags to filter by
    """
    load_dotenv()
    
    DD_API_KEY = os.getenv('DD_API_KEY')
    DD_APP_KEY = os.getenv('DD_APP_KEY')
    DD_SITE = os.getenv('DD_SITE', 'api.datadoghq.com')
    
    if not DD_API_KEY or not DD_APP_KEY:
        return {"error": "Missing DD_API_KEY or DD_APP_KEY environment variables"}
    
    url = f"https://{DD_SITE}/api/v1/monitor"
    headers = {
        'DD-API-KEY': DD_API_KEY,
        'DD-APPLICATION-KEY': DD_APP_KEY,
        'Accept': 'application/json'
    }
    
    # Build API parameters
    params = {}
    if group_states:
        # Join multiple states with comma for API call
        params['group_states'] = ','.join(group_states)
    
    if names:
        params['name'] = ','.join(names)
    
    if tags:
        params['tags'] = ','.join(tags)
    
    if monitor_tags:
        params['monitor_tags'] = ','.join(monitor_tags)
    
    try:
        # Debug: Show API call being made
        debug_info = []
        if group_states:
            debug_info.append(f"group_states={group_states}")
        if priority:
            debug_info.append(f"priority='{priority}'")
        if names:
            debug_info.append(f"names={names}")
        if tags:
            debug_info.append(f"tags={tags}")
        if monitor_tags:
            debug_info.append(f"monitor_tags={monitor_tags}")
        
        debug_params = ", ".join(debug_info) if debug_info else "no filters"
        print(f"🔄 YODA: Calling DataDog API with {debug_params}")
        print(f"🌐 API URL: {url}")
        if params:
            print(f"📋 API Params: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30, verify=get_requests_verify())
        
        if response.status_code == 200:
            monitors = response.json()
            print(f"📥 API Response: {len(monitors)} monitors received from DataDog")
            
            # Client-side filtering for more precise control
            filtered_monitors = []
            skipped_by_state = 0
            skipped_by_priority = 0
            
            for monitor in monitors:
                # State filtering (if needed for extra precision)
                if group_states:
                    monitor_state = monitor.get('overall_state', '').lower()
                    # Convert API states to lowercase for comparison
                    target_states = [state.lower() for state in group_states]
                    
                    if monitor_state not in target_states:
                        skipped_by_state += 1
                        continue
                
                # Priority filtering
                if priority:
                    monitor_priority = monitor.get('priority')
                    # Handle both string and numeric priority formats
                    # Convert both to strings for comparison
                    if monitor_priority is not None:
                        monitor_priority_str = str(monitor_priority)
                        search_priority = str(priority)
                        search_priority_no_p = search_priority.replace('P', '')
                        
                        # Check if priorities match (P1/1, P2/2, etc.)
                        if (monitor_priority_str != search_priority and 
                            monitor_priority_str != search_priority_no_p and
                            f"P{monitor_priority_str}" != search_priority):
                            skipped_by_priority += 1
                            continue
                    else:
                        # If monitor has no priority but we're filtering by priority, skip it
                        skipped_by_priority += 1
                        continue
                
                # Add monitor to results
                filtered_monitors.append({
                    "id": monitor.get('id'),
                    "name": monitor.get('name'),
                    "status": monitor.get('overall_state'),  # Changed from 'state' to 'status'
                    "priority": monitor.get('priority'),
                    "type": monitor.get('type'),
                    "query": monitor.get('query'),
                    "message": monitor.get('message'),
                    "tags": monitor.get('tags', []),
                    "created": monitor.get('created'),
                    "modified": monitor.get('modified'),
                    "creator": monitor.get('creator', {}).get('name'),
                })
            
            # Summary with clean output
            total_fetched = len(monitors)
            total_filtered = len(filtered_monitors)
            
            # Debug summary
            print(f"🎯 Filtering Summary:")
            print(f"   📊 Total received from API: {total_fetched}")
            print(f"   🚫 Skipped by state filter: {skipped_by_state}")
            print(f"   🚫 Skipped by priority filter: {skipped_by_priority}")
            print(f"   ✅ Final results: {total_filtered}")
            print()
            
            result = {
                "monitors": filtered_monitors,
                "summary": {
                    "total_fetched_from_api": total_fetched,
                    "total_after_filtering": total_filtered,
                    "filters_applied": {
                        "group_states": group_states,
                        "priority": priority,
                        "names": names,
                        "tags": tags,
                        "monitor_tags": monitor_tags
                    }
                }
            }
            
            print(f"📊 Found {total_filtered} results:")
            print()
            
            for i, monitor in enumerate(filtered_monitors, 1):
                state_emoji = "🔴" if monitor['status'] == 'Alert' else "🟡" if monitor['status'] == 'Warn' else "🟢"
                print(f"{state_emoji} {i}. {monitor['name']}")
                print(f"   Status: {monitor['status']}")
                if monitor['priority']:
                    print(f"   Priority: {monitor['priority']}")
                print()
            
            return result
            
        else:
            error_msg = f"API Error {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "data": []
            }
            
    except Exception as e:
        error_msg = f"Request failed: {str(e)}"
        print(f"💥 {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "data": []
        }

def get_monitors_mcp(group_states=None, priority=None, names=None, tags=None, monitor_tags=None, **kwargs):
    """
    MCP Function to get monitors from Datadog
    
    Args:
        group_states (list): List of states to filter by (e.g., ['alert', 'warn'])
        priority (str): Priority to filter by (e.g., 'P1', 'P2', etc.)
        names (list): List of monitor names to filter by
        tags (list): List of tags to filter by
        monitor_tags (list): List of monitor tags to filter by
    """
    return get_monitors(group_states=group_states, priority=priority, names=names, tags=tags, monitor_tags=monitor_tags)

def get_monitors_by_tag_mcp(tag_filter, group_states=None, priority=None, **kwargs):
    """
    MCP Function to get monitors filtered by a specific tag
    
    Args:
        tag_filter (str): Tag to filter by (e.g., "env:production", "service:web")
        group_states (list): List of states to filter by (e.g., ['alert', 'warn'])
        priority (str): Priority to filter by (e.g., 'P1', 'P2', etc.)
    
    Examples:
        get_monitors_by_tag_mcp("env:production")
        get_monitors_by_tag_mcp("service:web", group_states=["alert"])
        get_monitors_by_tag_mcp("product:apm", priority="P1")
    """
    print(f"🏷️ MCP: Getting monitors for tag '{tag_filter}'")
    
    result = get_monitors(group_states=group_states, priority=priority, tags=[tag_filter])
    
    if isinstance(result, dict) and 'monitors' in result:
        monitors = result['monitors']
        print(f"📊 MCP Result: Found {len(monitors)} monitors with tag '{tag_filter}'")
        
        return {
            "success": True,
            "error": None,
            "data": monitors,
            "filters": {
                "tag": tag_filter,
                "group_states": group_states,
                "priority": priority
            },
            "total_monitors": len(monitors),
            "summary": result.get('summary', {})
        }
    elif isinstance(result, dict) and 'error' in result:
        return {
            "success": False,
            "error": result['error'],
            "data": []
        }
    else:
        return {
            "success": False,
            "error": "Unexpected response format from monitors API",
            "data": []
        }

def get_monitors_by_environment_mcp(environment, group_states=None, priority=None, **kwargs):
    """
    MCP Function to get monitors for a specific environment
    
    Args:
        environment (str): Environment name (e.g., "production", "staging", "development")
        group_states (list): List of states to filter by (e.g., ['alert', 'warn'])
        priority (str): Priority to filter by (e.g., 'P1', 'P2', etc.)
    
    Examples:
        get_monitors_by_environment_mcp("production")
        get_monitors_by_environment_mcp("staging", group_states=["alert"])
    """
    tag_filter = f"env:{environment}"
    print(f"🌍 MCP: Getting monitors for environment '{environment}' (tag: {tag_filter})")
    
    return get_monitors_by_tag_mcp(tag_filter, group_states=group_states, priority=priority, **kwargs)

def get_monitors_by_service_mcp(service, group_states=None, priority=None, **kwargs):
    """
    MCP Function to get monitors for a specific service
    
    Args:
        service (str): Service name (e.g., "web-backend", "api", "database")
        group_states (list): List of states to filter by (e.g., ['alert', 'warn'])
        priority (str): Priority to filter by (e.g., 'P1', 'P2', etc.)
    
    Examples:
        get_monitors_by_service_mcp("web-backend")
        get_monitors_by_service_mcp("api", group_states=["alert", "warn"])
    """
    tag_filter = f"service:{service}"
    print(f"🔧 MCP: Getting monitors for service '{service}' (tag: {tag_filter})")
    
    return get_monitors_by_tag_mcp(tag_filter, group_states=group_states, priority=priority, **kwargs)

def get_monitors_by_multiple_tags_mcp(tags, group_states=None, priority=None, **kwargs):
    """
    MCP Function to get monitors filtered by multiple tags (AND logic)
    
    Args:
        tags (list): List of tags to filter by (e.g., ["env:production", "service:web-backend"])
        group_states (list): List of states to filter by (e.g., ['alert', 'warn'])
        priority (str): Priority to filter by (e.g., 'P1', 'P2', etc.)
    
    Examples:
        get_monitors_by_multiple_tags_mcp(["env:production", "service:web-backend"])
        get_monitors_by_multiple_tags_mcp(["product:apm", "check_status:live"], group_states=["alert"])
    """
    print(f"🏷️ MCP: Getting monitors for tags {tags}")
    
    result = get_monitors(group_states=group_states, priority=priority, tags=tags)
    
    if isinstance(result, dict) and 'monitors' in result:
        monitors = result['monitors']
        print(f"📊 MCP Result: Found {len(monitors)} monitors with tags {tags}")
        
        return {
            "success": True,
            "error": None,
            "data": monitors,
            "filters": {
                "tags": tags,
                "group_states": group_states,
                "priority": priority
            },
            "total_monitors": len(monitors),
            "summary": result.get('summary', {})
        }
    elif isinstance(result, dict) and 'error' in result:
        return {
            "success": False,
            "error": result['error'],
            "data": []
        }
    else:
        return {
            "success": False,
            "error": "Unexpected response format from monitors API",
            "data": []
        } 

def get_available_monitor_tags_mcp(force_refresh=False, **kwargs):
    """
    MCP Function to get all available tags from monitors with intelligent caching
    
    Args:
        force_refresh (bool): Force refresh cache even if valid
    """
    import json
    import os
    from datetime import datetime
    import time
    
    # Cache configuration
    CACHE_FILE = 'monitor_tags_cache.json'
    CACHE_DURATION_HOURS = 4  # Cache expires after 4 hours
    
    print(f"🏷️ MCP: Discovering available monitor tags...")
    
    # Check cache first (unless force refresh)
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
            
            cache_age_hours = (datetime.now() - datetime.fromtimestamp(cache_data['timestamp'])).total_seconds() / 3600
            
            # Check if cache is fresh
            if 'timestamp' in cache_data and cache_age_hours < CACHE_DURATION_HOURS:
                print(f"✅ Using cached monitor tags from {datetime.fromtimestamp(cache_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')} (age: {cache_age_hours:.1f}h)")
                
                return {
                    "success": True,
                    "error": None,
                    "data": cache_data['tags_data'],
                    "cache_info": {
                        "cache_age_hours": round(cache_age_hours, 1),
                        "cache_file": CACHE_FILE,
                        "discovery_method": "cache"
                    }
                }
            else:
                print(f"⚠️ Cache expired ({cache_age_hours:.1f}h old, max {CACHE_DURATION_HOURS}h). Refreshing from API.")
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}. Refreshing from API.")
    elif force_refresh:
        print(f"🔄 Force refresh requested. Fetching fresh data from API.")
    
    # Get all monitors (no filtering) - this is the expensive call
    print(f"📊 Fetching ALL monitors from Datadog API...")
    result = get_monitors()
    
    if isinstance(result, dict) and 'monitors' in result:
        monitors = result['monitors']
        print(f"📊 Analyzing {len(monitors)} monitors for tag discovery")
        
        # Extract and count tags
        tag_counts = {}
        environment_tags = {}
        service_tags = {}
        product_tags = {}
        other_tags = {}
        
        for monitor in monitors:
            tags = monitor.get('tags', [])
            for tag in tags:
                # Count all tags
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Categorize tags
                if tag.startswith('env:'):
                    env_name = tag.replace('env:', '')
                    environment_tags[env_name] = environment_tags.get(env_name, 0) + 1
                elif tag.startswith('service:'):
                    service_name = tag.replace('service:', '')
                    service_tags[service_name] = service_tags.get(service_name, 0) + 1
                elif tag.startswith('product:'):
                    product_name = tag.replace('product:', '')
                    product_tags[product_name] = product_tags.get(product_name, 0) + 1
                else:
                    other_tags[tag] = other_tags.get(tag, 0) + 1
        
        # Sort by frequency
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        sorted_environments = sorted(environment_tags.items(), key=lambda x: x[1], reverse=True)
        sorted_services = sorted(service_tags.items(), key=lambda x: x[1], reverse=True)
        sorted_products = sorted(product_tags.items(), key=lambda x: x[1], reverse=True)
        sorted_others = sorted(other_tags.items(), key=lambda x: x[1], reverse=True)
        
        print(f"🔍 Found {len(tag_counts)} unique tags:")
        print(f"   🌍 {len(environment_tags)} environments")
        print(f"   🔧 {len(service_tags)} services")
        print(f"   📦 {len(product_tags)} products")
        print(f"   🏷️ {len(other_tags)} other tags")
        
        # Prepare data for caching and response
        tags_data = {
            "total_monitors_analyzed": len(monitors),
            "total_unique_tags": len(tag_counts),
            "all_tags": sorted_tags,
            "environments": sorted_environments,
            "services": sorted_services, 
            "products": sorted_products,
            "other_tags": sorted_others,
            "tag_summary": {
                "most_common_tag": sorted_tags[0] if sorted_tags else None,
                "environment_count": len(environment_tags),
                "service_count": len(service_tags),
                "product_count": len(product_tags)
            }
        }
        
        # Save to cache
        cache_data = {
            'timestamp': int(time.time()),
            'tags_data': tags_data,
            'total_monitors': len(monitors)
        }
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=4)
            print(f"✅ Monitor tags cached to {CACHE_FILE}")
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
        
        return {
            "success": True,
            "error": None,
            "data": tags_data,
            "cache_info": {
                "cache_file": CACHE_FILE,
                "discovery_method": "fresh_api_call",
                "cached_at": datetime.now().isoformat()
            }
        }
    else:
        return {
            "success": False,
            "error": "Failed to fetch monitors for tag discovery",
            "data": []
        } 
