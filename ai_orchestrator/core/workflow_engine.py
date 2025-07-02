"""
YAML-based workflow engine for dynamic orchestration configuration.
"""

import yaml
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

from ..agents import TaskType, AgentTask, AgentRole
from .config import get_config


@dataclass
class WorkflowPhase:
    """Definition of a workflow phase from YAML configuration."""
    name: str
    description: str
    agent: str
    task_type: str
    parallel: bool = False
    parallel_group: Optional[str] = None
    required: bool = True
    enabled: bool = True  # Add enabled flag to skip phases
    condition: Optional[str] = None
    timeout: int = 300
    depends_on: Optional[List[str]] = None
    inputs: Optional[List[Dict[str, Any]]] = None
    outputs: Optional[List[Dict[str, Any]]] = None
    validation: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []
        if self.inputs is None:
            self.inputs = []
        if self.outputs is None:
            self.outputs = []
        if self.validation is None:
            self.validation = {}
        if self.retry_config is None:
            self.retry_config = {}
        # Ensure enabled is always a boolean
        if self.enabled is None:
            self.enabled = True


@dataclass
class WorkflowDefinition:
    """Complete workflow definition loaded from YAML."""
    name: str
    version: str
    description: str
    settings: Dict[str, Any]
    agents: Dict[str, Dict[str, Any]]
    phases: List[WorkflowPhase]
    conditions: Dict[str, Dict[str, Any]]
    error_handling: Dict[str, Any]
    output: Dict[str, Any]
    monitoring: Dict[str, Any]


class WorkflowEngine:
    """
    Engine for executing YAML-defined workflows with dynamic configuration.
    """
    
    def __init__(self, workflow_path: Optional[str] = None):
        self.config = get_config()
        self.logger = logging.getLogger("workflow_engine")
        
        # Load workflow definition
        workflow_file = workflow_path or self.config.workflow_config_path
        self.workflow_def = self._load_workflow_definition(workflow_file)
        
        # Runtime state
        self.workflow_state = {}
        self.execution_context = {}
        self.phase_results = {}
        
        # Agent mapping (will be set by orchestrator)
        self.agent_map = {}
        
        # Condition evaluators
        self.condition_evaluators = {
            'disagreements_exist': self._eval_disagreements_exist,
            'voting_enabled': self._eval_voting_enabled,
            'tie_exists': self._eval_tie_exists
        }
        
        # Data parsers
        self.data_parsers = {
            'disagreement_parser': self._parse_disagreements,
            'vote_parser': self._parse_vote,
            'extract_voting_options': self._extract_voting_options,
            'extract_api_structure': self._extract_api_structure
        }
        
        self.logger.info(f"Workflow engine initialized: {self.workflow_def.name} v{self.workflow_def.version}")
    
    def _load_workflow_definition(self, workflow_path: str) -> WorkflowDefinition:
        """Load and parse YAML workflow definition."""
        try:
            with open(workflow_path, 'r') as file:
                data = yaml.safe_load(file)
            
            # Parse phases
            phases = []
            for phase_data in data.get('phases', []):
                phase = WorkflowPhase(
                    name=phase_data['name'],
                    description=phase_data['description'],
                    agent=phase_data['agent'],
                    task_type=phase_data['task_type'],
                    parallel=phase_data.get('parallel', False),
                    parallel_group=phase_data.get('parallel_group'),
                    required=phase_data.get('required', True),
                    enabled=phase_data.get('enabled', True),  # Load enabled flag
                    condition=phase_data.get('condition'),
                    timeout=phase_data.get('timeout', 300),
                    depends_on=phase_data.get('depends_on', []),
                    inputs=phase_data.get('inputs', []),
                    outputs=phase_data.get('outputs', []),
                    validation=phase_data.get('validation', {}),
                    retry_config=phase_data.get('retry_config', {})
                )
                phases.append(phase)
            
            return WorkflowDefinition(
                name=data['name'],
                version=data['version'],
                description=data['description'],
                settings=data.get('settings', {}),
                agents=data.get('agents', {}),
                phases=phases,
                conditions=data.get('conditions', {}),
                error_handling=data.get('error_handling', {}),
                output=data.get('output', {}),
                monitoring=data.get('monitoring', {})
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load workflow definition: {str(e)}")
            raise
    
    async def execute_workflow(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete workflow based on YAML definition.
        
        Args:
            initial_state: Initial workflow state (user_request, etc.)
            
        Returns:
            Final workflow state with all results
        """
        self.workflow_state = initial_state.copy()
        self.execution_context = {
            'start_time': asyncio.get_event_loop().time(),
            'current_phase': None,
            'completed_phases': [],
            'failed_phases': [],
            'parallel_groups': {}
        }
        
        self.logger.info(f"Starting workflow execution: {self.workflow_def.name}")
        
        try:
            # Execute phases in order, respecting dependencies and parallelism
            await self._execute_phases()
            
            # Finalize workflow
            await self._finalize_workflow()
            
            self.logger.info("Workflow execution completed successfully")
            return self.workflow_state
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            await self._handle_workflow_failure(e)
            raise
    
    async def _execute_phases(self):
        """Execute all phases respecting dependencies and parallelism."""
        remaining_phases = self.workflow_def.phases.copy()
        
        while remaining_phases:
            # Find phases that can be executed now
            ready_phases = self._get_ready_phases(remaining_phases)
            
            if not ready_phases:
                # Check for circular dependencies or unmet conditions
                self._handle_blocked_phases(remaining_phases)
                break
            
            # Group phases by parallel groups
            parallel_groups = self._group_parallel_phases(ready_phases)
            
            # Execute phase groups
            for group_name, phases in parallel_groups.items():
                if group_name == 'sequential':
                    # Execute sequential phases one by one
                    for phase in phases:
                        await self._execute_single_phase(phase)
                        remaining_phases.remove(phase)
                else:
                    # Execute parallel group
                    await self._execute_parallel_group(phases)
                    for phase in phases:
                        remaining_phases.remove(phase)
    
    def _get_ready_phases(self, remaining_phases: List[WorkflowPhase]) -> List[WorkflowPhase]:
        """Get phases that are ready to execute."""
        ready_phases = []
        
        for phase in remaining_phases:
            # Check if phase is enabled
            if not phase.enabled:
                self.logger.info(f"Skipping disabled phase: {phase.name}")
                # Mark as completed so dependent phases aren't blocked
                self.execution_context['completed_phases'].append(phase.name)
                continue
            
            # Check if dependencies are met
            if not self._dependencies_met(phase):
                continue
            
            # Check conditions
            if phase.condition and not self._evaluate_condition(phase.condition):
                continue
            
            ready_phases.append(phase)
        
        return ready_phases
    
    def _dependencies_met(self, phase: WorkflowPhase) -> bool:
        """Check if phase dependencies are satisfied."""
        depends_on = phase.depends_on or []
        for dep in depends_on:
            if dep not in self.execution_context['completed_phases']:
                return False
        return True
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a workflow condition."""
        if condition in self.condition_evaluators:
            return self.condition_evaluators[condition]()
        
        # Simple expression evaluation for basic conditions
        try:
            # Replace workflow_state references
            expression = condition.replace('workflow_state.', 'self.workflow_state.')
            expression = expression.replace('config.', 'self.config.')
            return eval(expression)
        except Exception as e:
            self.logger.warning(f"Failed to evaluate condition '{condition}': {str(e)}")
            return False
    
    def _group_parallel_phases(self, phases: List[WorkflowPhase]) -> Dict[str, List[WorkflowPhase]]:
        """Group phases by parallel execution groups."""
        groups = {'sequential': []}
        
        for phase in phases:
            if phase.parallel and phase.parallel_group:
                if phase.parallel_group not in groups:
                    groups[phase.parallel_group] = []
                groups[phase.parallel_group].append(phase)
            else:
                groups['sequential'].append(phase)
        
        return groups
    
    async def _execute_single_phase(self, phase: WorkflowPhase):
        """Execute a single workflow phase."""
        self.execution_context['current_phase'] = phase.name
        self.logger.info(f"Executing phase: {phase.name}")
        
        try:
            # Prepare inputs
            inputs = self._prepare_phase_inputs(phase)
            
            # Create agent task
            # Add phase name to context for phase-specific handling
            task_context = inputs.get('context', {})
            task_context['phase_name'] = phase.name
            
            task = AgentTask(
                task_type=TaskType(phase.task_type),
                prompt=inputs.get('prompt', ''),
                context=task_context,
                requirements=inputs.get('requirements', {}),
                session_id=self.workflow_state.get('session_id', 'unknown')
            )
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_agent_task(phase.agent, task),
                timeout=phase.timeout
            )
            
            # Process outputs
            self._process_phase_outputs(phase, result)
            
            # Validate results
            if not self._validate_phase_result(phase, result):
                raise Exception(f"Phase validation failed: {phase.name}")
            
            self.execution_context['completed_phases'].append(phase.name)
            self.phase_results[phase.name] = result
            
            self.logger.info(f"Phase completed successfully: {phase.name}")
            
            # Reduced delay between phases for faster execution
            await asyncio.sleep(0.2)
            
        except Exception as e:
            self.logger.error(f"Phase failed: {phase.name} - {str(e)}")
            self.execution_context['failed_phases'].append(phase.name)
            
            if phase.required:
                raise
    
    async def _execute_parallel_group(self, phases: List[WorkflowPhase]):
        """Execute a group of phases in parallel."""
        group_name = phases[0].parallel_group if phases else "unknown"
        self.logger.info(f"Executing parallel group: {group_name}")
        
        # Create tasks for all phases
        tasks = []
        for phase in phases:
            task = self._execute_single_phase(phase)
            tasks.append(task)
        
        # Execute all tasks in parallel
        try:
            await asyncio.gather(*tasks)
            # Reduced delay after parallel execution for faster performance
            await asyncio.sleep(0.5)
        except Exception as e:
            self.logger.error(f"Parallel group failed: {group_name} - {str(e)}")
            raise
    
    def _prepare_phase_inputs(self, phase: WorkflowPhase) -> Dict[str, Any]:
        """Prepare inputs for a phase based on its configuration."""
        inputs = {'prompt': '', 'context': {}, 'requirements': {}}
        
        for input_config in (phase.inputs or []):
            input_name = input_config['name']
            source = input_config.get('source', '')
            
            if source == 'user_input':
                value = self.workflow_state.get('user_request', '')
            elif source == 'workflow_state':
                value = self.workflow_state.get(input_name, '')
            elif source.startswith('workflow_state.'):
                key = source.replace('workflow_state.', '')
                value = self.workflow_state.get(key, '')
            elif 'value' in input_config:
                value = input_config['value']
            else:
                value = ''
            
            # Apply parser if specified
            if 'parser' in input_config and input_config['parser'] in self.data_parsers:
                parser = self.data_parsers[input_config['parser']]
                value = parser(value)
            
            # Set the input value
            if input_name == 'refined_requirements' or input_name in ['user_request', 'prompt']:
                inputs['prompt'] = value
            else:
                inputs['context'][input_name] = value
        
        return inputs
    
    def _process_phase_outputs(self, phase: WorkflowPhase, result: Any):
        """Process phase outputs and update workflow state."""
        for output_config in (phase.outputs or []):
            output_name = output_config['name']
            destination = output_config.get('destination', 'workflow_state')
            
            if destination == 'workflow_state':
                if hasattr(result, 'content'):
                    self.workflow_state[output_name] = result.content
                else:
                    self.workflow_state[output_name] = str(result)
            
            # Apply parser if specified
            if 'parser' in output_config and output_config['parser'] in self.data_parsers:
                parser = self.data_parsers[output_config['parser']]
                parsed_value = parser(self.workflow_state[output_name])
                self.workflow_state[output_name] = parsed_value
    
    def _validate_phase_result(self, phase: WorkflowPhase, result: Any) -> bool:
        """Validate phase result based on configuration."""
        if not phase.validation:
            return True
        
        validation = phase.validation
        content = result.content if hasattr(result, 'content') else str(result)
        
        # Debug logging for strategy_alignment
        if phase.name == "strategy_alignment":
            self.logger.info(f"=== STRATEGY ALIGNMENT DEBUG ===")
            self.logger.info(f"Content length: {len(content)}")
            self.logger.info(f"Content preview: {content[:200]}...")
            if 'required_sections' in validation:
                for section in validation['required_sections']:
                    found = section.lower() in content.lower()
                    self.logger.info(f"Section '{section}': {'FOUND' if found else 'MISSING'}")
        
        # Check minimum content length
        if 'min_content_length' in validation:
            if len(content) < validation['min_content_length']:
                self.logger.warning(f"Phase {phase.name} - Content too short: {len(content)} < {validation['min_content_length']}")
                return False
        
        # Check required elements (flexible matching)
        required_elements = validation.get('required_elements', [])
        if required_elements:
            for element in required_elements:
                # Try multiple formats for flexible matching
                element_variations = [
                    element,
                    element.upper(),
                    element.replace('_', ' ').title(),
                    element.replace('_', ' ').upper(),
                    f"## {element.upper()}",
                    f"## {element.replace('_', ' ').title()}",
                    f"# {element.upper()}",
                    f"# {element.replace('_', ' ').title()}"
                ]
                
                found = any(variation in content for variation in element_variations)
                if not found:
                    self.logger.warning(f"Phase {phase.name} - Missing required element: {element} (tried variations: {element_variations[:3]}...)")
                    return False
        
        # Check required sections
        required_sections = validation.get('required_sections', [])
        if required_sections:
            for section in required_sections:
                if section.lower() not in content.lower():
                    self.logger.warning(f"Phase {phase.name} - Missing required section: {section}")
                    return False
        
        # Check required files (for project structure validation)
        required_files = validation.get('required_files', [])
        if required_files:
            for file_name in required_files:
                # Check for structured format: ===== filename =====
                structured_pattern = f"===== {file_name} ====="
                # Also check for simple filename mention
                if structured_pattern not in content and file_name not in content:
                    self.logger.warning(f"Phase {phase.name} - Missing required file: {file_name}")
                    return False
        
        # Check required features (for feature implementation validation)
        required_features = validation.get('required_features', [])
        if required_features:
            for feature in required_features:
                if feature.lower() not in content.lower():
                    self.logger.warning(f"Phase {phase.name} - Missing required feature: {feature}")
                    return False
        
        # Check required components (for frontend validation)
        required_components = validation.get('required_components', [])
        if required_components:
            for component in required_components:
                if component not in content:
                    self.logger.warning(f"Phase {phase.name} - Missing required component: {component}")
                    return False
        
        # Check required endpoints (for API validation)
        required_endpoints = validation.get('required_endpoints', [])
        if required_endpoints:
            for endpoint in required_endpoints:
                if endpoint not in content:
                    self.logger.warning(f"Phase {phase.name} - Missing required endpoint: {endpoint}")
                    return False
        
        # Check required operations (for CRUD validation)
        required_operations = validation.get('required_operations', [])
        if required_operations:
            for operation in required_operations:
                if operation.lower() not in content.lower():
                    self.logger.warning(f"Phase {phase.name} - Missing required operation: {operation}")
                    return False
        
        # Check code quality if specified
        if validation.get('code_quality_check', False):
            if not self._basic_code_quality_check(content):
                self.logger.warning(f"Phase {phase.name} - Failed code quality check")
                return False
        
        # Check integration test if specified
        if validation.get('integration_test', False):
            if not self._basic_integration_check(content):
                self.logger.warning(f"Phase {phase.name} - Failed integration check")
                    return False
        
        return True
    
    async def _execute_agent_task(self, agent_name: str, task: AgentTask):
        """Execute a task with the specified agent."""
        if agent_name not in self.agent_map:
            raise ValueError(f"Agent '{agent_name}' not found in agent map")
        
        agent = self.agent_map[agent_name]
        return await agent.execute_task(task)
    
    def _handle_blocked_phases(self, remaining_phases: List[WorkflowPhase]):
        """Handle phases that cannot be executed due to unmet dependencies."""
        self.logger.warning(f"Blocked phases detected: {[p.name for p in remaining_phases]}")
        
        # Check for circular dependencies
        for phase in remaining_phases:
            depends_on = phase.depends_on or []
            unmet_deps = [dep for dep in depends_on 
                         if dep not in self.execution_context['completed_phases']]
            if unmet_deps:
                self.logger.warning(f"Phase {phase.name} waiting for: {unmet_deps}")
    
    async def _finalize_workflow(self):
        """Finalize workflow execution."""
        self.workflow_state['execution_summary'] = {
            'total_time': asyncio.get_event_loop().time() - self.execution_context['start_time'],
            'completed_phases': self.execution_context['completed_phases'],
            'failed_phases': self.execution_context['failed_phases'],
            'phase_count': len(self.workflow_def.phases)
        }
    
    async def _handle_workflow_failure(self, error: Exception):
        """Handle workflow failure with error recovery."""
        self.workflow_state['error'] = {
            'message': str(error),
            'type': type(error).__name__,
            'failed_phase': self.execution_context.get('current_phase'),
            'completed_phases': self.execution_context['completed_phases']
        }
    
    # Condition evaluators
    def _eval_disagreements_exist(self) -> bool:
        """Check if disagreements exist in workflow state."""
        disagreements = self.workflow_state.get('disagreements', [])
        return len(disagreements) > 0
    
    def _eval_voting_enabled(self) -> bool:
        """Check if voting is enabled and disagreements exist."""
        return self.config.enable_voting and self._eval_disagreements_exist()
    
    def _eval_tie_exists(self) -> bool:
        """Check if votes are tied."""
        votes = self.workflow_state.get('votes', {})
        if len(votes) < 2:
            return False
        
        # Simple tie detection logic
        vote_values = list(votes.values())
        return len(set(vote_values)) == len(vote_values)
    
    # Data parsers
    def _parse_disagreements(self, content: str) -> List[Dict[str, Any]]:
        """Parse disagreements from comparison text (legacy - not used in GPT-Claude workflow)."""
        disagreements = []
        if "DISAGREEMENTS" in content.upper():
            disagreements.append({
                "description": "Technical approach disagreement",
                "approach_a": "Primary approach",
                "approach_b": "Alternative approach"
            })
        return disagreements
    
    def _parse_vote(self, content: str) -> Dict[str, Any]:
        """Parse vote from agent response."""
        vote_data = {"choice": 1, "reasoning": content}
        
        if "VOTE:" in content.upper():
            lines = content.split('\n')
            for line in lines:
                if line.upper().startswith("VOTE:"):
                    try:
                        vote_data["choice"] = int(line.split(':')[1].strip())
                    except:
                        pass
        
        return vote_data
    
    def _extract_voting_options(self, disagreements: List[Dict[str, Any]]) -> List[str]:
        """Extract voting options from disagreements (legacy - not used in GPT-Claude workflow)."""
        options = []
        for disagreement in disagreements:
            options.append(disagreement.get("approach_a", ""))
            options.append(disagreement.get("approach_b", ""))
        return options
    
    def _extract_api_structure(self, backend_code: str) -> Dict[str, Any]:
        """Extract API structure from backend implementation."""
        # Simple extraction logic - in production this would be more sophisticated
        return {
            "endpoints": ["GET /api/health", "POST /api/data"],
            "models": ["User", "Project"],
            "authentication": "JWT"
        }
    
    def _basic_code_quality_check(self, content: str) -> bool:
        """Basic code quality validation."""
        try:
            # Check for basic code structure indicators
            quality_indicators = [
                'class ',  # Object-oriented structure
                'def ',    # Function definitions
                'import ', # Proper imports
                '"""',     # Documentation
                'if __name__' # Proper entry points
            ]
            
            found_indicators = sum(1 for indicator in quality_indicators if indicator in content)
            
            # Require at least 2 quality indicators for basic validation
            return found_indicators >= 2
            
        except Exception as e:
            self.logger.warning(f"Code quality check failed: {str(e)}")
            return False
    
    def _basic_integration_check(self, content: str) -> bool:
        """Basic integration validation."""
        try:
            # Check for integration-related components
            integration_indicators = [
                'docker',      # Containerization
                'config',      # Configuration
                'environment', # Environment setup
                'database',    # Database integration
                'api',         # API integration
                'cors'         # Cross-origin setup
            ]
            
            found_indicators = sum(1 for indicator in integration_indicators 
                                 if indicator.lower() in content.lower())
            
            # Require at least 3 integration indicators
            return found_indicators >= 3
            
        except Exception as e:
            self.logger.warning(f"Integration check failed: {str(e)}")
            return False