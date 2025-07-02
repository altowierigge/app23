"""
Command-line interface for the AI Orchestration System.
"""

import asyncio
import click
import json
import sys
from pathlib import Path
from typing import Optional

from .core.orchestrator import AIOrchestrator
from .core.config import get_config, reload_config
from .utils.logging_config import setup_logging, get_logger, get_metrics_collector
from .utils.file_manager import FileOutputManager
from .utils.git_integration import ProjectPublisher


@click.group()
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--debug', '-d', is_flag=True, help='Enable debug logging')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, debug, verbose):
    """AI Orchestration System - Multi-agent workflow for software development."""
    
    # Setup logging first
    setup_logging()
    
    # Store context
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    
    if config:
        # Load custom config if provided
        reload_config()
    
    logger = get_logger("cli")
    logger.info("AI Orchestration System CLI started")


@cli.command()
@click.argument('request', required=True)
@click.option('--output', '-o', help='Output directory for generated project')
@click.option('--workflow', '-w', help='Path to workflow YAML file')
@click.option('--no-git', is_flag=True, help='Disable Git initialization')
@click.option('--no-github', is_flag=True, help='Disable GitHub push')
@click.option('--wait', is_flag=True, help='Wait for completion and show results')
@click.pass_context
def generate(ctx, request, output, workflow, no_git, no_github, wait):
    """Generate a project using multi-agent orchestration."""
    
    logger = get_logger("cli.generate")
    config = get_config()
    
    click.echo("🤖 Starting AI Orchestration System...")
    click.echo(f"📝 Request: {request}")
    
    async def run_generation():
        try:
            # Initialize orchestrator
            orchestrator = AIOrchestrator()
            
            # Start workflow
            session_id = await orchestrator.start_workflow(request)
            click.echo(f"🆔 Session ID: {session_id}")
            
            if wait:
                # Wait for completion and monitor progress
                await monitor_workflow(orchestrator, session_id)
                
                # Get final results
                workflow_state = orchestrator.active_sessions.get(session_id)
                if workflow_state:
                    await generate_output(workflow_state, output, no_git, no_github)
                else:
                    click.echo("❌ Workflow state not found")
            else:
                click.echo(f"🚀 Workflow started in background. Session ID: {session_id}")
                click.echo("Use 'ai-orchestrator status <session_id>' to check progress.")
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            click.echo(f"❌ Error: {str(e)}", err=True)
            sys.exit(1)
    
    # Run the async function
    asyncio.run(run_generation())


@cli.command()
@click.argument('session_id', required=True)
@click.pass_context
def status(ctx, session_id):
    """Check the status of a workflow session."""
    
    async def check_status():
        try:
            orchestrator = AIOrchestrator()
            status_info = await orchestrator.get_workflow_status(session_id)
            
            if 'error' in status_info:
                click.echo(f"❌ {status_info['error']}")
                return
            
            click.echo(f"📊 Workflow Status for {session_id}")
            click.echo(f"Phase: {status_info['current_phase']}")
            click.echo(f"Progress: {status_info['progress']:.1f}%")
            click.echo(f"Runtime: {status_info['execution_time']:.1f}s")
            click.echo(f"Errors: {status_info['error_count']}")
            
        except Exception as e:
            click.echo(f"❌ Error checking status: {str(e)}", err=True)
    
    asyncio.run(check_status())


@cli.command()
@click.pass_context
def metrics(ctx):
    """Show system metrics and performance data."""
    
    metrics_collector = get_metrics_collector()
    summary = metrics_collector.get_summary()
    
    click.echo("📈 System Metrics")
    click.echo(f"Total Runtime: {summary['total_runtime']:.2f}s")
    click.echo(f"Total Metrics: {summary['total_metrics']}")
    click.echo()
    
    if summary['aggregated_metrics']:
        click.echo("Key Metrics:")
        for name, data in summary['aggregated_metrics'].items():
            if data['count'] > 0:
                click.echo(f"  {name}: {data['average']:.3f} avg ({data['count']} samples)")


@cli.command()
@click.option('--check-apis', is_flag=True, help='Check API connectivity')
@click.option('--check-git', is_flag=True, help='Check Git configuration')
@click.option('--check-github', is_flag=True, help='Check GitHub integration')
@click.pass_context
def doctor(ctx, check_apis, check_git, check_github):
    """Diagnose system configuration and connectivity."""
    
    async def run_diagnostics():
        click.echo("🔍 Running System Diagnostics...")
        
        config = get_config()
        issues = []
        
        # Check configuration
        click.echo("\n📋 Configuration Check:")
        
        # API Keys
        if not config.openai.api_key:
            issues.append("Missing OpenAI API key")
            click.echo("❌ OpenAI API key not configured")
        else:
            click.echo("✅ OpenAI API key configured")
        
        if not config.anthropic.api_key:
            issues.append("Missing Anthropic API key")
            click.echo("❌ Anthropic API key not configured")
        else:
            click.echo("✅ Anthropic API key configured")
        
        if not config.google.api_key:
            issues.append("Missing Google API key")
            click.echo("❌ Google API key not configured")
        else:
            click.echo("✅ Google API key configured")
        
        # API Connectivity
        if check_apis:
            click.echo("\n🌐 API Connectivity Check:")
            # This would test actual API connections
            click.echo("⏳ API connectivity tests not implemented yet")
        
        # Git Configuration
        if check_git:
            click.echo("\n📚 Git Configuration Check:")
            try:
                import git
                click.echo("✅ GitPython available")
                
                # Check Git configuration
                import subprocess
                result = subprocess.run(['git', '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    click.echo(f"✅ Git installed: {result.stdout.strip()}")
                else:
                    issues.append("Git not installed")
                    click.echo("❌ Git not installed")
                    
            except ImportError:
                issues.append("GitPython not installed")
                click.echo("❌ GitPython not available")
        
        # GitHub Integration
        if check_github:
            click.echo("\n🐙 GitHub Integration Check:")
            if config.git.github_token:
                click.echo("✅ GitHub token configured")
                
                try:
                    from github import Github
                    client = Github(config.git.github_token)
                    user = client.get_user()
                    click.echo(f"✅ GitHub authentication successful: {user.login}")
                except Exception as e:
                    issues.append(f"GitHub authentication failed: {str(e)}")
                    click.echo(f"❌ GitHub authentication failed: {str(e)}")
            else:
                click.echo("⚠️  GitHub token not configured (optional)")
        
        # Summary
        click.echo(f"\n📊 Diagnostic Summary:")
        if issues:
            click.echo(f"❌ {len(issues)} issues found:")
            for issue in issues:
                click.echo(f"  • {issue}")
        else:
            click.echo("✅ All checks passed!")
    
    asyncio.run(run_diagnostics())


@cli.command()
@click.option('--port', '-p', default=8000, help='Port to run on')
@click.option('--host', '-h', default='localhost', help='Host to bind to')
@click.pass_context
def serve(ctx, port, host):
    """Start the AI orchestrator as a web service."""
    
    click.echo(f"🚀 Starting AI Orchestrator web service on {host}:{port}")
    
    try:
        from .web.app import create_app
        app = create_app()
        
        import uvicorn
        uvicorn.run(app, host=host, port=port)
        
    except ImportError:
        click.echo("❌ Web service dependencies not installed", err=True)
        click.echo("Install with: pip install 'ai-orchestrator[web]'", err=True)
        sys.exit(1)


async def monitor_workflow(orchestrator, session_id):
    """Monitor workflow progress with real-time updates."""
    
    import time
    
    click.echo("\n📊 Monitoring workflow progress...")
    
    last_phase = None
    start_time = time.time()
    
    while True:
        try:
            status = await orchestrator.get_workflow_status(session_id)
            
            if 'error' in status:
                click.echo(f"❌ {status['error']}")
                break
            
            current_phase = status['current_phase']
            progress = status['progress']
            
            # Show phase changes
            if current_phase != last_phase:
                click.echo(f"🔄 {current_phase.replace('_', ' ').title()}")
                last_phase = current_phase
            
            # Show progress bar
            bar_length = 30
            filled = int(progress / 100 * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            click.echo(f"\r⏳ [{bar}] {progress:.1f}%", nl=False)
            
            # Check if completed
            if current_phase in ['completed', 'failed']:
                click.echo()  # New line
                if current_phase == 'completed':
                    click.echo("✅ Workflow completed successfully!")
                else:
                    click.echo("❌ Workflow failed!")
                break
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except KeyboardInterrupt:
            click.echo("\n⏸️  Monitoring stopped (workflow continues in background)")
            break
        except Exception as e:
            click.echo(f"\n❌ Monitoring error: {str(e)}")
            break


async def generate_output(workflow_state, output_dir, no_git, no_github):
    """Generate and save the project output."""
    
    click.echo("\n📁 Generating project files...")
    
    try:
        # Create project structure
        file_manager = FileOutputManager()
        project = file_manager.create_project_structure(workflow_state.__dict__)
        
        # Write to disk
        if not output_dir:
            output_dir = f"./output/{project.name}"
        
        project_path = file_manager.write_project_to_disk(project, output_dir)
        click.echo(f"📂 Project saved to: {project_path}")
        
        # Git and GitHub integration
        if not no_git:
            try:
                publisher = ProjectPublisher()
                publish_result = publisher.publish_project(
                    project, 
                    project_path, 
                    push_to_github=not no_github
                )
                
                if publish_result['success']:
                    if publish_result['local_repo']:
                        click.echo("📚 Git repository initialized")
                    
                    if publish_result['github_repo']:
                        click.echo(f"🐙 Published to GitHub: {publish_result['github_repo']['html_url']}")
                else:
                    click.echo("⚠️  Git/GitHub integration had issues")
                    for error in publish_result['errors']:
                        click.echo(f"   • {error}")
                        
            except Exception as e:
                click.echo(f"⚠️  Git integration failed: {str(e)}")
        
        # Show summary
        click.echo(f"\n🎉 Project generation complete!")
        click.echo(f"📊 Files generated: {len(project.files)}")
        click.echo(f"📂 Location: {project_path}")
        
    except Exception as e:
        click.echo(f"❌ Output generation failed: {str(e)}")
        raise


if __name__ == '__main__':
    cli()