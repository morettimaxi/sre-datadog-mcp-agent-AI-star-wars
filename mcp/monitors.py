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
            
            return {
                "success": True,
                "data": filtered_monitors
            }
            
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