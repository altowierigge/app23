"""
Dynamic workflow generator that creates custom workflows based on project analysis.
"""
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .project_analyzer import ProjectAnalyzer, ProjectAnalysis, ProjectType
from ..agents import GPTManagerAgent, ClaudeAgent, AgentTask, TaskType
from ..utils.logging_config import get_logger
from ..utils.process_monitor import get_process_monitor


@dataclass
class DynamicPhase:
    """A dynamically generated workflow phase."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    agent_type: str = ""  # "gpt_manager", "claude", etc.
    task_type: TaskType = TaskType.IMPLEMENTATION
    depends_on: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)
    estimated_duration: int = 300  # seconds
    required: bool = True
    parallel_group: Optional[str] = None
    validation_criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class AdaptiveWorkflow:
    """A complete adaptive workflow for a project."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_analysis: ProjectAnalysis = None
    phases: List[DynamicPhase] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdaptiveWorkflowGenerator:
    """Generates custom workflows based on project requirements."""
    
    def __init__(self, gpt_manager: GPTManagerAgent):
        self.gpt_manager = gpt_manager
        self.project_analyzer = ProjectAnalyzer(gpt_manager)
        self.logger = get_logger("adaptive_workflow")
        self.process_monitor = get_process_monitor()
        
    async def generate_workflow(self, user_request: str, session_id: str) -> AdaptiveWorkflow:
        """
        Generate a complete adaptive workflow for the user's request.
        
        This is the main entry point that:
        1. Analyzes the project request
        2. Creates custom phases based on project needs
        3. Returns a complete workflow ready for execution
        """
        self.logger.info(f"Generating adaptive workflow for session: {session_id}")
        
        # Step 1: Analyze the project
        project_analysis = await self.project_analyzer.analyze(user_request, session_id)
        
        self.process_monitor.log_workflow_event(
            session_id=session_id,
            event="project_analysis_complete",
            details={
                "project_type": project_analysis.project_type.value,
                "complexity": project_analysis.estimated_complexity,
                "components": len(project_analysis.components)
            }
        )
        
        # Step 2: Generate workflow phases
        phases = await self._generate_phases(project_analysis, session_id)
        
        # Step 3: Optimize phase ordering and dependencies
        phases = self._optimize_phase_order(phases)
        
        # Step 4: Create workflow
        workflow = AdaptiveWorkflow(
            project_analysis=project_analysis,
            phases=phases,
            metadata={
                "session_id": session_id,
                "estimated_total_duration": sum(p.estimated_duration for p in phases),
                "phase_count": len(phases),
                "parallelizable_phases": len([p for p in phases if p.parallel_group])
            }
        )
        
        self.logger.info(f"Generated workflow with {len(phases)} phases for {project_analysis.project_type.value}")
        
        return workflow
    
    async def _generate_phases(self, analysis: ProjectAnalysis, session_id: str) -> List[DynamicPhase]:
        """Generate custom phases based on project analysis."""
        phases = []
        
        # Always start with requirements refinement
        phases.append(DynamicPhase(
            name="requirements_refinement",
            description="Refine and clarify project requirements",
            agent_type="gpt_manager",
            task_type=TaskType.REQUIREMENTS_REFINEMENT,
            outputs=["refined_requirements"],
            estimated_duration=300,
            validation_criteria={
                "min_length": 200,
                "required_sections": ["CORE_FEATURES", "PROJECT_UNDERSTANDING", "TECHNICAL_REQUIREMENTS"]
            }
        ))
        
        # Add project-specific phases
        if analysis.project_type == ProjectType.CLI_TOOL:
            phases.extend(self._generate_cli_phases(analysis))
        elif analysis.project_type == ProjectType.WEB_APP:
            phases.extend(self._generate_webapp_phases(analysis))
        elif analysis.project_type == ProjectType.GAME:
            phases.extend(self._generate_game_phases(analysis))
        elif analysis.project_type == ProjectType.API_SERVICE:
            phases.extend(self._generate_api_phases(analysis))
        elif analysis.project_type == ProjectType.BOT:
            phases.extend(self._generate_bot_phases(analysis))
        elif analysis.project_type == ProjectType.DATA_PIPELINE:
            phases.extend(self._generate_data_pipeline_phases(analysis))
        elif analysis.project_type == ProjectType.ML_PROJECT:
            phases.extend(self._generate_ml_phases(analysis))
        else:
            phases.extend(self._generate_generic_phases(analysis))
        
        # Always end with testing and documentation
        phases.extend([
            DynamicPhase(
                name="testing_implementation",
                description="Implement comprehensive tests",
                agent_type="claude",
                task_type=TaskType.IMPLEMENTATION,
                depends_on=[p.name for p in phases if "implementation" in p.name],
                outputs=["test_suite"],
                estimated_duration=600
            ),
            DynamicPhase(
                name="documentation_generation",
                description="Generate project documentation",
                agent_type="gpt_manager",
                task_type=TaskType.CONSULTATION,
                depends_on=[p.name for p in phases],
                outputs=["documentation"],
                estimated_duration=300
            )
        ])
        
        return phases
    
    def _generate_cli_phases(self, analysis: ProjectAnalysis) -> List[DynamicPhase]:
        """Generate phases for CLI tool projects."""
        phases = []
        
        # Architecture phase
        phases.append(DynamicPhase(
            name="cli_architecture",
            description="Design CLI tool architecture and command structure",
            agent_type="claude",
            task_type=TaskType.TECHNICAL_PLANNING,
            depends_on=["requirements_refinement"],
            outputs=["architecture_design"],
            estimated_duration=400
        ))
        
        # Core logic implementation
        phases.append(DynamicPhase(
            name="core_logic_implementation",
            description="Implement core business logic and algorithms",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["cli_architecture"],
            outputs=["core_logic"],
            estimated_duration=900
        ))
        
        # CLI interface
        phases.append(DynamicPhase(
            name="cli_interface_implementation",
            description="Implement command-line interface with argument parsing",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["core_logic_implementation"],
            outputs=["cli_interface"],
            estimated_duration=600
        ))
        
        # Output formatting
        if any(word in analysis.description.lower() for word in ['report', 'format', 'output', 'export']):
            phases.append(DynamicPhase(
                name="output_formatting",
                description="Implement output formatting and export options",
                agent_type="claude",
                task_type=TaskType.IMPLEMENTATION,
                depends_on=["cli_interface_implementation"],
                outputs=["formatters"],
                estimated_duration=400
            ))
        
        return phases
    
    def _generate_webapp_phases(self, analysis: ProjectAnalysis) -> List[DynamicPhase]:
        """Generate phases for web application projects."""
        phases = []
        
        # Architecture
        phases.append(DynamicPhase(
            name="webapp_architecture",
            description="Design application architecture and tech stack",
            agent_type="claude",
            task_type=TaskType.TECHNICAL_PLANNING,
            depends_on=["requirements_refinement"],
            outputs=["architecture_design", "tech_stack"],
            estimated_duration=600
        ))
        
        # Database design (if needed)
        if any(word in str(analysis.components).lower() for word in ['database', 'storage', 'data']):
            phases.append(DynamicPhase(
                name="database_design",
                description="Design database schema and relationships",
                agent_type="claude",
                task_type=TaskType.TECHNICAL_PLANNING,
                depends_on=["webapp_architecture"],
                outputs=["database_schema"],
                estimated_duration=400
            ))
        
        # Backend implementation
        phases.append(DynamicPhase(
            name="backend_implementation",
            description="Implement backend API and business logic",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["webapp_architecture", "database_design"] if "database_design" in [p.name for p in phases] else ["webapp_architecture"],
            outputs=["backend_code"],
            estimated_duration=1200
        ))
        
        # Frontend implementation  
        phases.append(DynamicPhase(
            name="frontend_implementation",
            description="Implement user interface and client-side logic",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["backend_implementation"],
            outputs=["frontend_code"],
            estimated_duration=1200,
            parallel_group="ui_implementation" if analysis.estimated_complexity != "complex" else None
        ))
        
        # Integration
        phases.append(DynamicPhase(
            name="integration",
            description="Integrate frontend with backend and ensure everything works",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["frontend_implementation", "backend_implementation"],
            outputs=["integrated_app"],
            estimated_duration=600
        ))
        
        return phases
    
    def _generate_game_phases(self, analysis: ProjectAnalysis) -> List[DynamicPhase]:
        """Generate phases for game projects."""
        phases = []
        
        # Game design
        phases.append(DynamicPhase(
            name="game_design",
            description="Design game mechanics, rules, and architecture",
            agent_type="claude",
            task_type=TaskType.TECHNICAL_PLANNING,
            depends_on=["requirements_refinement"],
            outputs=["game_design_doc"],
            estimated_duration=600
        ))
        
        # Engine setup
        phases.append(DynamicPhase(
            name="engine_setup",
            description="Set up game engine and project structure",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["game_design"],
            outputs=["game_engine"],
            estimated_duration=400
        ))
        
        # Core mechanics
        phases.append(DynamicPhase(
            name="core_mechanics",
            description="Implement core game mechanics and player controls",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["engine_setup"],
            outputs=["game_mechanics"],
            estimated_duration=1200
        ))
        
        # Game systems
        phases.append(DynamicPhase(
            name="game_systems",
            description="Implement game systems (scoring, levels, etc.)",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["core_mechanics"],
            outputs=["game_systems"],
            estimated_duration=900
        ))
        
        # Polish and assets
        phases.append(DynamicPhase(
            name="polish_and_assets",
            description="Add graphics, sound, and polish",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["game_systems"],
            outputs=["polished_game"],
            estimated_duration=600
        ))
        
        return phases
    
    def _generate_api_phases(self, analysis: ProjectAnalysis) -> List[DynamicPhase]:
        """Generate phases for API service projects."""
        phases = []
        
        # API design
        phases.append(DynamicPhase(
            name="api_design",
            description="Design API endpoints, data models, and architecture",
            agent_type="claude",
            task_type=TaskType.TECHNICAL_PLANNING,
            depends_on=["requirements_refinement"],
            outputs=["api_specification"],
            estimated_duration=500
        ))
        
        # Database design (if needed)
        if any(word in str(analysis.components).lower() for word in ['database', 'storage', 'persist']):
            phases.append(DynamicPhase(
                name="database_setup",
                description="Set up database and design schema",
                agent_type="claude",
                task_type=TaskType.IMPLEMENTATION,
                depends_on=["api_design"],
                outputs=["database_models"],
                estimated_duration=400
            ))
        
        # Core API implementation
        phases.append(DynamicPhase(
            name="api_implementation",
            description="Implement API endpoints and business logic",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["api_design", "database_setup"] if "database_setup" in [p.name for p in phases] else ["api_design"],
            outputs=["api_code"],
            estimated_duration=1000
        ))
        
        # Authentication/Security (if needed)
        if any(word in analysis.description.lower() for word in ['auth', 'secure', 'login', 'user']):
            phases.append(DynamicPhase(
                name="security_implementation",
                description="Implement authentication and security features",
                agent_type="claude",
                task_type=TaskType.IMPLEMENTATION,
                depends_on=["api_implementation"],
                outputs=["security_layer"],
                estimated_duration=600
            ))
        
        # API documentation
        phases.append(DynamicPhase(
            name="api_documentation",
            description="Generate OpenAPI/Swagger documentation",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["api_implementation"],
            outputs=["api_docs"],
            estimated_duration=300
        ))
        
        return phases
    
    def _generate_bot_phases(self, analysis: ProjectAnalysis) -> List[DynamicPhase]:
        """Generate phases for bot projects (Discord, Telegram, etc.)."""
        phases = []
        
        # Bot architecture
        phases.append(DynamicPhase(
            name="bot_architecture",
            description="Design bot architecture and command structure",
            agent_type="claude",
            task_type=TaskType.TECHNICAL_PLANNING,
            depends_on=["requirements_refinement"],
            outputs=["bot_design"],
            estimated_duration=400
        ))
        
        # Bot setup
        phases.append(DynamicPhase(
            name="bot_setup",
            description="Set up bot framework and authentication",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["bot_architecture"],
            outputs=["bot_framework"],
            estimated_duration=300
        ))
        
        # Command implementation
        phases.append(DynamicPhase(
            name="command_implementation",
            description="Implement bot commands and handlers",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["bot_setup"],
            outputs=["bot_commands"],
            estimated_duration=900
        ))
        
        # Features implementation
        phases.append(DynamicPhase(
            name="features_implementation",
            description="Implement specific bot features",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["command_implementation"],
            outputs=["bot_features"],
            estimated_duration=800
        ))
        
        return phases
    
    def _generate_data_pipeline_phases(self, analysis: ProjectAnalysis) -> List[DynamicPhase]:
        """Generate phases for data pipeline projects."""
        phases = []
        
        # Pipeline design
        phases.append(DynamicPhase(
            name="pipeline_design",
            description="Design data pipeline architecture and flow",
            agent_type="claude",
            task_type=TaskType.TECHNICAL_PLANNING,
            depends_on=["requirements_refinement"],
            outputs=["pipeline_architecture"],
            estimated_duration=500
        ))
        
        # Data ingestion
        phases.append(DynamicPhase(
            name="data_ingestion",
            description="Implement data ingestion and validation",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["pipeline_design"],
            outputs=["ingestion_layer"],
            estimated_duration=700
        ))
        
        # Data processing
        phases.append(DynamicPhase(
            name="data_processing",
            description="Implement data transformation and processing",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["data_ingestion"],
            outputs=["processing_layer"],
            estimated_duration=900
        ))
        
        # Data output
        phases.append(DynamicPhase(
            name="data_output",
            description="Implement data output and storage",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["data_processing"],
            outputs=["output_layer"],
            estimated_duration=600
        ))
        
        return phases
    
    def _generate_ml_phases(self, analysis: ProjectAnalysis) -> List[DynamicPhase]:
        """Generate phases for machine learning projects."""
        phases = []
        
        # ML design
        phases.append(DynamicPhase(
            name="ml_design",
            description="Design ML pipeline and model architecture",
            agent_type="claude",
            task_type=TaskType.TECHNICAL_PLANNING,
            depends_on=["requirements_refinement"],
            outputs=["ml_architecture"],
            estimated_duration=600
        ))
        
        # Data preparation
        phases.append(DynamicPhase(
            name="data_preparation",
            description="Implement data loading and preprocessing",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["ml_design"],
            outputs=["data_pipeline"],
            estimated_duration=800
        ))
        
        # Model implementation
        phases.append(DynamicPhase(
            name="model_implementation",
            description="Implement ML model and training logic",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["data_preparation"],
            outputs=["ml_model"],
            estimated_duration=1000
        ))
        
        # Evaluation
        phases.append(DynamicPhase(
            name="model_evaluation",
            description="Implement model evaluation and metrics",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["model_implementation"],
            outputs=["evaluation_results"],
            estimated_duration=500
        ))
        
        # Deployment prep
        phases.append(DynamicPhase(
            name="deployment_preparation",
            description="Prepare model for deployment",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["model_evaluation"],
            outputs=["deployment_package"],
            estimated_duration=600
        ))
        
        return phases
    
    def _generate_generic_phases(self, analysis: ProjectAnalysis) -> List[DynamicPhase]:
        """Generate generic phases for unspecified project types."""
        phases = []
        
        # Design phase
        phases.append(DynamicPhase(
            name="system_design",
            description="Design system architecture and components",
            agent_type="claude",
            task_type=TaskType.TECHNICAL_PLANNING,
            depends_on=["requirements_refinement"],
            outputs=["system_design"],
            estimated_duration=600
        ))
        
        # Core implementation
        phases.append(DynamicPhase(
            name="core_implementation",
            description="Implement core functionality",
            agent_type="claude",
            task_type=TaskType.IMPLEMENTATION,
            depends_on=["system_design"],
            outputs=["core_code"],
            estimated_duration=1200
        ))
        
        # Additional features
        if len(analysis.features) > 3:
            phases.append(DynamicPhase(
                name="feature_implementation",
                description="Implement additional features",
                agent_type="claude",
                task_type=TaskType.IMPLEMENTATION,
                depends_on=["core_implementation"],
                outputs=["features"],
                estimated_duration=900
            ))
        
        return phases
    
    def _optimize_phase_order(self, phases: List[DynamicPhase]) -> List[DynamicPhase]:
        """Optimize phase ordering and identify parallelization opportunities."""
        # Sort phases by dependencies
        sorted_phases = []
        phase_dict = {p.name: p for p in phases}
        
        # Topological sort
        visited = set()
        
        def visit(phase_name: str):
            if phase_name in visited:
                return
            visited.add(phase_name)
            
            phase = phase_dict.get(phase_name)
            if not phase:
                return
                
            for dep in phase.depends_on:
                visit(dep)
                
            sorted_phases.append(phase)
        
        for phase in phases:
            visit(phase.name)
            
        # Identify parallelization opportunities
        for i, phase in enumerate(sorted_phases):
            # Check if this phase can run in parallel with others
            if i > 0:
                prev_phase = sorted_phases[i-1]
                if not any(dep in prev_phase.outputs for dep in phase.depends_on):
                    # Can potentially run in parallel
                    phase.parallel_group = f"group_{i//2}"
                    
        return sorted_phases