"""
FastAPI web application for AI Orchestration System dashboard.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
from pathlib import Path

from ..core.orchestrator import AIOrchestrator
from ..core.config import get_config, reload_config
from ..utils.logging_config import setup_logging, get_logger, get_metrics_collector, get_performance_monitor
from ..utils.validation import SystemHealthChecker, APIKeyValidator
from ..utils.file_manager import FileOutputManager
from ..utils.env_manager import update_api_keys, validate_api_key
from ..utils.process_monitor import get_process_monitor, MessageType
# from ..core.code_generator import get_code_generator  # Temporarily disabled


# Pydantic models for API requests/responses
class ProjectRequest(BaseModel):
    """Request model for creating a new project."""
    description: str
    output_directory: Optional[str] = None
    enable_git: bool = True
    enable_github: bool = False


class ProjectResponse(BaseModel):
    """Response model for project creation."""
    session_id: str
    status: str
    message: str


class WorkflowStatus(BaseModel):
    """Model for workflow status."""
    session_id: str
    current_phase: str
    progress: float
    execution_time: float
    error_count: int
    created_at: float


class HealthStatus(BaseModel):
    """Model for system health status."""
    overall_status: str
    checks: Dict[str, Any]
    errors: List[str]
    warnings: List[str]


class ApiKeysRequest(BaseModel):
    """Request model for updating API keys."""
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    google_key: Optional[str] = None


class ApiKeysResponse(BaseModel):
    """Response model for API keys update."""
    status: str
    message: str
    updated_keys: List[str]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Setup logging
    setup_logging()
    logger = get_logger("web_app")
    
    # Create FastAPI app
    app = FastAPI(
        title="AI Orchestration System",
        description="Multi-agent workflow system for AI-powered software development",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # Setup static files and templates
    web_dir = Path(__file__).parent
    app.mount("/static", StaticFiles(directory=str(web_dir / "static")), name="static")
    templates = Jinja2Templates(directory=str(web_dir / "templates"))
    
    # Global instances
    orchestrator = None
    health_checker = SystemHealthChecker()
    api_validator = APIKeyValidator()
    file_manager = FileOutputManager()
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize the application on startup."""
        nonlocal orchestrator
        try:
            orchestrator = AIOrchestrator()
            logger.info("AI Orchestration System web interface started")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up on shutdown."""
        if orchestrator:
            await orchestrator.cleanup()
        logger.info("AI Orchestration System web interface stopped")
    
    # Web UI Routes
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Main dashboard page."""
        config = get_config()
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "title": "AI Orchestration Dashboard",
            "environment": config.environment
        })
    
    @app.get("/projects", response_class=HTMLResponse)
    async def projects_page(request: Request):
        """Projects management page."""
        return templates.TemplateResponse("projects.html", {
            "request": request,
            "title": "Projects"
        })
    
    @app.get("/monitoring", response_class=HTMLResponse)
    async def monitoring_page(request: Request):
        """System monitoring page."""
        return templates.TemplateResponse("monitoring.html", {
            "request": request,
            "title": "System Monitoring"
        })
    
    @app.get("/process-monitor/{session_id}", response_class=HTMLResponse)
    async def process_monitor_page(request: Request, session_id: str):
        """Real-time process monitoring page for a specific session."""
        return templates.TemplateResponse("process_monitor.html", {
            "request": request,
            "title": f"Process Monitor - {session_id}",
            "session_id": session_id
        })
    
    @app.get("/universal-generator", response_class=HTMLResponse)
    async def adaptive_generator_page(request: Request):
        """Adaptive Project Generator page."""
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "title": "Adaptive Project Generator"
        })
    
    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request):
        """System settings page."""
        config = get_config()
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "title": "Settings",
            "config": config
        })
    
    # API Routes
    @app.post("/api/projects", response_model=ProjectResponse)
    async def create_project(project: ProjectRequest, background_tasks: BackgroundTasks):
        """Create a new AI-generated project."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        try:
            # Start workflow using micro-phase system (working version from July 2nd)
            session_id = await orchestrator.start_micro_phase_workflow(project.description)
            
            logger.info(f"Started new project: {session_id}")
            
            return ProjectResponse(
                session_id=session_id,
                status="started",
                message=f"Project workflow started successfully. Session ID: {session_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects/{session_id}/status", response_model=WorkflowStatus)
    async def get_project_status(session_id: str):
        """Get the status of a specific project workflow."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        try:
            status_info = await orchestrator.get_workflow_status(session_id)
            
            if 'error' in status_info:
                raise HTTPException(status_code=404, detail=status_info['error'])
            
            return WorkflowStatus(**status_info)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get project status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects")
    async def list_projects():
        """List all active projects."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        try:
            active_sessions = []
            for session_id, state in orchestrator.active_sessions.items():
                status_info = await orchestrator.get_workflow_status(session_id)
                active_sessions.append({
                    "session_id": session_id,
                    "user_request": state.user_request[:100] + "..." if len(state.user_request) > 100 else state.user_request,
                    "current_phase": status_info.get('current_phase', 'unknown'),
                    "progress": status_info.get('progress', 0),
                    "created_at": state.created_at
                })
            
            return {"projects": active_sessions}
            
        except Exception as e:
            logger.error(f"Failed to list projects: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects/{session_id}/download")
    async def download_project(session_id: str):
        """Generate and download project files."""
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not available")
        
        try:
            # Check if session exists and is completed
            if session_id not in orchestrator.active_sessions:
                raise HTTPException(status_code=404, detail="Project session not found")
            
            workflow_state = orchestrator.active_sessions[session_id]
            status_info = await orchestrator.get_workflow_status(session_id)
            
            if status_info['current_phase'] != 'completed':
                raise HTTPException(status_code=400, detail=f"Project not completed yet. Current phase: {status_info['current_phase']}")
            
            # Get session results
            session_results = await orchestrator.get_session_results(session_id)
            if 'error' in session_results:
                raise HTTPException(status_code=400, detail=session_results['error'])
            
            # Create project structure and write to disk
            workflow_state_dict = {
                'session_id': session_id,
                'refined_requirements': workflow_state.refined_requirements,
                'gpt_brainstorm': workflow_state.gpt_brainstorm,
                'claude_brainstorm': workflow_state.claude_brainstorm,
                'final_strategy': workflow_state.final_strategy,
                'claude_plan': workflow_state.claude_plan,
                'improved_backend_implementation': workflow_state.improved_backend_implementation,
                'improved_frontend_implementation': workflow_state.improved_frontend_implementation,
                'backend_implementation': workflow_state.backend_implementation,
                'frontend_implementation': workflow_state.frontend_implementation,
                'test_implementation': workflow_state.test_implementation,
                'code_review_feedback': workflow_state.code_review_feedback,
                'final_documentation': workflow_state.final_documentation,
                'quality_report': workflow_state.quality_report
            }
            
            # Generate project structure
            project_structure = file_manager.create_project_structure(workflow_state_dict)
            
            # Write files to disk
            output_path = file_manager.write_project_to_disk(project_structure)
            
            logger.info(f"Project files generated successfully: {output_path}")
            
            return {
                "status": "success",
                "message": "Project files generated successfully",
                "output_path": output_path,
                "project_name": project_structure.name,
                "file_count": len(project_structure.files),
                "session_id": session_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate project files: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate project files: {str(e)}")
    
    @app.post("/api/projects/{session_id}/generate")
    async def generate_project_files(session_id: str):
        """Generate project files for a completed workflow."""
        # Same logic as download but as POST endpoint
        return await download_project(session_id)
    
    @app.get("/api/health", response_model=HealthStatus)
    async def health_check():
        """Get system health status."""
        try:
            health_report = await health_checker.check_system_health()
            return HealthStatus(**health_report)
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/metrics")
    async def get_metrics():
        """Get system metrics."""
        try:
            metrics_collector = get_metrics_collector()
            performance_monitor = get_performance_monitor()
            
            metrics_summary = metrics_collector.get_summary()
            health_status = performance_monitor.get_health_status()
            
            return {
                "metrics": metrics_summary,
                "health": health_status,
                "timestamp": metrics_summary.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/validate-keys")
    async def validate_api_keys():
        """Validate all configured API keys."""
        try:
            validation_results = await api_validator.validate_all_api_keys()
            
            return {
                "results": validation_results,
                "all_valid": all(validation_results.values()),
                "total_keys": len(validation_results),
                "valid_keys": sum(validation_results.values())
            }
            
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/config")
    async def get_configuration():
        """Get current system configuration (sanitized)."""
        try:
            config = get_config()
            
            # Return sanitized configuration (no API keys)
            sanitized_config = {
                "environment": config.environment,
                "debug": config.debug,
                "log_level": config.log_level.value,
                "output_dir": config.output_dir,
                "enable_voting": config.enable_voting,
                "require_consensus": config.require_consensus,
                "allow_tie_breaking": config.allow_tie_breaking,
                "max_concurrent_agents": config.max_concurrent_agents,
                "git_enabled": config.git.enabled,
                "git_auto_commit": config.git.auto_commit,
                "git_auto_push": config.git.auto_push
            }
            
            return {"config": sanitized_config}
            
        except Exception as e:
            logger.error(f"Failed to get configuration: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/settings/apikeys", response_model=ApiKeysResponse)
    async def update_api_keys_endpoint(request: ApiKeysRequest):
        """Update API keys configuration."""
        try:
            # Convert request to dictionary and filter out None values
            api_keys = {}
            updated_keys = []
            
            if request.openai_key:
                # Accept any non-empty API key (relaxed validation)
                if request.openai_key.strip():
                    api_keys['openai_key'] = request.openai_key.strip()
                    updated_keys.append('OpenAI')
                else:
                    raise HTTPException(status_code=400, detail="OpenAI API key cannot be empty")
            
            if request.anthropic_key:
                # Accept any non-empty API key (relaxed validation)
                if request.anthropic_key.strip():
                    api_keys['anthropic_key'] = request.anthropic_key.strip()
                    updated_keys.append('Anthropic')
                else:
                    raise HTTPException(status_code=400, detail="Anthropic API key cannot be empty")
            
            if request.google_key:
                # Accept any non-empty API key (relaxed validation)
                if request.google_key.strip():
                    api_keys['google_key'] = request.google_key.strip()
                    updated_keys.append('Google')
                else:
                    raise HTTPException(status_code=400, detail="Google API key cannot be empty")
            
            if not api_keys:
                raise HTTPException(status_code=400, detail="No valid API keys provided")
            
            # Update the .env file
            success, message = update_api_keys(api_keys)
            
            if not success:
                raise HTTPException(status_code=500, detail=message)
            
            # Reload configuration to pick up new keys
            try:
                reload_config()
                logger.info("Configuration reloaded after API key update")
            except Exception as e:
                logger.warning(f"Failed to reload configuration: {str(e)}")
            
            # Reinitialize orchestrator with new keys
            nonlocal orchestrator
            try:
                if orchestrator:
                    await orchestrator.cleanup()
                orchestrator = AIOrchestrator()
                logger.info("Orchestrator reinitialized with new API keys")
            except Exception as e:
                logger.error(f"Failed to reinitialize orchestrator: {str(e)}")
                # Continue anyway - the keys are saved
            
            logger.info(f"Successfully updated API keys: {', '.join(updated_keys)}")
            
            return ApiKeysResponse(
                status="success",
                message=f"Successfully updated {len(updated_keys)} API key(s)",
                updated_keys=updated_keys
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update API keys: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    
    @app.post("/api/settings/github")
    async def save_github_settings(request: Request):
        """Save GitHub integration settings."""
        try:
            data = await request.json()
            token = data.get('token', '').strip()
            
            if not token:
                raise HTTPException(status_code=400, detail="GitHub token is required")
            
            # Test the token by getting user info
            from ..utils.github_integration import GitHubIntegration
            try:
                github = GitHubIntegration(token=token)
                user_info = github._get_authenticated_user()
                
                # Save settings to environment
                from ..utils.env_manager import save_github_settings_to_env
                env_data = {
                    'GITHUB_TOKEN': token,
                    'GIT_ENABLED': 'true',
                    'GIT_AUTO_COMMIT': str(data.get('auto_commit', True)).lower(),
                    'GIT_AUTO_PUSH': str(data.get('create_pr', False)).lower()
                }
                save_github_settings_to_env(env_data)
                
                # Update config
                config = get_config()
                config.git.github_token = token
                config.git.enabled = True
                config.git.auto_commit = data.get('auto_commit', True)
                config.git.auto_push = data.get('create_pr', False)
                
                return {
                    "status": "success",
                    "message": "GitHub connected successfully",
                    "user": {
                        "login": user_info.get('login'),
                        "email": user_info.get('email'),
                        "avatar_url": user_info.get('avatar_url')
                    }
                }
            except Exception as e:
                logger.error(f"GitHub authentication failed: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid GitHub token")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving GitHub settings: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/settings/github/status")
    async def get_github_status():
        """Get GitHub connection status."""
        try:
            config = get_config()
            
            if not config.git.enabled or not config.git.github_token:
                return {"connected": False}
            
            # Try to get user info
            from ..utils.github_integration import GitHubIntegration
            try:
                github = GitHubIntegration(token=config.git.github_token)
                user_info = github._get_authenticated_user()
                
                return {
                    "connected": True,
                    "user": {
                        "login": user_info.get('login'),
                        "email": user_info.get('email'),
                        "avatar_url": user_info.get('avatar_url')
                    }
                }
            except:
                return {"connected": False}
                
        except Exception as e:
            logger.error(f"Error checking GitHub status: {str(e)}")
            return {"connected": False}

    @app.get("/api/settings/github/test")
    async def test_github_connection():
        """Test GitHub connection."""
        try:
            config = get_config()
            
            if not config.git.enabled or not config.git.github_token:
                return {"connected": False, "message": "GitHub not configured"}
            
            from ..utils.github_integration import GitHubIntegration
            try:
                github = GitHubIntegration(token=config.git.github_token)
                user_info = github._get_authenticated_user()
                
                return {
                    "connected": True,
                    "username": user_info.get('login'),
                    "message": f"Connected as {user_info.get('login')}"
                }
            except Exception as e:
                return {"connected": False, "message": f"Connection failed: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error testing GitHub connection: {str(e)}")
            return {"connected": False, "message": "Internal error"}
    
    # Process Monitoring API Endpoints
    @app.get("/api/process-monitor/{session_id}/messages")
    async def get_process_messages(
        session_id: str,
        limit: Optional[int] = None,
        message_type: Optional[str] = None,
        source: Optional[str] = None,
        level: Optional[str] = None
    ):
        """Get process messages for a session with optional filtering."""
        try:
            monitor = get_process_monitor()
            
            # Convert string message_type to enum if provided
            msg_type_enum = None
            if message_type:
                try:
                    msg_type_enum = MessageType(message_type)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid message_type: {message_type}")
            
            messages = monitor.get_messages(
                session_id=session_id,
                limit=limit,
                message_type=msg_type_enum,
                source=source,
                level=level
            )
            
            return {"messages": messages}
            
        except Exception as e:
            logger.error(f"Error getting process messages: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/process-monitor/{session_id}/stats")
    async def get_process_stats(session_id: str):
        """Get process statistics for a session."""
        try:
            monitor = get_process_monitor()
            stats = monitor.get_session_stats(session_id)
            return {"stats": stats}
            
        except Exception as e:
            logger.error(f"Error getting process stats: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/process-monitor/sessions")
    async def get_monitored_sessions():
        """Get list of sessions being monitored."""
        try:
            monitor = get_process_monitor()
            sessions = monitor.get_active_sessions()
            return {"sessions": sessions}
            
        except Exception as e:
            logger.error(f"Error getting monitored sessions: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/process-monitor/{session_id}")
    async def clear_process_messages(session_id: str):
        """Clear all messages for a session."""
        try:
            monitor = get_process_monitor()
            monitor.clear_session(session_id)
            return {"status": "success", "message": "Session messages cleared"}
            
        except Exception as e:
            logger.error(f"Error clearing process messages: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Universal Project Generator API Endpoints
    @app.post("/api/universal-generator/analyze")
    async def analyze_project_idea(request: dict):
        """Analyze project idea and generate complete specification."""
        try:
            user_idea = request.get("idea", "")
            if not user_idea:
                raise HTTPException(status_code=400, detail="Project idea is required")
            
            # Generate session ID
            import uuid
            session_id = str(uuid.uuid4())
            
            # Use micro-phase workflow system (working version from July 2nd)
            session_id = await orchestrator.start_micro_phase_workflow(user_idea)
            
            return {
                "session_id": session_id,
                "analysis": {"user_request": user_idea, "workflow_type": "micro_phase"},
                "status": "started"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing project idea: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/universal-generator/generate")
    async def generate_complete_project(request: dict):
        """Generate complete working project from specification."""
        try:
            project_spec = request.get("project_spec")
            if not project_spec:
                raise HTTPException(status_code=400, detail="Project specification is required")
            
            session_id = request.get("session_id", str(uuid.uuid4()))
            
            # Create unique output directory
            import time
            timestamp = int(time.time())
            output_dir = f"./output/ai-generated-{timestamp}"
            
            code_generator = get_code_generator()
            result = await code_generator.generate_complete_project(
                project_spec=project_spec,
                session_id=session_id,
                output_path=output_dir
            )
            
            return {
                "status": "success",
                "message": "Complete project generated successfully!",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error generating project: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/universal-generator/quick-build")
    async def quick_build_project(request: dict):
        """Quick build: Analyze idea and generate complete project in one step."""
        try:
            user_idea = request.get("idea", "")
            if not user_idea:
                raise HTTPException(status_code=400, detail="Project idea is required")
            
            # Generate session ID
            import uuid, time
            session_id = str(uuid.uuid4())
            timestamp = int(time.time())
            
            logger.info(f"Starting adaptive project build for: {user_idea[:100]}...")
            
            # Use micro-phase workflow system to generate the complete project (working version from July 2nd)
            session_id = await orchestrator.start_micro_phase_workflow(user_idea)
            
            return {
                "status": "success", 
                "message": "Micro-phase project workflow started successfully!",
                "session_id": session_id,
                "analysis": {"user_request": user_idea, "workflow_type": "micro_phase"},
                "monitor_url": f"/process-monitor/{session_id}",
                "info": "Project will be built using the adaptive workflow system. Monitor progress at the provided URL."
            }
            
        except Exception as e:
            logger.error(f"Error in quick build: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # WebSocket endpoints for real-time updates
    @app.websocket("/ws/projects/{session_id}")
    async def websocket_project_updates(websocket: WebSocket, session_id: str):
        """WebSocket endpoint for real-time project updates."""
        await websocket.accept()
        
        try:
            while True:
                if orchestrator and session_id in orchestrator.active_sessions:
                    status_info = await orchestrator.get_workflow_status(session_id)
                    await websocket.send_json(status_info)
                else:
                    await websocket.send_json({"error": "Session not found"})
                    break
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            await websocket.close()
    
    @app.websocket("/ws/process-monitor/{session_id}")
    async def websocket_process_monitor(websocket: WebSocket, session_id: str):
        """WebSocket endpoint for real-time process monitoring."""
        await websocket.accept()
        monitor = get_process_monitor()
        
        # Send current messages first
        try:
            messages = monitor.get_messages(session_id, limit=50)
            await websocket.send_json({
                "type": "initial_messages",
                "messages": messages
            })
        except Exception as e:
            logger.error(f"Error sending initial messages: {str(e)}")
        
        # Subscribe to new messages
        async def message_callback(message_data):
            try:
                await websocket.send_json({
                    "type": "new_message",
                    "message": message_data
                })
            except Exception as e:
                logger.error(f"Error sending message via WebSocket: {str(e)}")
        
        monitor.subscribe(session_id, message_callback)
        
        try:
            # Keep connection alive and handle client messages
            while True:
                try:
                    data = await websocket.receive_json()
                    
                    # Handle client commands
                    if data.get("command") == "get_stats":
                        stats = monitor.get_session_stats(session_id)
                        await websocket.send_json({
                            "type": "stats_update",
                            "stats": stats
                        })
                    elif data.get("command") == "get_messages":
                        filters = data.get("filters", {})
                        messages = monitor.get_messages(
                            session_id=session_id,
                            limit=filters.get("limit"),
                            message_type=MessageType(filters["message_type"]) if filters.get("message_type") else None,
                            source=filters.get("source"),
                            level=filters.get("level")
                        )
                        await websocket.send_json({
                            "type": "filtered_messages",
                            "messages": messages
                        })
                        
                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send_json({"type": "heartbeat"})
                
        except WebSocketDisconnect:
            logger.info(f"Process monitor WebSocket disconnected for session {session_id}")
        except Exception as e:
            logger.error(f"Process monitor WebSocket error: {str(e)}")
        finally:
            monitor.unsubscribe(session_id, message_callback)
    
    # Error handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        """Handle 404 errors."""
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={"detail": "API endpoint not found"}
            )
        return templates.TemplateResponse("404.html", {
            "request": request,
            "title": "Page Not Found"
        }, status_code=404)
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {str(exc)}")
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        return templates.TemplateResponse("500.html", {
            "request": request,
            "title": "Server Error"
        }, status_code=500)
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)