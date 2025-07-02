#!/usr/bin/env python3
"""
Main entry point for the AI Orchestration System.

This module provides multiple ways to run the system:
1. Command-line interface
2. Python API
3. Web service
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ai_orchestrator import AIOrchestrator, setup_logging, get_logger
from ai_orchestrator.cli import cli


async def example_usage():
    """Example of using the AI orchestrator programmatically."""
    
    # Setup logging
    setup_logging()
    logger = get_logger("example")
    
    logger.info("Starting AI Orchestration System example")
    
    try:
        # Initialize the orchestrator
        orchestrator = AIOrchestrator()
        
        # Example project request
        user_request = """
        Create a simple todo application with the following features:
        - User authentication (login/register)
        - Create, read, update, delete todo items
        - Mark todos as complete/incomplete
        - Filter todos by status
        - Responsive web interface
        - RESTful API backend
        """
        
        print("🤖 Starting AI multi-agent workflow...")
        print(f"📝 Request: {user_request}")
        
        # Start the workflow
        session_id = await orchestrator.start_workflow(user_request)
        print(f"🆔 Session ID: {session_id}")
        
        # Monitor progress (in a real application, this would be done differently)
        print("⏳ Workflow started. Check logs for progress...")
        print(f"💡 Use 'python main.py status {session_id}' to check status")
        
        # Cleanup
        await orchestrator.cleanup()
        
    except Exception as e:
        logger.error(f"Example failed: {str(e)}")
        print(f"❌ Error: {str(e)}")


def main():
    """Main entry point."""
    
    if len(sys.argv) == 1:
        # No arguments - run example
        print("🚀 AI Orchestration System")
        print("Running example workflow...")
        print()
        
        asyncio.run(example_usage())
        
        print()
        print("💡 For more options, use:")
        print("   python main.py --help")
        print("   python -m ai_orchestrator.cli --help")
        
    else:
        # Run CLI
        cli()


if __name__ == "__main__":
    main()