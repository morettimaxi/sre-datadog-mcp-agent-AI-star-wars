#!/usr/bin/env python3

import os
import sys
import subprocess

def install_requirements():
    """Install required packages"""
    print("🔧 Installing UI dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_ui.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def check_env_file():
    """Check if .env file exists with required keys"""
    if not os.path.exists('.env'):
        print("⚠️ .env file not found!")
        print("Creating sample .env file...")
        with open('.env', 'w') as f:
            f.write("# OpenAI API Configuration\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n\n")
            f.write("# DataDog API Configuration\n")
            f.write("DD_API_KEY=your_datadog_api_key_here\n")
            f.write("DD_APP_KEY=your_datadog_app_key_here\n")
            f.write("DD_SITE=api.datadoghq.com\n")
        print("📝 Please edit .env file with your API keys!")
        return False
    return True

def main():
    """Main startup function"""
    print("🚀 YODA Galactic Command Center Startup")
    print("🌟 May the Force be with your Infrastructure!")
    print("="*50)
    
    # Check environment file
    if not check_env_file():
        print("\n⚠️ Please configure your .env file with API keys before continuing.")
        input("Press Enter to continue anyway...")
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Failed to install requirements. Please install manually:")
        print("   pip install -r requirements_ui.txt")
        input("Press Enter to continue anyway...")
    
    print("\n🌌 Launching YODA UI...")
    print("🔗 The UI will be available at: http://localhost:7860")
    print("✨ Opening your Star Wars command center...")
    
    # Import and launch the UI
    try:
        from yoda_ui import create_yoda_ui
        ui = create_yoda_ui()
        ui.launch(
            server_name="0.0.0.0",
            server_port=None,  # Let Gradio find an available port
            share=False,
            show_error=True,
            debug=False,
            inbrowser=True  # Automatically open browser
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all files are in the same directory")
    except Exception as e:
        print(f"❌ Error launching UI: {e}")

if __name__ == "__main__":
    main() 