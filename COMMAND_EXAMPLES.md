# 🤖 YODA MCP Commands Reference

> **Note**: All service names in this documentation are **generic examples**. YODA will automatically discover your real service names dynamically!

## 📊 **KUBERNETES METRICS** (NEW!)
```
# Get K8s metrics for specific deployment
"get kubernetes metrics for frontend-app"
"show me CPU and memory for frontend-app"
"kubernetes performance for frontend-app over 2 hours"
"get k8s metrics for frontend-app over 30 minutes"

# Get all K8s metrics
"show me all kubernetes metrics"
"get kubernetes performance for all deployments"
```

## 🚨 **MONITORS & ALERTS** (FIXED!)
```
# Get specific priority alerts
"show me P1 alerts"
"get P1 priority monitors"
"check alerts with priority 1"
"show me critical alerts"

# Get alerts by state
"show me all alerts"
"get monitors in alert state"
"check alert status"

# Combined filters
"get P1 alerts that are currently alerting"
"show me high priority monitors in alert state"
```

## 📈 **GENERAL METRICS**
```
# Application metrics
"get application metrics for backend-api"
"show me app performance for auth-service"
"application metrics for database-service over 4 hours"

# System metrics
"get system metrics"
"show me CPU and memory for all hosts"
"system performance over 1 day"

# Custom metric queries
"query metric avg:system.cpu.user{*}"
"get metric kubernetes.cpu.usage.total for frontend-app"
```

## 🚀 **APM METRICS** (100% GENERIC - AUTO-DISCOVERY!)
```
# Get all APM/trace metrics (auto-discovers everything)
"get apm metrics"
"show me APM performance" 
"get trace metrics for last hour"

# APM metrics for specific services (finds real services automatically)
"get apm metrics for auth-service"
"get apm metrics for payment-api"
"show me monitoring agent performance"
"apm metrics for web-framework operations"

# Specific metric types (auto-discovered: hits, duration, apdex, errors, etc.)
"get apm request counts"
"show me response times from traces" 
"get apdex scores for last 2 hours"

# Example operations that could be auto-discovered:
"get apm metrics for UserService"
"show me loginEvent performance"  
"trace metrics for PaymentProcessor operations"
"monitoring agent trace metrics"

# ZERO HARDCODING - Everything discovered from your real environment!
# Auto-discovers all available trace metrics:
# - Types: hits, duration, apdex, by_http_status, errors
# - Services: monitoring-agent, auth-api, backend-service, web-framework, rpc-service, gateway
# - Operations: request, trace_processor, command, query
```

## 🔍 **LOGS**
```
# Search logs
"search logs for error"
"get error logs from backend-api"
"show me logs with 'exception' from last hour"

# Stream logs
"get log streams"
"show me recent log activity"
```

## 🚀 **EVENTS**
```
# Deployment events
"get deployment events"
"show me deployments from today"
"deployment events for auth-service over 1 week"

# Recent events
"get recent events"
"show me what happened in the last 4 hours"

# Search events
"search events for 'restart'"
"find events about 'error' from yesterday"
```

## 📊 **DASHBOARDS**
```
# List dashboards
"list dashboards"
"show me all available dashboards"
"get production dashboards"

# Get specific dashboard
"get dashboard for production"
"show me infrastructure dashboard"
```

## 🎯 **INTERACTIVE COMMANDS** (YODA will ask for details)
```
# Vague commands that trigger questions
"show me metrics" → YODA asks which service
"check alerts" → YODA asks which priority
"get logs" → YODA asks which service
"show me events" → YODA asks time range
```

## 🏭 **KNOWN SERVICES** (use these in commands)
```
# Kubernetes Deployments
- front
- api


# Other Services

```

## ⏰ **TIME RANGES** (use any of these)
```
- "15 minutes" or "15m"
- "1 hour" or "1h"  
- "4 hours" or "4h"
- "1 day" or "1d"
- "3 days" or "3d"
- "1 week" or "1w"
- "1 month" or "1m"
```

## 🎖️ **PRIORITY LEVELS** (for alerts)
```
- "P1" or "1" (Critical)
- "P2" or "2" (Important)  
- "P3" or "3" (Normal)
- "high", "normal", "low"
```

## 💡 **EXAMPLE CONVERSATIONS**
```
User: "show me metrics"
YODA: "Which deployment requires your attention, Commander? (frontend-app, auth-service, etc.)"
User: "frontend-app"
YODA: [executes get_kubernetes_metrics for frontend-app]

User: "check alerts"  
YODA: "What priority level concerns you? (P1 for critical, P2 for important, etc.)"
User: "P1"
YODA: [executes get_monitors with P1 filter]
```

## 🛠️ **DEBUG COMMANDS**
```
"show tools" - List all available MCP tools
"list tools" - Same as above
"available tools" - Same as above
"debug tools" - Same as above
```

## ✅ **WORKING FUNCTIONS**
- ✅ get_kubernetes_metrics (NEW!)
- ✅ get_apm_metrics (NEW! - 100% Generic)
- ✅ get_available_services (NEW! - Dynamic Discovery)
- ✅ get_monitors (FIXED priority filtering!)
- ✅ get_deployment_events (IMPROVED search!)
- ✅ get_application_metrics  
- ✅ get_system_metrics
- ✅ search_events
- ✅ get_recent_events
- ✅ search_logs
- ✅ search_error_logs
- ✅ list_dashboards
- ✅ query_metrics
- ✅ search_metrics

All functions now return **REAL DATA** from Datadog, not fake responses! 🎉

### 🆕 **LATEST ADDITIONS:**
- **get_available_services**: 🔥 **GAME CHANGER!** Dynamically discovers services + **INTELLIGENT CACHE** (2,640x faster!)
- **get_apm_metrics**: 100% generic auto-discovery (723 trace metrics), works with any environment
- **get_deployment_events**: Improved multi-query search finds actual deployment events  
- **get_kubernetes_metrics**: Works perfectly with real K8s deployments

### 🚀 **CACHE SYSTEM:**
- **services_cache.json**: Local cache file with 4-hour duration
- **2,640x performance boost** (0.001s vs 2.6s)
- **Auto-refresh**: Expires and updates automatically
- **Force refresh option**: For getting latest data

### 🤖 **YODA NOW TRULY INTERACTIVE:**
YODA will automatically discover your real services and ask intelligent questions instead of guessing!

## 🔍 **DYNAMIC SERVICE DISCOVERY** (NEW! - WITH INTELLIGENT CACHE!)
```
# Discover available services (SUPER FAST with caching!)
"what services are available?"
"show me available services" 
"list active services"

# Force refresh cache for latest data
"refresh available services"
"get latest services"

# YODA automatically calls get_available_services() for vague questions:
"show me metrics" → YODA discovers services first, then asks which one
"check logs" → YODA shows real available services, then asks which one  
"any errors?" → YODA finds real services, then asks which to check

# ⚡ CACHE PERFORMANCE:
# - First call: 2.6 seconds (analyzes 1000 logs)
# - Cached calls: 0.001 seconds (2,640x faster!)
# - Cache duration: 4 hours
# - Auto-refresh when expired

# Example services that could be discovered:
# - backend-api (500+ logs, 10+ hosts) - High activity
# - frontend-app (200+ logs, 12+ hosts) - Medium activity
# - worker-service (100+ logs, 5+ hosts) - Medium activity  
# - auth-service, payment-api, notification-service...
``` 