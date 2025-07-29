#!/usr/bin/env python3

import gradio as gr
import os
from dotenv import load_dotenv
from yoda_ui import create_yoda_ui

# Load environment variables
load_dotenv()

def warm_up_caches():
    """
    Optional: Warm up caches at startup for better performance
    Set PRELOAD_CACHES=true in .env to enable
    """
    preload = os.getenv('PRELOAD_CACHES', 'false').lower() in ('true', '1', 'yes')
    
    if preload:
        print("🔥 Warming up caches at startup...")
        try:
            # Pre-populate services cache
            from mcp.logs import get_available_services_mcp
            print("📋 Pre-loading services cache...")
            services_result = get_available_services_mcp()
            
            if services_result['success']:
                services_data = services_result['data']
                print(f"   ✅ Found {len(services_data)} active services")
                if services_data:
                    # Show top 5 most active services
                    top_services = services_data[:5]
                    print("   🏆 Top active services:")
                    for i, service in enumerate(top_services, 1):
                        print(f"      {i}. {service['name']} ({service['log_count']} logs)")
                    if len(services_data) > 5:
                        print(f"      ... and {len(services_data) - 5} more services")
            
            # Pre-populate monitor tags cache  
            from mcp.monitors import get_available_monitor_tags_mcp
            print("🏷️ Pre-loading monitor tags cache...")
            tags_result = get_available_monitor_tags_mcp()
            
            if tags_result['success']:
                tags_data = tags_result['data']
                print(f"   ✅ Analyzed {tags_data['total_monitors_analyzed']} monitors")
                print(f"   🏷️ Found {tags_data['total_unique_tags']} unique tags")
                print(f"   🌍 Environments: {tags_data['tag_summary']['environment_count']}")
                print(f"   🔧 Services: {tags_data['tag_summary']['service_count']}")
                print(f"   📦 Products: {tags_data['tag_summary']['product_count']}")
                
                # Show top environments and services
                if tags_data['environments']:
                    top_env = tags_data['environments'][0]
                    print(f"   🏆 Top environment: {top_env[0]} ({top_env[1]} monitors)")
                
                if tags_data['services']:
                    top_service = tags_data['services'][0]
                    print(f"   🏆 Top service: {top_service[0]} ({top_service[1]} monitors)")
            
            print("✅ Cache warm-up completed! All queries will now be super fast ⚡")
        except Exception as e:
            print(f"⚠️ Cache warm-up failed (will work on-demand): {e}")
    else:
        print("💡 Tip: Set PRELOAD_CACHES=true in .env to warm up caches at startup")

def main():
    print("🤖 YODA Systems Initializing...")
    
    # Warm up caches if enabled
    warm_up_caches()
    
    # Create the Gradio interface
    interface = create_yoda_ui()
    
    # Launch the interface
    print("🚀 Launching YODA Interface...")
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    )

if __name__ == "__main__":
    main() 