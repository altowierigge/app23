"""
Command-line interface for the AI Orchestration System.
"""

import asyncio
import click
import json
import os
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
@click.option('--workflow-type', '-t', type=click.Choice(['legacy', 'micro_phase']), default='legacy', help='Workflow type to use')
@click.option('--no-git', is_flag=True, help='Disable Git initialization')
@click.option('--no-github', is_flag=True, help='Disable GitHub push')
@click.option('--wait', is_flag=True, help='Wait for completion and show results')
@click.pass_context
def generate(ctx, request, output, workflow, workflow_type, no_git, no_github, wait):
    """Generate a project using multi-agent orchestration."""
    
    logger = get_logger("cli.generate")
    config = get_config()
    
    click.echo("🤖 Starting AI Orchestration System...")
    click.echo(f"📝 Request: {request}")
    click.echo(f"🔧 Workflow Type: {workflow_type}")
    
    async def run_generation():
        try:
            # Initialize orchestrator
            orchestrator = AIOrchestrator()
            
            # Start workflow with specified type
            session_id = await orchestrator.start_workflow_with_type(request, workflow_type)
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
            status_info = await orchestrator.get_unified_workflow_status(session_id)
            
            if 'error' in status_info:
                click.echo(f"❌ {status_info['error']}")
                return
            
            workflow_type = status_info.get('workflow_type', 'unknown')
            click.echo(f"📊 Workflow Status for {session_id}")
            click.echo(f"Type: {workflow_type}")
            click.echo(f"Phase: {status_info['current_phase']}")
            
            if workflow_type == 'micro_phase':
                completed = status_info.get('completed_phases_count', 0)
                total = status_info.get('total_phases_count', 0)
                click.echo(f"Progress: {completed}/{total} micro-phases completed")
                if 'repository_url' in status_info and status_info['repository_url']:
                    click.echo(f"Repository: {status_info['repository_url']}")
            else:
                click.echo(f"Progress: {status_info.get('progress', 0):.1f}%")
                click.echo(f"Runtime: {status_info.get('execution_time', 0):.1f}s")
                click.echo(f"Errors: {status_info.get('error_count', 0)}")
            
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
        
        # Google API deprecated in v2.0
        click.echo("ℹ️ Google API deprecated in v2.0 - using OpenAI and Anthropic only")
        
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


# Cache management commands
@cli.command()
@click.argument('session_id', required=True)
@click.pass_context
def cost_analysis(ctx, session_id):
    """Get detailed cost analysis for a workflow session."""
    
    async def get_analysis():
        try:
            orchestrator = AIOrchestrator()
            
            # Check if micro-phase coordinator is available
            if hasattr(orchestrator, 'micro_phase_coordinator'):
                analysis = await orchestrator.micro_phase_coordinator.get_cost_analysis(session_id)
                
                if 'error' in analysis:
                    click.echo(f"❌ {analysis['error']}")
                    return
                
                cost_report = analysis['cost_analysis']
                summary = cost_report['summary']
                
                click.echo(f"💰 Cost Analysis for Session: {session_id}")
                click.echo(f"📈 Cache Effectiveness: {analysis['cache_effectiveness']}")
                click.echo(f"💵 Estimated Monthly Cost: ${analysis['estimated_monthly_cost']:.2f}")
                click.echo(f"💡 Top Recommendation: {analysis['top_recommendation']}")
                
                # Show detailed recommendations
                recommendations = cost_report.get('optimization_recommendations', [])
                if recommendations:
                    click.echo("\n🎯 Optimization Recommendations:")
                    for i, rec in enumerate(recommendations[:3], 1):
                        click.echo(f"   {i}. {rec['description']}")
                        click.echo(f"      Potential Savings: ${rec['potential_savings_usd']:.2f}")
                        click.echo(f"      Effort: {rec['implementation_effort']} | Risk: {rec['risk_level']}\n")
            else:
                click.echo("❌ Cost analysis only available for micro-phase workflows")
                
        except Exception as e:
            click.echo(f"❌ Error getting cost analysis: {str(e)}", err=True)
    
    asyncio.run(get_analysis())


@cli.command()
@click.argument('cache_key', required=True)
@click.option('--confirm', is_flag=True, help='Confirm cache invalidation')
@click.pass_context
def invalidate_cache(ctx, cache_key, confirm):
    """Invalidate specific cache entries."""
    
    if not confirm:
        click.echo("⚠️  Cache invalidation requires --confirm flag")
        click.echo(f"   This will remove cached data for: {cache_key}")
        click.echo("   Add --confirm to proceed")
        return
    
    async def invalidate():
        try:
            orchestrator = AIOrchestrator()
            
            if hasattr(orchestrator, 'micro_phase_coordinator'):
                result = await orchestrator.micro_phase_coordinator.invalidate_cache(cache_key)
                
                click.echo(f"✅ {result['message']}")
                if result['invalidated_keys']:
                    click.echo("   Invalidated keys:")
                    for key in result['invalidated_keys']:
                        click.echo(f"   - {key}")
            else:
                click.echo("❌ Cache invalidation only available for micro-phase workflows")
                
        except Exception as e:
            click.echo(f"❌ Error invalidating cache: {str(e)}", err=True)
    
    asyncio.run(invalidate())


@cli.command()
@click.option('--days', default=7, help='Number of days to analyze (default: 7)')
@click.pass_context
def cache_stats(ctx, days):
    """Show comprehensive cache statistics and performance metrics."""
    
    async def show_stats():
        try:
            click.echo(f"📊 Cache Statistics (Last {days} days)")
            click.echo("\n💾 Cache Performance:")
            click.echo("   Total Entries: N/A (Implementation requires active session)")
            click.echo("   Hit Rate: N/A")
            click.echo("   Total Size: N/A")
            click.echo("   Cost Savings: N/A")
            click.echo("\n⚠️  Full cache statistics require active workflow session")
            click.echo("   Use 'status --include-cache <session_id>' for active sessions")
            click.echo("   Use 'cost-analysis <session_id>' for detailed cost information")
                
        except Exception as e:
            click.echo(f"❌ Error getting cache statistics: {str(e)}", err=True)
    
    asyncio.run(show_stats())


# Cache management group
@cli.group()
def cache():
    """Cache management commands."""
    pass


@cache.command('clear')
@click.option('--confirm', is_flag=True, help='Confirm cache clearing')
def clear_cache(confirm):
    """Clear all cached data."""
    if not confirm:
        click.echo("⚠️  This will remove ALL cached data")
        click.echo("   Add --confirm to proceed")
        return
    
    try:
        import shutil
        cache_path = "/tmp/ai_orchestrator_cache"
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)
            click.echo("🗑️  Cache cleared successfully")
        else:
            click.echo("ℹ️  No cache directory found")
    except Exception as e:
        click.echo(f"❌ Error clearing cache: {str(e)}")


@cache.command('info')
def cache_info():
    """Show cache configuration and location."""
    click.echo("📁 Cache Configuration:")
    click.echo("   Location: /tmp/ai_orchestrator_cache")
    click.echo("   Max Size: 10 GB")
    click.echo("   Default Expiry: 72 hours") 
    click.echo("   Compression: Enabled")
    click.echo("   Analytics: Enabled")
    
    # Check if cache exists
    cache_path = "/tmp/ai_orchestrator_cache"
    if os.path.exists(cache_path):
        try:
            import shutil
            size = shutil.disk_usage(cache_path).used
            size_mb = size / (1024 * 1024)
            click.echo(f"   Current Size: {size_mb:.2f} MB")
        except:
            click.echo("   Current Size: Unknown")
    else:
        click.echo("   Current Size: 0 MB (no cache)")


# Update the status command to include cache information
@cli.command()
@click.argument('session_id', required=True) 
@click.option('--include-cache', is_flag=True, help='Include cache statistics in status')
@click.pass_context
def status_with_cache(ctx, session_id, include_cache):
    """Check the status of a workflow session with optional cache stats."""
    
    async def check_status():
        try:
            orchestrator = AIOrchestrator()
            status_info = await orchestrator.get_unified_workflow_status(session_id)
            
            if 'error' in status_info:
                click.echo(f"❌ {status_info['error']}")
                return
            
            workflow_type = status_info.get('workflow_type', 'unknown')
            click.echo(f"📊 Workflow Status for {session_id}")
            click.echo(f"Type: {workflow_type}")
            click.echo(f"Phase: {status_info['current_phase']}")
            
            if workflow_type == 'micro_phase':
                completed = status_info.get('completed_phases_count', 0)
                total = status_info.get('total_phases_count', 0)
                click.echo(f"Progress: {completed}/{total} micro-phases completed")
                if 'repository_url' in status_info and status_info['repository_url']:
                    click.echo(f"Repository: {status_info['repository_url']}")
                    
                # Show cache statistics if available and requested
                if include_cache and 'cache_stats' in status_info:
                    cache_stats = status_info['cache_stats']
                    click.echo("\n💾 Cache Performance:")
                    click.echo(f"   Hit Rate: {cache_stats.get('hit_rate', 'N/A')}")
                    click.echo(f"   Cost Savings: {cache_stats.get('cost_savings_usd', 'N/A')}")
                    click.echo(f"   API Calls Saved: {cache_stats.get('api_calls_saved', 'N/A')}")
            else:
                click.echo(f"Progress: {status_info.get('progress', 0):.1f}%")
                click.echo(f"Runtime: {status_info.get('execution_time', 0):.1f}s")
                click.echo(f"Errors: {status_info.get('error_count', 0)}")
            
        except Exception as e:
            click.echo(f"❌ Error checking status: {str(e)}", err=True)
    
    asyncio.run(check_status())


if __name__ == '__main__':
    cli()