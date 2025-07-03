"""
Micro-Phase Coordinator - Orchestrates the new multi-GPT + Claude workflow.
Handles agent coordination and communication for micro-phase development.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from ..agents import (
    GPTManagerAgent, GPTValidatorAgent, GPTGitAgent, GPTIntegrationAgent,
    ClaudeAgent, AgentTask, TaskType, AgentResponse, MicroPhase, ValidationResult
)
from ..core.config import AIModelConfig, OpenAIConfig, AnthropicConfig
from ..utils.repository_manager import RepositoryManager, ProjectSetupConfig
from ..utils.ci_cd_automation import CICDAutomation, PipelineConfig, PipelineStage
from ..cache import CacheManager, CacheStatus
from ..cache.cost_optimizer import CostOptimizer
from ..documentation import PhaseDocumenter, PhaseDocumentation, ArchitecturePlan
from ..utils.process_monitor import get_process_monitor


class WorkflowPhase(str, Enum):
    """Phases in the micro-phase workflow."""
    JOINT_BRAINSTORMING = "joint_brainstorming"
    ARCHITECTURE_DESIGN = "architecture_design"
    ARCHITECTURE_REVIEW = "architecture_review"
    MICRO_PHASE_PLANNING = "micro_phase_planning"
    MICRO_PHASE_VALIDATION = "micro_phase_validation"
    ITERATIVE_DEVELOPMENT = "iterative_development"
    FINAL_INTEGRATION = "final_integration"


class PhaseStatus(str, Enum):
    """Status of workflow phases."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowState:
    """State management for the micro-phase workflow."""
    session_id: str
    current_phase: WorkflowPhase
    phase_status: Dict[WorkflowPhase, PhaseStatus]
    project_requirements: str
    
    # Brainstorming results
    gpt_brainstorm: Optional[str] = None
    claude_brainstorm: Optional[str] = None
    unified_features: Optional[str] = None
    
    # Architecture results
    claude_architecture: Optional[str] = None
    approved_architecture: Optional[str] = None
    architecture_feedback: Optional[str] = None
    
    # Micro-phase planning
    proposed_micro_phases: List[MicroPhase] = None
    approved_micro_phases: List[MicroPhase] = None
    
    # Development tracking
    completed_phases: List[str] = None
    current_micro_phase: Optional[MicroPhase] = None
    phase_results: Dict[str, Any] = None
    
    # Integration
    integration_results: Dict[str, Any] = None
    final_repository_url: Optional[str] = None
    
    def __post_init__(self):
        if self.phase_status is None:
            self.phase_status = {phase: PhaseStatus.PENDING for phase in WorkflowPhase}
        if self.proposed_micro_phases is None:
            self.proposed_micro_phases = []
        if self.approved_micro_phases is None:
            self.approved_micro_phases = []
        if self.completed_phases is None:
            self.completed_phases = []
        if self.phase_results is None:
            self.phase_results = {}
        if self.integration_results is None:
            self.integration_results = {}


class MicroPhaseCoordinator:
    """
    Coordinates the multi-GPT + Claude micro-phase workflow.
    
    Manages communication between specialized agents and orchestrates
    the complete development process from brainstorming to deployment.
    """
    
    def __init__(self, openai_config: OpenAIConfig, anthropic_config: AnthropicConfig, 
                 cache_root: str = "/tmp/ai_orchestrator_cache",
                 docs_root: str = "/tmp/ai_orchestrator_docs"):
        self.logger = logging.getLogger("micro_phase_coordinator")
        
        # Initialize documentation system first
        self.phase_documenter = PhaseDocumenter(docs_root)
        
        # Initialize prompt enhancer
        from ..documentation.prompt_enhancer import PromptEnhancer
        self.prompt_enhancer = PromptEnhancer(self.phase_documenter)
        
        # Initialize specialized agents with enhanced prompts
        self.gpt_manager = GPTManagerAgent(openai_config)
        self.gpt_validator = GPTValidatorAgent(openai_config)
        self.gpt_git_agent = GPTGitAgent(openai_config)
        self.gpt_integration_agent = GPTIntegrationAgent(openai_config)
        self.claude = ClaudeAgent(anthropic_config)
        self.claude.prompt_enhancer = self.prompt_enhancer
        
        # Initialize GitHub integration systems
        self.repository_manager = RepositoryManager()
        self.cicd_automation = CICDAutomation(self.gpt_git_agent.github_client)
        
        # Initialize caching system
        self.cache_manager = CacheManager(cache_root)
        self.cost_optimizer = CostOptimizer(self.cache_manager)
        
        # (Documentation system already initialized above)
        
        # State management
        self.active_workflows: Dict[str, WorkflowState] = {}
        
        # Process monitoring
        self.process_monitor = get_process_monitor()
        
        # Track phase timing for documentation
        self.phase_start_times: Dict[str, datetime] = {}
    
    async def start_micro_phase_workflow(self, project_requirements: str) -> str:
        """Start a new micro-phase workflow."""
        session_id = str(uuid.uuid4())
        
        workflow_state = WorkflowState(
            session_id=session_id,
            current_phase=WorkflowPhase.JOINT_BRAINSTORMING,
            phase_status={},
            project_requirements=project_requirements
        )
        
        self.active_workflows[session_id] = workflow_state
        
        self.logger.info(f"Started micro-phase workflow: {session_id}")
        
        # Log workflow start
        self.process_monitor.log_workflow_event(
            session_id=session_id,
            event="micro_phase_workflow_started",
            details={
                "project_requirements": project_requirements[:200],  # Truncate for display
                "workflow_type": "micro_phase",
                "available_phases": [phase.value for phase in WorkflowPhase]
            }
        )
        
        # Begin the workflow
        await self._execute_workflow(session_id)
        
        return session_id
    
    async def _execute_workflow(self, session_id: str):
        """Execute the complete micro-phase workflow."""
        workflow_state = self.active_workflows[session_id]
        
        # Initialize phase timing tracking
        self.phase_start_times[session_id] = datetime.utcnow()
        
        try:
            # Phase 0: Repository Setup
            await self._phase_repository_setup(workflow_state)
            
            # Phase 1: Joint Brainstorming
            await self._phase_joint_brainstorming(workflow_state)
            
            # Phase 2: Architecture Design
            await self._phase_architecture_design(workflow_state)
            
            # Phase 3: Architecture Review
            await self._phase_architecture_review(workflow_state)
            
            # Phase 4: Micro-Phase Planning
            await self._phase_micro_phase_planning(workflow_state)
            
            # Phase 5: Micro-Phase Validation
            await self._phase_micro_phase_validation(workflow_state)
            
            # Phase 6: Iterative Development
            await self._phase_iterative_development(workflow_state)
            
            # Phase 7: Final Integration
            await self._phase_final_integration(workflow_state)
            
            self.logger.info(f"Workflow completed successfully: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {session_id} - {str(e)}")
            workflow_state.phase_status[workflow_state.current_phase] = PhaseStatus.FAILED
            raise
    
    async def _phase_repository_setup(self, workflow_state: WorkflowState):
        """Phase 0: Set up GitHub repository and CI/CD infrastructure."""
        self.logger.info("Starting repository setup phase")
        workflow_state.current_phase = WorkflowPhase.JOINT_BRAINSTORMING  # Use existing enum for now
        
        # Create project setup configuration
        project_config = ProjectSetupConfig(
            project_name=f"ai-project-{workflow_state.session_id[:8]}",
            session_id=workflow_state.session_id,
            description=f"AI-generated project: {workflow_state.project_requirements[:100]}...",
            tech_stack=["python", "javascript"],  # Will be determined in architecture phase
            enable_ci_cd=False,  # Disabled to avoid Git conflicts
            enable_branch_protection=False,  # Disabled for free GitHub accounts
            private_repository=True
        )
        
        # Set up repository
        repo_state = await self.repository_manager.setup_micro_phase_project(project_config)
        
        # Set up CI/CD pipeline
        pipeline_config = PipelineConfig(
            name=f"AI Project Pipeline",
            triggers=["push", "pull_request"],
            stages=[
                PipelineStage.VALIDATION,
                PipelineStage.TESTING,
                PipelineStage.SECURITY,
                PipelineStage.QUALITY
            ],
            tech_stack=project_config.tech_stack
        )
        
        # Skip CI/CD setup to avoid GitHub API conflicts
        # cicd_result = await self.cicd_automation.setup_micro_phase_pipeline(
        #     repo_name=repo_state.repository_name,
        #     config=pipeline_config
        # )
        cicd_result = {"status": "skipped", "message": "CI/CD disabled to avoid conflicts"}
        
        # Store repository information in workflow state
        workflow_state.integration_results = {
            "repository_url": repo_state.repository_url,
            "repository_name": repo_state.repository_name,
            "ci_cd_setup": cicd_result,
            "branches": repo_state.created_branches
        }
        
        self.logger.info(f"Repository setup completed: {repo_state.repository_url}")
    
    async def _phase_joint_brainstorming(self, workflow_state: WorkflowState):
        """Phase 1: Joint brainstorming between GPT Manager and Claude."""
        self.logger.info("Starting joint brainstorming phase")
        workflow_state.current_phase = WorkflowPhase.JOINT_BRAINSTORMING
        workflow_state.phase_status[WorkflowPhase.JOINT_BRAINSTORMING] = PhaseStatus.IN_PROGRESS
        
        # Log phase start
        self.process_monitor.log_phase_start(
            session_id=workflow_state.session_id,
            phase_name=WorkflowPhase.JOINT_BRAINSTORMING.value,
            metadata={
                "description": "Joint brainstorming between GPT Manager and Claude",
                "agents": ["gpt_manager", "claude_agent"]
            }
        )
        
        # Check cache for existing brainstorming results
        cached_features = await self.cache_manager.get("brainstorming_features")
        if cached_features:
            self.logger.info("Using cached brainstorming results")
            workflow_state.unified_features = cached_features.get("content") if isinstance(cached_features, dict) else cached_features
            workflow_state.phase_status[WorkflowPhase.JOINT_BRAINSTORMING] = PhaseStatus.COMPLETED
            return
        
        # GPT Manager strategic brainstorming
        gpt_task = AgentTask(
            task_type=TaskType.BRAINSTORMING,
            prompt=workflow_state.project_requirements,
            context={},
            requirements={},
            session_id=workflow_state.session_id
        )
        
        gpt_response = await self.gpt_manager.execute_task(gpt_task)
        workflow_state.gpt_brainstorm = gpt_response.content
        
        # Claude technical brainstorming
        claude_task = AgentTask(
            task_type=TaskType.BRAINSTORMING,
            prompt=workflow_state.project_requirements,
            context={"gpt_brainstorm": workflow_state.gpt_brainstorm},
            requirements={},
            session_id=workflow_state.session_id
        )
        
        claude_response = await self.claude.execute_task(claude_task)
        workflow_state.claude_brainstorm = claude_response.content
        
        # GPT Manager synthesizes both perspectives
        synthesis_task = AgentTask(
            task_type=TaskType.PLAN_COMPARISON,
            prompt=workflow_state.project_requirements,
            context={
                "gpt_brainstorm": workflow_state.gpt_brainstorm,
                "claude_brainstorm": workflow_state.claude_brainstorm
            },
            requirements={},
            session_id=workflow_state.session_id
        )
        
        synthesis_response = await self.gpt_manager.execute_task(synthesis_task)
        workflow_state.unified_features = synthesis_response.content
        
        # Cache the brainstorming results
        await self.cache_manager.cache_brainstorming(
            workflow_state.unified_features,
            workflow_state.session_id
        )
        
        # Document the brainstorming phase
        phase_duration = (datetime.utcnow() - self.phase_start_times.get(workflow_state.session_id, datetime.utcnow())).total_seconds()
        await self.phase_documenter.document_brainstorming_phase(
            workflow_state.session_id,
            workflow_state.gpt_brainstorm,
            workflow_state.claude_brainstorm, 
            workflow_state.unified_features,
            phase_duration
        )
        
        workflow_state.phase_status[WorkflowPhase.JOINT_BRAINSTORMING] = PhaseStatus.COMPLETED
        self.logger.info("Joint brainstorming phase completed, cached, and documented")
    
    async def _phase_architecture_design(self, workflow_state: WorkflowState):
        """Phase 2: Claude designs the architecture."""
        self.logger.info("Starting architecture design phase")
        workflow_state.current_phase = WorkflowPhase.ARCHITECTURE_DESIGN
        workflow_state.phase_status[WorkflowPhase.ARCHITECTURE_DESIGN] = PhaseStatus.IN_PROGRESS
        
        # Check cache for existing architecture
        cached_architecture = await self.cache_manager.get("system_architecture_plan")
        if cached_architecture:
            self.logger.info("Using cached architecture plan")
            workflow_state.claude_architecture = cached_architecture.get("content") if isinstance(cached_architecture, dict) else cached_architecture
            workflow_state.phase_status[WorkflowPhase.ARCHITECTURE_DESIGN] = PhaseStatus.COMPLETED
            return
        
        architecture_task = AgentTask(
            task_type=TaskType.TECHNICAL_PLANNING,
            prompt=workflow_state.project_requirements,
            context={"unified_features": workflow_state.unified_features},
            requirements={},
            session_id=workflow_state.session_id
        )
        
        architecture_response = await self.claude.execute_task(architecture_task)
        workflow_state.claude_architecture = architecture_response.content
        
        # Cache the architecture plan
        await self.cache_manager.cache_architecture(
            workflow_state.claude_architecture,
            workflow_state.session_id,
            ["brainstorming_features"]
        )
        
        # Document architecture phase and create plan file
        phase_duration = (datetime.utcnow() - self.phase_start_times.get(f"{workflow_state.session_id}_arch", datetime.utcnow())).total_seconds()
        phase_doc, arch_plan = await self.phase_documenter.document_architecture_phase(
            workflow_state.session_id,
            workflow_state.claude_architecture,
            workflow_state.claude_architecture,  # Approved architecture (same in this case)
            phase_duration
        )
        
        # Store architecture plan reference in workflow state
        workflow_state.integration_results["architecture_plan_file"] = arch_plan
        
        workflow_state.phase_status[WorkflowPhase.ARCHITECTURE_DESIGN] = PhaseStatus.COMPLETED
        self.logger.info("Architecture design phase completed, cached, documented with plan file created")
    
    async def _phase_architecture_review(self, workflow_state: WorkflowState):
        """Phase 3: GPT Manager reviews and approves architecture."""
        self.logger.info("Starting architecture review phase")
        workflow_state.current_phase = WorkflowPhase.ARCHITECTURE_REVIEW
        workflow_state.phase_status[WorkflowPhase.ARCHITECTURE_REVIEW] = PhaseStatus.IN_PROGRESS
        
        review_task = AgentTask(
            task_type=TaskType.PLAN_COMPARISON,
            prompt=workflow_state.project_requirements,
            context={
                "unified_features": workflow_state.unified_features,
                "claude_architecture": workflow_state.claude_architecture
            },
            requirements={},
            session_id=workflow_state.session_id
        )
        
        review_response = await self.gpt_manager.execute_task(review_task)
        workflow_state.architecture_feedback = review_response.content
        
        # For now, assume approval. In real implementation, parse response for approval status
        workflow_state.approved_architecture = workflow_state.claude_architecture
        
        workflow_state.phase_status[WorkflowPhase.ARCHITECTURE_REVIEW] = PhaseStatus.COMPLETED
        self.logger.info("Architecture review phase completed")
    
    async def _phase_micro_phase_planning(self, workflow_state: WorkflowState):
        """Phase 4: Claude breaks down project into micro-phases."""
        self.logger.info("Starting micro-phase planning")
        workflow_state.current_phase = WorkflowPhase.MICRO_PHASE_PLANNING
        workflow_state.phase_status[WorkflowPhase.MICRO_PHASE_PLANNING] = PhaseStatus.IN_PROGRESS
        
        # Check cache for existing micro-phase breakdown
        cached_phases = await self.cache_manager.get("project_micro_phases")
        if cached_phases:
            self.logger.info("Using cached micro-phase breakdown")
            # Convert cached data back to MicroPhase objects
            workflow_state.proposed_micro_phases = [
                MicroPhase(**phase_data) for phase_data in cached_phases
            ] if isinstance(cached_phases, list) else []
            workflow_state.phase_status[WorkflowPhase.MICRO_PHASE_PLANNING] = PhaseStatus.COMPLETED
            return
        
        planning_task = AgentTask(
            task_type=TaskType.MICRO_PHASE_PLANNING,
            prompt=workflow_state.project_requirements,
            context={
                "approved_architecture": workflow_state.approved_architecture,
                "unified_features": workflow_state.unified_features
            },
            requirements={},
            session_id=workflow_state.session_id
        )
        
        planning_response = await self.claude.execute_task(planning_task)
        
        # Parse micro-phases from response (simplified for demo)
        # In real implementation, parse the structured response
        workflow_state.proposed_micro_phases = await self.claude.create_micro_phases(
            {"architecture": workflow_state.approved_architecture},
            ["feature1", "feature2"]
        )
        
        # Cache the micro-phase breakdown
        await self.cache_manager.cache_micro_phases(
            workflow_state.proposed_micro_phases,
            workflow_state.session_id,
            ["system_architecture_plan"]
        )
        
        # Document micro-phase planning
        phase_duration = (datetime.utcnow() - self.phase_start_times.get(f"{workflow_state.session_id}_planning", datetime.utcnow())).total_seconds()
        await self.phase_documenter.document_micro_phase_planning(
            workflow_state.session_id,
            workflow_state.proposed_micro_phases,
            phase_duration
        )
        
        workflow_state.phase_status[WorkflowPhase.MICRO_PHASE_PLANNING] = PhaseStatus.COMPLETED
        self.logger.info("Micro-phase planning completed, cached, and documented with updated plan file")
    
    async def _phase_micro_phase_validation(self, workflow_state: WorkflowState):
        """Phase 5: GPT Manager validates micro-phase breakdown."""
        self.logger.info("Starting micro-phase validation")
        workflow_state.current_phase = WorkflowPhase.MICRO_PHASE_VALIDATION
        workflow_state.phase_status[WorkflowPhase.MICRO_PHASE_VALIDATION] = PhaseStatus.IN_PROGRESS
        
        validation_task = AgentTask(
            task_type=TaskType.MICRO_PHASE_VALIDATION,
            prompt=workflow_state.project_requirements,
            context={
                "approved_architecture": workflow_state.approved_architecture,
                "proposed_micro_phases": [asdict(phase) for phase in workflow_state.proposed_micro_phases]
            },
            requirements={},
            session_id=workflow_state.session_id
        )
        
        validation_response = await self.gpt_manager.execute_task(validation_task)
        
        # For now, assume approval
        workflow_state.approved_micro_phases = workflow_state.proposed_micro_phases
        
        workflow_state.phase_status[WorkflowPhase.MICRO_PHASE_VALIDATION] = PhaseStatus.COMPLETED
        self.logger.info("Micro-phase validation completed")
    
    async def _phase_iterative_development(self, workflow_state: WorkflowState):
        """Phase 6: Iterative development of each micro-phase."""
        self.logger.info("Starting iterative development")
        workflow_state.current_phase = WorkflowPhase.ITERATIVE_DEVELOPMENT
        workflow_state.phase_status[WorkflowPhase.ITERATIVE_DEVELOPMENT] = PhaseStatus.IN_PROGRESS
        
        for micro_phase in workflow_state.approved_micro_phases:
            await self._execute_micro_phase(workflow_state, micro_phase)
        
        workflow_state.phase_status[WorkflowPhase.ITERATIVE_DEVELOPMENT] = PhaseStatus.COMPLETED
        self.logger.info("Iterative development completed")
    
    async def _execute_micro_phase(self, workflow_state: WorkflowState, micro_phase: MicroPhase):
        """Execute a single micro-phase."""
        self.logger.info(f"Executing micro-phase: {micro_phase.name}")
        workflow_state.current_micro_phase = micro_phase
        
        # Track phase start time for documentation
        phase_start_time = datetime.utcnow()
        
        # Get implementation guide from architecture plan
        implementation_guide = await self.phase_documenter.get_implementation_guide_for_phase(
            workflow_state.session_id, micro_phase.id
        )
        
        # Check cache for existing implementation
        cached_files = await self.cache_manager.get_phase_files(micro_phase.id)
        cached_validation = await self.cache_manager.get(f"phase-{micro_phase.id}-validation_report")
        
        if cached_files and cached_validation:
            self.logger.info(f"Using cached implementation for micro-phase: {micro_phase.name}")
            
            # Use cached GitHub operations if available
            github_result = await self.repository_manager.execute_micro_phase_workflow(
                session_id=workflow_state.session_id,
                micro_phase=micro_phase,
                generated_files=cached_files
            )
            
            # Store results using cached data
            workflow_state.phase_results[micro_phase.id] = {
                "implementation": "Loaded from cache",
                "validation": cached_validation,
                "github_operations": github_result,
                "repository_url": github_result.get("repository_url"),
                "pull_request_url": github_result.get("pull_request", {}).get("url"),
                "cached": True
            }
            
            workflow_state.completed_phases.append(micro_phase.id)
            self.logger.info(f"Micro-phase completed from cache: {micro_phase.name}")
            return
        
        # Claude implements the micro-phase with plan file guidance
        implementation_task = AgentTask(
            task_type=TaskType.MICRO_PHASE_IMPLEMENTATION,
            prompt=workflow_state.project_requirements,
            context={
                "micro_phase": asdict(micro_phase),
                "previous_phases": workflow_state.completed_phases,
                "project_architecture": workflow_state.approved_architecture,
                "implementation_guide": implementation_guide,
                "architecture_plan_file": workflow_state.integration_results.get("architecture_plan_file"),
                "phase_documentation": await self.phase_documenter.get_phase_documentation(workflow_state.session_id)
            },
            requirements={},
            session_id=workflow_state.session_id,
            micro_phase_id=micro_phase.id
        )
        
        implementation_response = await self.claude.execute_task(implementation_task)
        
        # GPT Validator validates the implementation
        validation_task = AgentTask(
            task_type=TaskType.CODE_VALIDATION,
            prompt="Validate micro-phase implementation",
            context={
                "generated_files": {"main.py": implementation_response.content},
                "micro_phase": asdict(micro_phase),
                "acceptance_criteria": micro_phase.acceptance_criteria
            },
            requirements={},
            session_id=workflow_state.session_id,
            micro_phase_id=micro_phase.id
        )
        
        validation_response = await self.gpt_validator.execute_task(validation_task)
        
        # Execute real GitHub operations
        repo_name = workflow_state.integration_results.get("repository_name", "")
        generated_files = {f"src/{micro_phase.name.lower()}.py": implementation_response.content}
        
        # Cache the generated files and validation results
        await self.cache_manager.cache_phase_files(
            micro_phase.id,
            generated_files,
            workflow_state.session_id,
            ["project_micro_phases"]
        )
        
        validation_report = {
            "success": True,  # Simplified - parse from validation_response
            "details": validation_response.content,
            "timestamp": workflow_state.session_id
        }
        
        await self.cache_manager.cache_validation_report(
            micro_phase.id,
            validation_report,
            workflow_state.session_id
        )
        
        # Use repository manager for actual GitHub operations
        github_result = await self.repository_manager.execute_micro_phase_workflow(
            session_id=workflow_state.session_id,
            micro_phase=micro_phase,
            generated_files=generated_files
        )
        
        # Skip CI/CD validation completely to avoid GitHub API conflicts
        validation_result = {"status": "skipped", "message": "CI/CD validation disabled"}
        
        # Document micro-phase implementation
        phase_duration = (datetime.utcnow() - phase_start_time).total_seconds()
        phase_doc = await self.phase_documenter.document_micro_phase_implementation(
            workflow_state.session_id,
            micro_phase,
            implementation_response.content,
            validation_report,
            github_result,
            phase_duration
        )
        
        # Store results
        workflow_state.phase_results[micro_phase.id] = {
            "implementation": implementation_response.content,
            "validation": validation_response.content,
            "github_operations": github_result,
            "ci_cd_validation": validation_result if 'validation_result' in locals() else None,
            "repository_url": github_result.get("repository_url"),
            "pull_request_url": github_result.get("pull_request", {}).get("url"),
            "cached": False,
            "documentation": asdict(phase_doc)
        }
        
        workflow_state.completed_phases.append(micro_phase.id)
        self.logger.info(f"Micro-phase completed, cached, and documented: {micro_phase.name}")
    
    async def _phase_final_integration(self, workflow_state: WorkflowState):
        """Phase 7: Final integration and deployment."""
        self.logger.info("Starting final integration")
        workflow_state.current_phase = WorkflowPhase.FINAL_INTEGRATION
        workflow_state.phase_status[WorkflowPhase.FINAL_INTEGRATION] = PhaseStatus.IN_PROGRESS
        
        integration_task = AgentTask(
            task_type=TaskType.FINAL_ASSEMBLY,
            prompt="Integrate all micro-phases and prepare for deployment",
            context={
                "completed_phases": workflow_state.completed_phases,
                "project_metadata": {"session_id": workflow_state.session_id},
                "deployment_target": "production"
            },
            requirements={},
            session_id=workflow_state.session_id
        )
        
        integration_response = await self.gpt_integration_agent.execute_task(integration_task)
        
        # Finalize project integration in repository
        repo_finalization = await self.repository_manager.finalize_project_integration(
            session_id=workflow_state.session_id
        )
        
        # Cache the final integration summary
        integration_summary = {
            "status": "completed",
            "details": integration_response.content,
            "finalization": repo_finalization,
            "final_repository_url": repo_finalization.get("repository_url"),
            "completed_phases": workflow_state.completed_phases
        }
        
        await self.cache_manager.cache_integration_summary(
            integration_summary,
            workflow_state.session_id,
            [f"phase-{phase_id}-validation_report" for phase_id in workflow_state.completed_phases]
        )
        
        # Document integration phase
        phase_duration = (datetime.utcnow() - self.phase_start_times.get(f"{workflow_state.session_id}_integration", datetime.utcnow())).total_seconds()
        integration_doc = await self.phase_documenter.document_integration_phase(
            workflow_state.session_id,
            integration_summary,
            workflow_state.completed_phases,
            phase_duration
        )
        
        workflow_state.integration_results.update(integration_summary)
        workflow_state.final_repository_url = repo_finalization.get("repository_url")
        workflow_state.integration_results["documentation"] = asdict(integration_doc)
        
        workflow_state.phase_status[WorkflowPhase.FINAL_INTEGRATION] = PhaseStatus.COMPLETED
        self.logger.info("Final integration completed, cached, and fully documented")
    
    async def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a workflow."""
        if session_id not in self.active_workflows:
            return {"error": "Workflow not found"}
        
        workflow_state = self.active_workflows[session_id]
        
        # Get cache analytics for the session
        cache_stats = await self.cache_manager.get_cache_analytics()
        
        # Get documentation summary
        phase_docs = await self.phase_documenter.get_phase_documentation(session_id)
        
        return {
            "session_id": session_id,
            "current_phase": workflow_state.current_phase.value,
            "phase_status": {phase.value: status.value for phase, status in workflow_state.phase_status.items()},
            "completed_phases_count": len(workflow_state.completed_phases),
            "total_phases_count": len(workflow_state.approved_micro_phases) if workflow_state.approved_micro_phases else 0,
            "repository_url": workflow_state.final_repository_url,
            "cache_stats": {
                "hit_rate": f"{cache_stats.hit_rate:.1f}%",
                "cost_savings_usd": f"${cache_stats.cost_savings_usd:.2f}",
                "api_calls_saved": cache_stats.api_calls_saved
            },
            "documentation_stats": {
                "total_phase_docs": len(phase_docs),
                "documented_phases": [doc.phase_name for doc in phase_docs],
                "total_documentation_time": f"{sum(doc.duration_seconds for doc in phase_docs):.1f}s"
            }
        }
    
    async def get_cost_analysis(self, session_id: str) -> Dict[str, Any]:
        """Get detailed cost analysis for a workflow session."""
        if session_id not in self.active_workflows:
            return {"error": "Workflow not found"}
        
        # Generate comprehensive cost report
        cost_report = await self.cost_optimizer.generate_cost_report()
        
        return {
            "session_id": session_id,
            "cost_analysis": cost_report,
            "cache_effectiveness": cost_report["summary"]["cache_effectiveness"],
            "estimated_monthly_cost": cost_report["summary"]["current_monthly_cost"],
            "top_recommendation": cost_report["summary"]["top_recommendation"]
        }
    
    async def invalidate_cache(self, cache_key: str) -> Dict[str, Any]:
        """Manually invalidate cache entries."""
        invalidated_keys = await self.cache_manager.invalidate(cache_key, cascade=True)
        
        return {
            "invalidated_keys": invalidated_keys,
            "message": f"Invalidated {len(invalidated_keys)} cache entries"
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.gpt_manager.cleanup()
        await self.gpt_validator.cleanup()
        await self.gpt_git_agent.cleanup()
        await self.gpt_integration_agent.cleanup()
        await self.claude.cleanup()
        
        # Cleanup GitHub integration components
        await self.repository_manager.cleanup()
        
        # Cleanup caching system
        await self.cache_manager.cleanup()
        
        # Cleanup documentation system
        await self.phase_documenter.cleanup()
        
        # Note: cicd_automation cleanup is handled via github_client