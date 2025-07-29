#!/usr/bin/env python3

import os
import base64
from mcp_loader import get_available_mcp_tools

def get_image_as_base64(image_path):
    """Convert image to base64 data URI"""
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                # Determine the image type
                if image_path.lower().endswith('.png'):
                    return f"data:image/png;base64,{encoded_string}"
                elif image_path.lower().endswith(('.jpg', '.jpeg')):
                    return f"data:image/jpeg;base64,{encoded_string}"
                elif image_path.lower().endswith('.gif'):
                    return f"data:image/gif;base64,{encoded_string}"
                else:
                    return f"data:image/png;base64,{encoded_string}"
        else:
            return None
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def create_simple_intro():
    """Create the Star Wars intro animation"""
    return """
    <script>
        // Define skip function for keyboard and click events
        function skipIntro() {
            const intro = document.getElementById('starwars-intro');
            if (intro) {
                intro.style.transition = 'opacity 0.5s ease-out';
                intro.style.opacity = '0';
                setTimeout(function() {
                    intro.remove();
                }, 500);
            }
        }
    </script>
    
    <!-- Star Wars Intro using proven portsoc/episodeiv CSS -->
    <div id="starwars-intro" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: #000;
        z-index: 9999;
        perspective: 50vh;
        overflow: hidden;
    ">
        <!-- Star field background -->
        <div id="stars" style="
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #000;
        "></div>
        
        <!-- Skip Button -->
        <div style="
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(79, 195, 247, 0.3);
            border: 2px solid #4fc3f7;
            border-radius: 5px;
            padding: 10px 20px;
            color: #4fc3f7;
            font-family: 'Orbitron', monospace;
            font-size: 0.9rem;
            cursor: pointer;
            z-index: 10;
            text-shadow: 0 0 10px #4fc3f7;
            transition: all 0.3s;
        " onclick="document.getElementById('starwars-intro').style.opacity='0';setTimeout(function(){document.getElementById('starwars-intro').remove()},500)" onmouseover="this.style.background='rgba(79, 195, 247, 0.5)'" onmouseout="this.style.background='rgba(79, 195, 247, 0.3)'">
            SKIP INTRO
        </div>
        
        <!-- Instructions -->
        <div style="
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: #4fc3f7;
            font-family: 'Orbitron', monospace;
            font-size: 0.8rem;
            opacity: 0.7;
            z-index: 10;
        ">Click anywhere or press any key to skip</div>

        
        <!-- Article with crawling text - using portsoc method -->
        <article style="
            font-family: arial, sans-serif;
            color: #FFE81F;
            text-align: justify;
            margin: auto;
            width: 15em;
            font-size: 6.666vw;
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;
            transform-origin: center bottom;
            transform: rotate3d(1, 0, 0, 45deg);
            animation: crawler 45s linear forwards;
            animation-delay: 2s;
            opacity: 0;
        ">
            <section>
                <header style="text-align: center;">
                    <h1 style="text-transform: uppercase; margin: 0; font-size: 1.2em; color: #FFE81F;">Episode V</h1>
                    <h1 style="text-transform: uppercase; margin: 0.5em 0 2em; font-size: 1.5em; color: #FFE81F;">The Ops Strike Back</h1>
                </header>
                
                <p style="color: #FFE81F;">The <strong style="text-transform: uppercase; font-weight: normal; color: #FFE81F;">Infrastructure Empire</strong> has struck back! Critical systems are down across the galaxy.</p>
                
                <p style="color: #FFE81F;">Young SRE agent <strong style="text-transform: uppercase; font-weight: normal; color: #FFE81F;">YODA</strong> must restore the monitoring systems and bring peace to the EVIL-CORP infrastructure...</p>
            </section>
        </article>
    </div>
    
    <style>
        @keyframes crawler {
            0% {
                transform: rotate3d(1, 0, 0, 45deg) translateY(100%);
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: rotate3d(1, 0, 0, 45deg) translateY(-50%);
                opacity: 0;
            }
        }
    </style>
    
    <script>
        // Wait for DOM and add event listeners
        document.addEventListener('DOMContentLoaded', function() {
            const intro = document.getElementById('starwars-intro');
            if (intro) {
                // Click anywhere to skip
                intro.addEventListener('click', skipIntro);
                
                // Add visual feedback that it's clickable
                intro.style.cursor = 'pointer';
            }
        });
        
        // Press any key to skip
        document.addEventListener('keydown', function(event) {
            const intro = document.getElementById('starwars-intro');
            if (intro && intro.style.display !== 'none') {
                skipIntro();
            }
        });
        
        // Auto-hide after 47 seconds (2s delay + 45s crawl)
        setTimeout(function() {
            const intro = document.getElementById('starwars-intro');
            if (intro) {
                intro.style.display = 'none';
            }
        }, 47000);
        
        // Emergency cleanup
        setTimeout(function() {
            const intro = document.getElementById('starwars-intro');
            if (intro) {
                intro.remove();
            }
        }, 49000);
    </script>
    """

def create_header():
    """Create the Star Wars themed header with YODA logo"""
    # Get the YODA image as base64
    yoda_image = get_image_as_base64("yoda.png")
    
    # Create the image HTML only if the image exists - MUCH BIGGER
    if yoda_image:
        image_html = f'<img src="{yoda_image}" alt="YODA" style="width: 150px; height: 150px; border-radius: 50%; border: 4px solid #00ffff; box-shadow: 0 0 25px #00ffff, 0 0 50px rgba(0,255,255,0.5);">'
    else:
        image_html = '<div style="width: 150px; height: 150px; border-radius: 50%; border: 4px solid #00ffff; background: linear-gradient(45deg, #00ffff, #0088cc); display: flex; align-items: center; justify-content: center; color: #000; font-weight: bold; font-size: 24px;">SR</div>'
    
    return f"""
    <div class="header holographic">
        <div style="display: flex; align-items: center; justify-content: center; gap: 15px;">
            {image_html}
            <div>
                <h1>YODA - Master SRE of the Galaxy</h1>
                <h2>⭐ Jedi-Level Infrastructure Monitoring & DataDog Mastery ⭐</h2>
            </div>
        </div>
        <p style="color: #88ccff; font-size: 0.9em; margin-top: 10px; text-align: center;">
            <span class="status-indicator status-online"></span>
            Galactic Command Center Online | 
            <span style="color: #00ffff;">Strong with the Force, your infrastructure will be</span>
        </p>
    </div>
    """

def create_sidebar():
    """Create the tools sidebar with available MCP tools"""
    tools = get_available_mcp_tools()
    tools_html = "<div class='sidebar'><h3>🛠️ Available Tools</h3><div class='tool-list'>"
    
    tool_categories = {
        "🔍 Monitors": [t for t in tools if 'monitor' in t.lower()],
        "📊 Dashboards": [t for t in tools if 'dashboard' in t.lower()],
        "📝 Logs": [t for t in tools if 'log' in t.lower()],
        "🎯 Events": [t for t in tools if 'event' in t.lower()],
        "📈 Metrics": [t for t in tools if 'metric' in t.lower()]
    }
    
    for category, cat_tools in tool_categories.items():
        if cat_tools:
            tools_html += f"<div style='color: #00ffff; font-weight: bold; margin: 10px 0 5px 0;'>{category}</div>"
            for tool in cat_tools:
                tools_html += f"<div class='tool-item'>{tool}</div>"
    
    tools_html += "</div></div>"
    return tools_html

def create_examples_sidebar():
    """Create the comprehensive examples sidebar"""
    return """
    <div class="sidebar" style="max-height: 600px; overflow-y: auto;">
        <h3>🌟 Jedi SRE Command Examples</h3>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #ff6b6b;">🚨 Critical Alerts & Monitors</h4>
            <div style="font-size: 11px; color: #88ccff; line-height: 1.4;">
                • "show me all P1 alerts"<br>
                • "get critical monitors"<br>
                • "show monitors in alert state"<br>
                • "find high priority incidents"<br>
                • "get all triggered monitors"
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #4ecdc4;">📊 Dashboard Analytics</h4>
            <div style="font-size: 11px; color: #88ccff; line-height: 1.4;">
                • "list all dashboards"<br>
                • "analyze production dashboard"<br>
                • "get dashboard metrics"<br>
                • "show system overview dashboard"<br>
                • "get widget data for performance"
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #ffe66d;">📝 Log Investigation</h4>
            <div style="font-size: 11px; color: #88ccff; line-height: 1.4;">
                • "search error logs from last hour"<br>
                • "find API errors in production"<br>
                • "analyze log patterns for service auth"<br>
                • "search logs for 500 errors"<br>
                • "get log streams for application"<br>
                • "find exceptions in microservice logs"
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #ff9f43;">🎯 Event Tracking</h4>
            <div style="font-size: 11px; color: #88ccff; line-height: 1.4;">
                • "show recent deployment events"<br>
                • "get deployment events for API service"<br>
                • "find alert events from last day"<br>
                • "analyze event patterns"<br>
                • "search events for kubernetes"<br>
                • "get deployment history"
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #a55eea;">📈 Performance Metrics</h4>
            <div style="font-size: 11px; color: #88ccff; line-height: 1.4;">
                • "show CPU usage metrics"<br>
                • "analyze memory trends"<br>
                • "get system metrics for last hour"<br>
                • "show application performance"<br>
                • "query database metrics"<br>
                • "analyze response time trends"<br>
                • "get disk usage metrics"
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #26de81;">🔍 Advanced Queries</h4>
            <div style="font-size: 11px; color: #88ccff; line-height: 1.4;">
                • "search metrics for database connections"<br>
                • "find high error rate services"<br>
                • "analyze infrastructure trends"<br>
                • "get metric metadata for system.cpu"<br>
                • "show network metrics by host"<br>
                • "query container metrics"
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #fd79a8;">🛠️ Troubleshooting</h4>
            <div style="font-size: 11px; color: #88ccff; line-height: 1.4;">
                • "find root cause of high latency"<br>
                • "analyze service dependencies"<br>
                • "search for timeout errors"<br>
                • "investigate memory leaks"<br>
                • "check service health patterns"<br>
                • "analyze deployment impact"
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #6c5ce7;">🌐 Infrastructure Health</h4>
            <div style="font-size: 11px; color: #88ccff; line-height: 1.4;">
                • "show overall system health"<br>
                • "get infrastructure overview"<br>
                • "analyze resource utilization"<br>
                • "check service availability"<br>
                • "monitor cloud costs"<br>
                • "verify backup systems"
            </div>
        </div>
        
        <div style="padding: 10px; background: rgba(0,255,255,0.1); border-radius: 8px; margin-top: 15px;">
            <p style="color: #00ffff; font-size: 10px; margin: 0; text-align: center;">
                <strong>💡 Pro Tip:</strong><br>
                Use natural language - YODA understands your intent!<br>
                <em>"Debug the API issues"</em> works just as well as<br>
                <em>"Search error logs for API service"</em>
            </p>
        </div>
    </div>
    """

def create_footer():
    """Create the footer component"""
    return """
    <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
        <p>🌟 YODA v4.0 - Powered by the Force & DataDog APIs 🌟</p>
        <p style="color: #00ffff;">Remember: With great monitoring power comes great reliability responsibility</p>
    </div>
    """

def get_common_commands():
    """Get the list of common commands for the dropdown"""
    return [
        "show me all P1 alerts",
        "get critical monitors", 
        "show monitors in alert state",
        "search error logs from last hour",
        "find API errors in production",
        "show recent deployment events",
        "get deployment events for API service",
        "show CPU usage metrics",
        "analyze memory trends", 
        "get system metrics for last hour",
        "list all dashboards",
        "analyze production dashboard",
        "search for service metrics",
        "show me trace metrics for all services",
        "find high error rate services",
        "analyze infrastructure trends",
        "search logs for 500 errors",
        "get alert events from last day",
        "show application performance",
        "query database metrics"
    ]

def get_initial_messages():
    """Get initial welcome messages for the chatbot"""
    return [
        {"role": "assistant", "content": "🤖 **YODA DROID ONLINE** - *Systems initialized, Commander. The Empire's monitoring apparatus is at your command. How may this humble droid serve the cause today?*"},
        {"role": "assistant", "content": "⚡ **TRANSMISSION**: *Young Padawan, try commanding me with: 'show recent alerts', 'analyze CPU metrics', or 'search for disturbances in the logs'. The Force flows through our monitoring systems.*"}
    ] 