import requests
import os
from dotenv import load_dotenv
from colorama import Fore
import urllib3
urllib3.disable_warnings()

# Load environment variables
load_dotenv()
DD_API_KEY = os.getenv('DD_API_KEY')
DD_APP_KEY = os.getenv('DD_APP_KEY')
DD_SITE = os.getenv('DD_SITE', 'api.datadoghq.com')

def get_monitors_mcp(group_states=None, priority=None, tags=None, limit=None, **kwargs):
    """
    MCP Function to get Datadog monitors
    Supports all group_states, priorities, tags and limit
    
    Args:
        group_states: List of states ['alert', 'warn', 'no data', 'ignored', 'skipped', 'unknown', 'ok']
        priority: Priority filter ['P1', 'P2', 'P3', 'P4', 'P5'] or None for all
        tags: Tag filter string
        limit: Maximum number of results
    """
    
    print(f"🔍 DEBUG: get_monitors_mcp called with:")
    print(f"   group_states: {group_states}")
    print(f"   priority: {priority}")
    print(f"   tags: {tags}")
    print(f"   limit: {limit}")
    
    # VERIFY KEYS
    print(f"🔍 DEBUG: Checking API keys...")
    print(f"   DD_API_KEY exists: {bool(DD_API_KEY)}")
    print(f"   DD_APP_KEY exists: {bool(DD_APP_KEY)}")
    print(f"   DD_SITE: {DD_SITE}")
    
    if not all([DD_API_KEY, DD_APP_KEY]):
        print(f"❌ ERROR: Missing API keys!")
        return {
            "success": False,
            "error": "Missing DD_API_KEY or DD_APP_KEY",
            "data": []
        }
    
    # DATADOG API CALL
    try:
        url = f"https://{DD_SITE}/api/v1/monitor"
        headers = {
            'DD-API-KEY': DD_API_KEY,
            'DD-APPLICATION-KEY': DD_APP_KEY,
            'Accept': 'application/json'
        }
        
        # Add query parameters if provided
        params = {}
        if group_states:
            params['group_states'] = ','.join(group_states)
        if tags:
            params['tags'] = tags
        
        print(f"🔄 MCP: Calling Datadog API...")
        print(f"🔍 DEBUG: URL: {url}")
        print(f"🔍 DEBUG: Headers: {dict(headers)}")
        print(f"🔍 DEBUG: Params: {params}")
        
        response = requests.get(url, headers=headers, params=params, verify=False)
        
        print(f"🔍 DEBUG: Response status: {response.status_code}")
        print(f"🔍 DEBUG: Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            monitors = response.json()
            print(f"🔍 DEBUG: Total monitors returned from API: {len(monitors)}")
            
            # Log first few monitors for debugging
            if monitors:
                print(f"🔍 DEBUG: First monitor sample:")
                first_monitor = monitors[0]
                print(f"   ID: {first_monitor.get('id')}")
                print(f"   Name: {first_monitor.get('name')}")
                print(f"   Overall State: {first_monitor.get('overall_state')}")
                print(f"   Priority: {first_monitor.get('priority')}")
                print(f"   Type: {first_monitor.get('type')}")
            
            filtered_monitors = []
            
            print(f"🔍 DEBUG: Starting to filter {len(monitors)} monitors...")
            
            for monitor in monitors:
                print(f"🔍 DEBUG: Processing monitor {monitor.get('id')} - {monitor.get('name')[:50]}")
                print(f"   Current state: '{monitor.get('overall_state')}'")
                
                # Filter by group_states if provided
                if group_states:
                    monitor_state = monitor.get('overall_state', '').lower()
                    print(f"   Requested states: {group_states}")
                    print(f"   Monitor state (lowercase): '{monitor_state}'")
                    
                    # Map Datadog states to our filter
                    state_mapping = {
                        'alert': 'Alert',
                        'warn': 'Warn', 
                        'no data': 'No Data',
                        'ignored': 'Ignored',
                        'skipped': 'Skipped',
                        'unknown': 'Unknown',
                        'ok': 'OK'
                    }
                    
                    # Check if current monitor state matches any requested states
                    matches_state = False
                    for requested_state in group_states:
                        mapped_state = state_mapping.get(requested_state.lower(), '')
                        print(f"   Checking '{requested_state}' -> '{mapped_state}' vs '{monitor.get('overall_state')}'")
                        if mapped_state == monitor.get('overall_state'):
                            matches_state = True
                            print(f"   ✅ STATE MATCH FOUND!")
                            break
                    
                    if not matches_state:
                        print(f"   ❌ No state match, skipping this monitor")
                        continue
                    else:
                        print(f"   ✅ State matches, continuing to priority check...")
                
                # Filter by priority if provided  
                if priority:
                    monitor_priority = monitor.get('priority')
                    # Handle both string and numeric priorities
                    if isinstance(monitor_priority, int):
                        monitor_priority = f"P{monitor_priority}"
                    
                    if monitor_priority != priority:
                        continue
                
                # Build monitor info
                monitor_info = {
                    "id": monitor.get('id'),
                    "name": monitor.get('name'),
                    "status": monitor.get('overall_state'),
                    "message": monitor.get('message', ''),
                    "query": monitor.get('query', ''),
                    "priority": monitor.get('priority'),
                    "last_triggered": monitor.get('last_triggered_ts'),
                    "tags": monitor.get('tags', []),
                    "type": monitor.get('type')
                }
                filtered_monitors.append(monitor_info)
                
                # Apply limit if provided
                if limit and len(filtered_monitors) >= limit:
                    break
            
            print(f"🔍 DEBUG: Final results:")
            print(f"   Total monitors from API: {len(monitors)}")
            print(f"   Filtered monitors: {len(filtered_monitors)}")
            print(f"   Requested group_states: {group_states}")
            print(f"   Requested priority: {priority}")
            
            return {
                "success": True,
                "error": None,
                "data": filtered_monitors,
                "total_monitors": len(monitors),
                "filtered_alerts": len(filtered_monitors)
            }
            
        else:
            print(f"❌ ERROR: Datadog API error!")
            print(f"   Status code: {response.status_code}")
            print(f"   Response text: {response.text[:500]}")
            return {
                "success": False,
                "error": f"Datadog API error: {response.status_code}",
                "data": []
            }
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "data": []
        } 