"""
Main orchestrator for managing multi-agent AI workflows.
"""

import asyncio
import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..agents import (
    GPTAgent, ClaudeAgent, GPTManagerAgent, GPTValidatorAgent,
    GPTGitAgent, GPTIntegrationAgent,
    AgentTask, TaskType, AgentResponse, AgentRole
)
from ..core.config import get_config
from ..utils.logging_config import get_logger, get_workflow_logger
from .workflow_engine import WorkflowEngine
from .micro_phase_coordinator import MicroPhaseCoordinator
from .adaptive_workflow import AdaptiveWorkflowGenerator


class WorkflowPhase(str, Enum):
    INITIALIZATION = "initialization"
    REQUIREMENTS_REFINEMENT = "requirements_refinement"
    BRAINSTORMING_GPT = "brainstorming_gpt"
    BRAINSTORMING_CLAUDE = "brainstorming_claude"
    STRATEGY_ALIGNMENT = "strategy_alignment"
    TECHNICAL_PLANNING = "technical_planning"
    BACKEND_IMPLEMENTATION = "backend_implementation"
    FRONTEND_IMPLEMENTATION = "frontend_implementation"
    CODE_REVIEW = "code_review"
    CODE_IMPROVEMENTS = "code_improvements"
    TESTING = "testing"
    FINAL_QA = "final_qa"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowState:
    """Complete state of the workflow execution."""
    session_id: str
    current_phase: WorkflowPhase
    user_request: str
    created_at: float = field(default_factory=time.time)
    
    # Workflow data
    refined_requirements: Optional[str] = None
    gpt_brainstorm: Optional[str] = None
    claude_brainstorm: Optional[str] = None
    final_strategy: Optional[str] = None
    claude_plan: Optional[str] = None
    
    # Implementation results
    backend_implementation: Optional[str] = None
    frontend_implementation: Optional[str] = None
    improved_backend_implementation: Optional[str] = None
    improved_frontend_implementation: Optional[str] = None
    test_implementation: Optional[str] = None
    
    # Review and consultation
    code_review_feedback: Optional[str] = None
    final_documentation: Optional[str] = None
    quality_report: Optional[str] = None
    
    # Metadata
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    error_count: int = 0
    total_execution_time: float = 0


class AIOrchestrator:
    """
    Main orchestrator that manages the GPT-Claude collaborative workflow.
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("orchestrator")
        
        # Initialize legacy agents
        self.gpt_agent = GPTAgent(self.config.openai)
        self.claude_agent = ClaudeAgent(self.config.anthropic)
        
        # Initialize new specialized agents
        self.gpt_manager = GPTManagerAgent(self.config.openai)
        self.gpt_validator = GPTValidatorAgent(self.config.openai)
        self.gpt_git_agent = GPTGitAgent(self.config.openai)
        self.gpt_integration_agent = GPTIntegrationAgent(self.config.openai)
        
        # Initialize workflow engines
        self.workflow_engine = WorkflowEngine()
        self.micro_phase_coordinator = MicroPhaseCoordinator(
            self.config.openai, 
            self.config.anthropic
        )
        
        # Initialize adaptive workflow generator
        self.adaptive_workflow_generator = AdaptiveWorkflowGenerator(self.gpt_manager)
        
        # Workflow state management
        self.active_sessions: Dict[str, WorkflowState] = {}
        
        # Agent mapping for workflow engine
        self.agent_map = {
            # Legacy agents
            "gpt": self.gpt_agent,
            "claude": self.claude_agent,
            # New specialized agents
            "gpt_manager": self.gpt_manager,
            "gpt_validator": self.gpt_validator,
            "gpt_git_agent": self.gpt_git_agent,
            "gpt_integration_agent": self.gpt_integration_agent
        }
        
        self.logger.info("AI Orchestrator initialized with both legacy and micro-phase workflows")
    
    async def start_workflow(self, user_request: str) -> str:
        """
        Start a new GPT-Claude collaborative workflow.
        
        Args:
            user_request: The initial project request from the user
            
        Returns:
            session_id: Unique identifier for this workflow session
        """
        session_id = str(uuid.uuid4())
        
        workflow_state = WorkflowState(
            session_id=session_id,
            current_phase=WorkflowPhase.INITIALIZATION,
            user_request=user_request
        )
        
        self.active_sessions[session_id] = workflow_state
        
        self.logger.info(f"Started new GPT-Claude collaborative workflow session: {session_id}")
        self._log_workflow_event(workflow_state, "workflow_started", {
            "user_request_length": len(user_request),
            "workflow_type": "gpt_claude_collaborative"
        })
        
        # Start the workflow execution using workflow engine
        asyncio.create_task(self._execute_workflow_with_engine(session_id))
        
        return session_id
    
    async def create_adaptive_project(self, user_request: str) -> str:
        """
        Create ANY type of project using the adaptive workflow system.
        
        Args:
            user_request: The project request from the user
            
        Returns:
            session_id: Unique identifier for this workflow session
        """
        session_id = str(uuid.uuid4())
        
        # Create a simplified workflow state for adaptive projects
        workflow_state = WorkflowState(
            session_id=session_id,
            current_phase=WorkflowPhase.INITIALIZATION,
            user_request=user_request
        )
        
        self.active_sessions[session_id] = workflow_state
        
        self.logger.info(f"Started new adaptive project workflow session: {session_id}")
        self._log_workflow_event(workflow_state, "adaptive_workflow_started", {
            "user_request_length": len(user_request),
            "workflow_type": "adaptive"
        })
        
        # Start the adaptive workflow execution
        asyncio.create_task(self._execute_adaptive_workflow(session_id))
        
        return session_id
    
    async def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow."""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        state = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "current_phase": state.current_phase.value,
            "created_at": state.created_at,
            "execution_time": time.time() - state.created_at,
            "error_count": state.error_count,
            "progress": self._calculate_progress(state.current_phase),
            "workflow_type": "gpt_claude_collaborative"
        }
    
    async def _execute_workflow_with_engine(self, session_id: str):
        """Execute workflow using the YAML-based workflow engine."""
        state = self.active_sessions[session_id]
        workflow_logger = get_workflow_logger(session_id)
        start_time = time.time()
        
        try:
            workflow_logger.log_workflow_start(state.user_request)
            
            # Set up agent mapping for workflow engine
            self.workflow_engine.agent_map = self.agent_map
            
            # Prepare initial state for workflow engine
            initial_state = {
                'session_id': session_id,
                'user_request': state.user_request,
                'created_at': state.created_at
            }
            
            # Execute workflow using engine
            final_state = await self.workflow_engine.execute_workflow(initial_state)
            
            # Update our workflow state with results
            self._update_state_from_engine_result(state, final_state)
            
            state.current_phase = WorkflowPhase.COMPLETED
            state.total_execution_time = time.time() - start_time
            
            workflow_logger.log_workflow_complete(True)
            self.logger.info(f"GPT-Claude collaborative workflow completed successfully: {session_id}")
            
            # Auto-generate project files for successful workflows
            try:
                self._create_successful_project_structure(session_id, final_state)
            except Exception as creation_error:
                self.logger.error(f"Failed to auto-generate project files for successful workflow: {creation_error}")
            
        except Exception as e:
            state.current_phase = WorkflowPhase.FAILED
            state.error_count += 1
            workflow_logger.log_workflow_complete(False)
            self.logger.error(f"Workflow failed: {session_id} - {str(e)}")
            self._log_workflow_event(state, "workflow_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Still create basic project structure even for failed workflows
            try:
                # Prepare what we have from the engine or current state
                available_state = {
                    'session_id': session_id,
                    'user_request': state.user_request,
                    'refined_requirements': getattr(state, 'refined_requirements', None),
                    'gpt_brainstorm': getattr(state, 'gpt_brainstorm', None),
                    'claude_brainstorm': getattr(state, 'claude_brainstorm', None),
                    'final_strategy': getattr(state, 'final_strategy', None),
                    'claude_plan': getattr(state, 'claude_plan', None),
                    'backend_implementation': getattr(state, 'backend_implementation', None),
                    'frontend_implementation': getattr(state, 'frontend_implementation', None),
                    'error': str(e)
                }
                self._create_failed_project_structure(session_id, available_state)
            except Exception as creation_error:
                self.logger.error(f"Failed to create project structure for failed workflow: {creation_error}")
    
    async def _execute_adaptive_workflow(self, session_id: str):
        """Execute workflow using the adaptive workflow system."""
        state = self.active_sessions[session_id]
        workflow_logger = get_workflow_logger(session_id)
        start_time = time.time()
        
        try:
            workflow_logger.log_workflow_start(state.user_request)
            
            # Set up agent mapping for workflow engine
            self.workflow_engine.agent_map = self.agent_map
            
            # Generate adaptive workflow
            self.logger.info(f"Generating adaptive workflow for: {state.user_request[:100]}...")
            workflow = await self.adaptive_workflow_generator.generate_workflow(
                state.user_request, 
                session_id
            )
            
            self.logger.info(f"Generated {workflow.project_analysis.project_type.value} workflow with {len(workflow.phases)} phases")
            
            # Update state with project analysis
            state.current_phase = WorkflowPhase.REQUIREMENTS_REFINEMENT
            state.refined_requirements = f"Project Type: {workflow.project_analysis.project_type.value}\\n" + \
                                       f"Features: {', '.join(workflow.project_analysis.features)}\\n" + \
                                       f"Tech Stack: {workflow.project_analysis.tech_stack}\\n" + \
                                       f"Complexity: {workflow.project_analysis.estimated_complexity}"
            
            # Execute adaptive workflow
            final_state = await self.workflow_engine.execute_adaptive_workflow(workflow, session_id)
            
            # Update our workflow state with results
            self._update_state_from_adaptive_result(state, final_state, workflow)
            
            state.current_phase = WorkflowPhase.COMPLETED
            state.total_execution_time = time.time() - start_time
            
            workflow_logger.log_workflow_complete(True)
            self.logger.info(f"Adaptive workflow completed successfully: {session_id} ({workflow.project_analysis.project_type.value})")
            
            # Auto-generate project files for successful workflows
            try:
                self._create_adaptive_project_structure(session_id, final_state, workflow)
            except Exception as creation_error:
                self.logger.error(f"Failed to auto-generate adaptive project files: {creation_error}")
            
        except Exception as e:
            state.current_phase = WorkflowPhase.FAILED
            state.error_count += 1
            workflow_logger.log_workflow_complete(False)
            self.logger.error(f"Adaptive workflow failed: {session_id} - {str(e)}")
            self._log_workflow_event(state, "adaptive_workflow_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Still create basic project structure even for failed workflows
            try:
                available_state = {
                    'session_id': session_id,
                    'user_request': state.user_request,
                    'refined_requirements': getattr(state, 'refined_requirements', None),
                    'error': str(e),
                    'workflow_type': 'adaptive'
                }
                self._create_failed_project_structure(session_id, available_state)
            except Exception as creation_error:
                self.logger.error(f"Failed to create adaptive project structure for failed workflow: {creation_error}")
    
    def _update_state_from_engine_result(self, state: WorkflowState, engine_result: Dict[str, Any]):
        """Update workflow state with results from workflow engine."""
        # Requirements and strategy
        state.refined_requirements = engine_result.get('refined_requirements')
        state.gpt_brainstorm = engine_result.get('gpt_brainstorm')
        state.claude_brainstorm = engine_result.get('claude_brainstorm')
        state.final_strategy = engine_result.get('final_strategy')
        state.claude_plan = engine_result.get('claude_plan')
        
        # Implementation results
        state.backend_implementation = engine_result.get('backend_implementation')
        state.frontend_implementation = engine_result.get('frontend_implementation')
        state.improved_backend_implementation = engine_result.get('improved_backend_implementation')
        state.improved_frontend_implementation = engine_result.get('improved_frontend_implementation')
        state.test_implementation = engine_result.get('test_implementation')
        
        # Review and consultation
        state.code_review_feedback = engine_result.get('code_review_feedback')
        state.final_documentation = engine_result.get('final_documentation')
        state.quality_report = engine_result.get('quality_report')
    
    def _update_state_from_adaptive_result(self, state: WorkflowState, engine_result: Dict[str, Any], workflow):
        """Update workflow state with results from adaptive workflow."""
        from .adaptive_workflow import AdaptiveWorkflow
        
        # Store basic information
        state.refined_requirements = engine_result.get('refined_requirements', state.refined_requirements)
        
        # Store all phase results
        for phase_name in engine_result.get('completed_phases', []):
            phase_result = engine_result.get(f"{phase_name}_result")
            if phase_result:
                # Store in appropriate state field based on phase name
                if 'implementation' in phase_name:
                    if not hasattr(state, 'adaptive_implementations'):
                        state.adaptive_implementations = {}
                    state.adaptive_implementations[phase_name] = phase_result
                elif 'documentation' in phase_name:
                    state.final_documentation = phase_result
                elif 'test' in phase_name:
                    state.test_implementation = phase_result
        
        # Store project metadata
        if not hasattr(state, 'project_metadata'):
            state.project_metadata = {}
        state.project_metadata.update({
            'project_type': workflow.project_analysis.project_type.value,
            'project_name': workflow.project_analysis.project_name,
            'tech_stack': workflow.project_analysis.tech_stack,
            'features': workflow.project_analysis.features,
            'complexity': workflow.project_analysis.estimated_complexity
        })
    
    def _log_workflow_event(self, state: WorkflowState, event_type: str, data: Dict[str, Any]):
        """Log workflow events with enhanced data."""
        event = {
            "timestamp": time.time(),
            "session_id": state.session_id,
            "current_phase": state.current_phase.value,
            "event_type": event_type,
            "data": data
        }
        
        state.execution_log.append(event)
        self.logger.info(f"Workflow event: {event_type}", extra=event)
    
    def _calculate_progress(self, current_phase: WorkflowPhase) -> float:
        """Calculate workflow progress percentage based on current phase."""
        phase_weights = {
            WorkflowPhase.INITIALIZATION: 0.0,
            WorkflowPhase.REQUIREMENTS_REFINEMENT: 0.1,
            WorkflowPhase.BRAINSTORMING_GPT: 0.2,
            WorkflowPhase.BRAINSTORMING_CLAUDE: 0.25,
            WorkflowPhase.STRATEGY_ALIGNMENT: 0.3,
            WorkflowPhase.TECHNICAL_PLANNING: 0.35,
            WorkflowPhase.BACKEND_IMPLEMENTATION: 0.5,
            WorkflowPhase.FRONTEND_IMPLEMENTATION: 0.65,
            WorkflowPhase.CODE_REVIEW: 0.75,
            WorkflowPhase.CODE_IMPROVEMENTS: 0.85,
            WorkflowPhase.TESTING: 0.9,
            WorkflowPhase.FINAL_QA: 0.95,
            WorkflowPhase.COMPLETED: 1.0,
            WorkflowPhase.FAILED: 0.0
        }
        
        return phase_weights.get(current_phase, 0.0)
    
    async def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get the complete results of a completed workflow session."""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        state = self.active_sessions[session_id]
        
        if state.current_phase != WorkflowPhase.COMPLETED:
            return {"error": "Workflow not completed yet"}
        
        return {
            "session_id": session_id,
            "status": "completed",
            "execution_time": state.total_execution_time,
            "results": {
                "refined_requirements": state.refined_requirements,
                "brainstorming": {
                    "gpt_brainstorm": state.gpt_brainstorm,
                    "claude_brainstorm": state.claude_brainstorm,
                    "final_strategy": state.final_strategy
                },
                "technical_plan": state.claude_plan,
                "implementation": {
                    "backend_implementation": state.improved_backend_implementation or state.backend_implementation,
                    "frontend_implementation": state.improved_frontend_implementation or state.frontend_implementation,
                    "test_implementation": state.test_implementation
                },
                "quality_assurance": {
                    "code_review_feedback": state.code_review_feedback,
                    "final_documentation": state.final_documentation,
                    "quality_report": state.quality_report
                }
            },
            "metadata": {
                "error_count": state.error_count,
                "execution_log": state.execution_log
            }
        }
    
    def _create_failed_project_structure(self, session_id: str, final_state: Dict[str, Any]):
        """Create basic project structure even for failed workflows."""
        from ..utils.file_manager import FileOutputManager, GeneratedFile, ProjectStructure
        from datetime import datetime
        import os
        
        try:
            # Create basic project structure with whatever data we have
            file_manager = FileOutputManager()
            
            # Prepare minimal workflow state
            workflow_state = {
                'session_id': session_id,
                'user_request': final_state.get('user_request', 'Project request not available'),
                'refined_requirements': final_state.get('refined_requirements', 'Requirements not completed'),
                'gpt_brainstorm': final_state.get('gpt_brainstorm', ''),
                'claude_brainstorm': final_state.get('claude_brainstorm', ''),
                'final_strategy': final_state.get('final_strategy', ''),
                'claude_plan': final_state.get('claude_plan', ''),
                'backend_implementation': final_state.get('backend_implementation', ''),
                'frontend_implementation': final_state.get('frontend_implementation', '')
            }
            
            # Create basic files
            files = []
            
            # Extract and save any generated implementation code
            if workflow_state.get('backend_implementation'):
                backend_files = file_manager.parser.parse_backend_implementation(
                    workflow_state['backend_implementation'], session_id
                )
                files.extend(backend_files)
                self.logger.info(f"Extracted {len(backend_files)} backend files from failed workflow")
            
            if workflow_state.get('frontend_implementation'):
                frontend_files = file_manager.parser.parse_frontend_implementation(
                    workflow_state['frontend_implementation'], session_id
                )
                files.extend(frontend_files)
                self.logger.info(f"Extracted {len(frontend_files)} frontend files from failed workflow")
            
            # README with failure info
            readme_content = f"""# AI Generated Project (Incomplete)

**Session ID:** {session_id}  
**Status:** Failed during workflow execution  
**Generated:** {datetime.now().isoformat()}

## Project Request

{workflow_state['user_request']}

## Status

This project generation was incomplete due to a workflow failure. 
Some files may be missing or incomplete.

## Available Components

- Requirements: {'✅ Available' if workflow_state.get('refined_requirements') else '❌ Not completed'}
- Strategy: {'✅ Available' if workflow_state.get('final_strategy') else '❌ Not completed'}
- Backend: {'✅ Available' if workflow_state.get('backend_implementation') else '❌ Not completed'}
- Frontend: {'✅ Available' if workflow_state.get('frontend_implementation') else '❌ Not completed'}

## Next Steps

1. Review the available components
2. Retry the project generation if needed
3. Manual completion of missing components

*This project was generated by AI Orchestrator v2.0*
"""
            
            files.append(GeneratedFile(
                path="README.md",
                content=readme_content,
                file_type="documentation",
                language="markdown"
            ))
            
            # Create basic project structure
            project_structure = ProjectStructure(
                name=f"incomplete-project-{session_id[:8]}",
                description=workflow_state['user_request'][:100] + "..." if len(workflow_state['user_request']) > 100 else workflow_state['user_request'],
                session_id=session_id,
                created_at=datetime.now(),
                files=files,
                metadata={'status': 'failed', 'partial': True}
            )
            
            # Write to disk
            output_path = file_manager.write_project_to_disk(project_structure)
            self.logger.info(f"Created basic project structure for failed workflow: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create basic project structure: {str(e)}")

    def _create_successful_project_structure(self, session_id: str, final_state: Dict[str, Any]):
        """Automatically create project structure for successful workflows."""
        from ..utils.file_manager import FileOutputManager
        
        try:
            # Get the current workflow state
            state = self.active_sessions[session_id]
            
            # Create project structure and write to disk
            workflow_state_dict = {
                'session_id': session_id,
                'refined_requirements': state.refined_requirements,
                'gpt_brainstorm': state.gpt_brainstorm,
                'claude_brainstorm': state.claude_brainstorm,
                'final_strategy': state.final_strategy,
                'claude_plan': state.claude_plan,
                'improved_backend_implementation': state.improved_backend_implementation,
                'improved_frontend_implementation': state.improved_frontend_implementation,
                'backend_implementation': state.backend_implementation,
                'frontend_implementation': state.frontend_implementation,
                'test_implementation': state.test_implementation,
                'code_review_feedback': state.code_review_feedback,
                'final_documentation': state.final_documentation,
                'quality_report': state.quality_report
            }
            
            # Initialize file manager and generate project structure
            file_manager = FileOutputManager()
            project_structure = file_manager.create_project_structure(workflow_state_dict)
            
            # Write files to disk
            output_path = file_manager.write_project_to_disk(project_structure)
            
            self.logger.info(f"Auto-generated project files successfully: {output_path}")
            self.logger.info(f"Project name: {project_structure.name}")
            self.logger.info(f"Generated {len(project_structure.files)} files")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to auto-generate project structure: {str(e)}")
            raise

    def _create_adaptive_project_structure(self, session_id: str, final_state: Dict[str, Any], workflow):
        """Automatically create project structure for adaptive workflows."""
        from ..utils.file_manager import FileOutputManager
        
        try:
            # Get the current workflow state
            state = self.active_sessions[session_id]
            
            # Create project structure for adaptive workflow
            workflow_state_dict = {
                'session_id': session_id,
                'user_request': state.user_request,
                'refined_requirements': state.refined_requirements,
                'final_documentation': state.final_documentation,
                'test_implementation': state.test_implementation,
                'project_metadata': getattr(state, 'project_metadata', {}),
                'workflow_type': 'adaptive'
            }
            
            # Add all adaptive implementations
            if hasattr(state, 'adaptive_implementations'):
                workflow_state_dict.update(state.adaptive_implementations)
            
            # Add all phase results from final_state
            for key, value in final_state.items():
                if key.endswith('_result') or key in ['refined_requirements', 'documentation_generation_result']:
                    workflow_state_dict[key] = value
            
            # Initialize file manager and generate project structure
            file_manager = FileOutputManager()
            project_structure = file_manager.create_project_structure(workflow_state_dict)
            
            # Write files to disk
            output_path = file_manager.write_project_to_disk(project_structure)
            
            self.logger.info(f"Auto-generated adaptive project files successfully: {output_path}")
            self.logger.info(f"Project type: {workflow.project_analysis.project_type.value}")
            self.logger.info(f"Project name: {project_structure.name}")
            self.logger.info(f"Generated {len(project_structure.files)} files")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to auto-generate adaptive project structure: {str(e)}")
            raise

    async def start_micro_phase_workflow(self, user_request: str) -> str:
        """
        Start a new micro-phase workflow using the specialized agent system.
        
        Args:
            user_request: The initial project request from the user
            
        Returns:
            session_id: Unique identifier for this workflow session
        """
        self.logger.info("Starting micro-phase workflow")
        session_id = await self.micro_phase_coordinator.start_micro_phase_workflow(user_request)
        
        # Track session in our active sessions (for compatibility)
        workflow_state = WorkflowState(
            session_id=session_id,
            current_phase=WorkflowPhase.INITIALIZATION,
            user_request=user_request
        )
        self.active_sessions[session_id] = workflow_state
        
        self.logger.info(f"Started micro-phase workflow session: {session_id}")
        return session_id
    
    async def get_micro_phase_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a micro-phase workflow."""
        status = await self.micro_phase_coordinator.get_workflow_status(session_id)
        
        # Add workflow type identifier
        if "error" not in status:
            status["workflow_type"] = "micro_phase"
        
        return status
    
    def is_micro_phase_workflow(self, session_id: str) -> bool:
        """Check if a session is using the micro-phase workflow."""
        return session_id in self.micro_phase_coordinator.active_workflows
    
    async def get_unified_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get workflow status regardless of workflow type."""
        # Check if it's a micro-phase workflow first
        if self.is_micro_phase_workflow(session_id):
            return await self.get_micro_phase_status(session_id)
        else:
            # Fall back to legacy workflow status
            return await self.get_workflow_status(session_id)
    
    async def start_workflow_with_type(self, user_request: str, workflow_type: str = "legacy") -> str:
        """
        Start a workflow with specified type.
        
        Args:
            user_request: The initial project request
            workflow_type: "legacy" or "micro_phase"
            
        Returns:
            session_id: Unique identifier for this workflow session
        """
        if workflow_type == "micro_phase":
            return await self.start_micro_phase_workflow(user_request)
        else:
            return await self.start_workflow(user_request)

    async def cleanup(self):
        """Cleanup resources and active sessions."""
        self.logger.info("Cleaning up AI Orchestrator...")
        
        # Close all agent connections (legacy)
        await self.gpt_agent.cleanup()
        await self.claude_agent.cleanup()
        
        # Close new specialized agents
        await self.gpt_manager.cleanup()
        await self.gpt_validator.cleanup()
        await self.gpt_git_agent.cleanup()
        await self.gpt_integration_agent.cleanup()
        
        # Cleanup micro-phase coordinator
        await self.micro_phase_coordinator.cleanup()
        
        # Clear active sessions
        self.active_sessions.clear()
        
        self.logger.info("AI Orchestrator cleanup completed")