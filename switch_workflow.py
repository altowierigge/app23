#!/usr/bin/env python3
"""
Workflow Switcher for AI Orchestrator
Allows switching between different workflow configurations
"""

import shutil
import os
import sys

WORKFLOWS = {
    'default': {
        'file': 'workflows/default.yaml',
        'description': 'Original workflow (has completion issues)'
    },
    'feature-based': {
        'file': 'workflows/feature-based.yaml', 
        'description': 'New feature-based workflow (fixes incomplete apps)'
    }
}

def switch_workflow(workflow_name: str):
    """Switch to a specific workflow configuration."""
    if workflow_name not in WORKFLOWS:
        print(f"❌ Unknown workflow: {workflow_name}")
        print(f"Available workflows: {', '.join(WORKFLOWS.keys())}")
        return False
    
    workflow_info = WORKFLOWS[workflow_name]
    source_file = workflow_info['file']
    target_file = 'workflows/active.yaml'
    
    if not os.path.exists(source_file):
        print(f"❌ Workflow file not found: {source_file}")
        return False
    
    try:
        # Copy the selected workflow to active.yaml
        shutil.copy2(source_file, target_file)
        print(f"✅ Switched to '{workflow_name}' workflow")
        print(f"📝 {workflow_info['description']}")
        print(f"🔄 Restart the application to use the new workflow")
        return True
    except Exception as e:
        print(f"❌ Failed to switch workflow: {str(e)}")
        return False

def list_workflows():
    """List all available workflows."""
    print("🔧 Available Workflows:")
    print("=" * 50)
    
    for name, info in WORKFLOWS.items():
        status = "✅ Available" if os.path.exists(info['file']) else "❌ Missing"
        print(f"{name:15} - {info['description']}")
        print(f"{'':15}   {status}")
        print()

def main():
    if len(sys.argv) < 2:
        print("AI Orchestrator Workflow Switcher")
        print("=" * 40)
        print()
        list_workflows()
        print("Usage:")
        print(f"  python {sys.argv[0]} <workflow_name>")
        print(f"  python {sys.argv[0]} list")
        print()
        print("Examples:")
        print(f"  python {sys.argv[0]} feature-based")
        print(f"  python {sys.argv[0]} default")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_workflows()
    elif command in WORKFLOWS:
        switch_workflow(command)
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'list' to see available workflows")

if __name__ == "__main__":
    main() 