#!/usr/bin/env python3
"""
Startup script for the AI Orchestrator Web Interface
"""

import uvicorn
from ai_orchestrator.web.app import create_app

def main():
    """Start the web application."""
    print("🚀 Starting AI Orchestrator Web Interface...")
    print("📍 URL: http://localhost:8000")
    print("⚙️  Settings: http://localhost:8000/settings")
    print("📊 Health: http://localhost:8000/api/health")
    print()
    
    # Create the app
    app = create_app()
    
    # Run the server
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000, 
            reload=False,  # Disable reload to avoid import issues
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Orchestrator Web Interface...")
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        print("💡 Make sure port 8000 is not already in use")

if __name__ == "__main__":
    main() 