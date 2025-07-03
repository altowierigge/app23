"""
GPT Validator Agent - Quality Assurance for micro-phase workflow.
Handles code validation, structure validation, and quality control.
"""

import json
import re
from typing import Dict, Any, List

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType, ValidationResult
from ..core.config import OpenAIConfig


class GPTValidatorAgent(BaseAgent):
    """
    GPT Validator Agent (#2) - Quality Assurance
    
    Responsibilities:
    - File structure validation
    - Code completeness verification
    - Standards compliance checking
    - Integration readiness assessment
    """
    
    def __init__(self, config: OpenAIConfig):
        super().__init__(config, AgentRole.GPT_VALIDATOR)
        self.system_prompts = {
            TaskType.CODE_VALIDATION: self._get_code_validation_prompt(),
            TaskType.STRUCTURE_VALIDATION: self._get_structure_validation_prompt(),
            TaskType.INTEGRATION_VALIDATION: self._get_integration_validation_prompt()
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get OpenAI API headers."""
        headers = super()._get_headers()
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    async def _make_api_request(self, prompt: str, **kwargs) -> str:
        """Make request to OpenAI API."""
        task_type = kwargs.get('task_type')
        
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": self._get_system_prompt(task_type)},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": 0.2  # Lower temperature for validation consistency
        }
        
        response = await self.client.post(
            f"{self.config.base_url}/chat/completions",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def _get_system_prompt(self, task_type: TaskType = None) -> str:
        """Get system prompt based on task type."""
        if task_type and task_type in self.system_prompts:
            return self.system_prompts[task_type]
        
        return """You are the GPT Validator Agent, responsible for quality assurance in micro-phase development. 
        Your role is to validate code quality, file structure, and integration readiness. You ensure that each 
        micro-phase meets quality standards before it proceeds to Git operations. Always provide detailed, 
        actionable feedback with specific issues and suggestions for improvement."""
    
    def _format_prompt(self, task: AgentTask) -> str:
        """Format prompt based on task type."""
        if task.task_type == TaskType.CODE_VALIDATION:
            return self._format_code_validation_prompt(task)
        elif task.task_type == TaskType.STRUCTURE_VALIDATION:
            return self._format_structure_validation_prompt(task)
        elif task.task_type == TaskType.INTEGRATION_VALIDATION:
            return self._format_integration_validation_prompt(task)
        else:
            return task.prompt
    
    def _format_code_validation_prompt(self, task: AgentTask) -> str:
        """Format code validation prompt."""
        generated_files = task.context.get('generated_files', {})
        micro_phase = task.context.get('micro_phase', {})
        acceptance_criteria = task.context.get('acceptance_criteria', [])
        
        return f"""
        Validate the code quality and completeness for this micro-phase:
        
        MICRO-PHASE DETAILS:
        {json.dumps(micro_phase, indent=2)}
        
        ACCEPTANCE CRITERIA:
        {json.dumps(acceptance_criteria, indent=2)}
        
        GENERATED FILES:
        {json.dumps(generated_files, indent=2)}
        
        Perform comprehensive code validation covering:
        
        ## CODE_QUALITY_ASSESSMENT
        - Is the code well-structured and readable?
        - Are naming conventions consistent and clear?
        - Is the code properly commented where necessary?
        - Are there any obvious bugs or logic errors?
        - Does the code follow best practices for the language?
        
        ## COMPLETENESS_CHECK
        - Are all required files present?
        - Does each file contain the expected functionality?
        - Are all acceptance criteria addressed in the code?
        - Are error handling and edge cases covered?
        - Are necessary imports and dependencies included?
        
        ## SECURITY_REVIEW
        - Are there any security vulnerabilities?
        - Is input validation properly implemented?
        - Are authentication and authorization handled correctly?
        - Are sensitive data and credentials protected?
        - Are there any injection or XSS vulnerabilities?
        
        ## PERFORMANCE_ANALYSIS
        - Are there any obvious performance issues?
        - Is the code efficient for its intended use?
        - Are database queries optimized?
        - Are there any memory leaks or resource issues?
        - Is caching implemented where appropriate?
        
        ## MAINTAINABILITY_ASSESSMENT
        - Is the code modular and well-organized?
        - Are functions and classes appropriately sized?
        - Is the code testable and debuggable?
        - Are interfaces and contracts clear?
        - Is technical debt minimized?
        
        ## VALIDATION_RESULT
        Provide a clear validation decision:
        - PASS: Code meets all quality standards
        - PASS_WITH_MINOR_ISSUES: Acceptable with noted improvements
        - FAIL: Significant issues require fixes before proceeding
        
        ## SPECIFIC_ISSUES
        List any specific issues found with:
        - File name and line number if applicable
        - Description of the issue
        - Severity level (Critical/High/Medium/Low)
        - Suggested fix or improvement
        
        ## IMPROVEMENT_SUGGESTIONS
        Provide actionable suggestions for code improvement:
        - Specific changes to make
        - Better approaches or patterns to use
        - Additional features or safeguards to consider
        - Optimization opportunities
        
        Be thorough but practical in your validation. Focus on issues that impact functionality, 
        security, or maintainability.
        """
    
    def _format_structure_validation_prompt(self, task: AgentTask) -> str:
        """Format file structure validation prompt."""
        project_structure = task.context.get('project_structure', {})
        expected_structure = task.context.get('expected_structure', {})
        micro_phase = task.context.get('micro_phase', {})
        
        return f"""
        Validate the file and directory structure for this micro-phase:
        
        MICRO-PHASE: {json.dumps(micro_phase, indent=2)}
        
        EXPECTED STRUCTURE: {json.dumps(expected_structure, indent=2)}
        
        ACTUAL STRUCTURE: {json.dumps(project_structure, indent=2)}
        
        Perform structure validation covering:
        
        ## DIRECTORY_STRUCTURE
        - Are all required directories present?
        - Is the directory hierarchy logical and consistent?
        - Do directory names follow conventions?
        - Are there any unnecessary or misplaced directories?
        - Is the structure compatible with the chosen framework?
        
        ## FILE_ORGANIZATION
        - Are all expected files present?
        - Are files placed in appropriate directories?
        - Do file names follow naming conventions?
        - Are file extensions correct for their content?
        - Is there proper separation of concerns across files?
        
        ## CONFIGURATION_FILES
        - Are all necessary configuration files present?
        - Are package.json, requirements.txt, etc. properly configured?
        - Are environment-specific configs handled correctly?
        - Are build and deployment configs included?
        - Are IDE and tool configs appropriate?
        
        ## INTEGRATION_STRUCTURE
        - Does the structure support integration with other phases?
        - Are public interfaces clearly defined and accessible?
        - Are shared resources properly organized?
        - Will this structure work with the overall project layout?
        
        ## BEST_PRACTICES_COMPLIANCE
        - Does the structure follow framework conventions?
        - Are there industry best practices being followed?
        - Is the structure scalable for future development?
        - Are testing files properly organized?
        - Is documentation structure appropriate?
        
        ## VALIDATION_RESULT
        - PASS: Structure meets all requirements
        - PASS_WITH_SUGGESTIONS: Acceptable with recommended improvements
        - FAIL: Structure issues must be fixed
        
        ## STRUCTURAL_ISSUES
        List specific structural problems:
        - Missing files or directories
        - Incorrectly placed files
        - Naming convention violations
        - Configuration problems
        
        ## IMPROVEMENT_RECOMMENDATIONS
        - Structural improvements to make
        - Better organization approaches
        - Additional files or configs needed
        - Cleanup opportunities
        
        Focus on structure that enables smooth development and deployment.
        """
    
    def _format_integration_validation_prompt(self, task: AgentTask) -> str:
        """Format integration readiness validation prompt."""
        current_phase = task.context.get('current_phase', {})
        previous_phases = task.context.get('previous_phases', [])
        next_phases = task.context.get('next_phases', [])
        integration_points = task.context.get('integration_points', [])
        
        return f"""
        Validate integration readiness for this micro-phase:
        
        CURRENT PHASE: {json.dumps(current_phase, indent=2)}
        
        PREVIOUS PHASES: {json.dumps(previous_phases, indent=2)}
        
        NEXT PHASES: {json.dumps(next_phases, indent=2)}
        
        INTEGRATION POINTS: {json.dumps(integration_points, indent=2)}
        
        Assess integration readiness across:
        
        ## INTERFACE_COMPATIBILITY
        - Are all required interfaces properly defined?
        - Do APIs match expected contracts?
        - Are data formats consistent across phases?
        - Are communication protocols properly implemented?
        - Are version compatibilities maintained?
        
        ## DEPENDENCY_VALIDATION
        - Are all dependencies properly declared?
        - Are dependency versions compatible?
        - Are circular dependencies avoided?
        - Are external service dependencies handled?
        - Are database schema changes compatible?
        
        ## DATA_FLOW_VALIDATION
        - Is data flow between phases correct?
        - Are data transformations properly handled?
        - Are data validation rules consistent?
        - Is data persistence handled correctly?
        - Are data migration needs addressed?
        
        ## API_CONTRACT_VALIDATION
        - Are REST API endpoints properly defined?
        - Are request/response formats correct?
        - Is authentication/authorization integrated?
        - Are error responses standardized?
        - Is API documentation accurate?
        
        ## CONFIGURATION_INTEGRATION
        - Are environment configurations compatible?
        - Are shared configurations properly referenced?
        - Are secrets and credentials handled consistently?
        - Are feature flags integrated correctly?
        - Are logging and monitoring integrated?
        
        ## TESTING_INTEGRATION
        - Are integration test points defined?
        - Can this phase be tested in isolation?
        - Are mock/stub interfaces available?
        - Are test data requirements clear?
        - Are testing environments compatible?
        
        ## INTEGRATION_READINESS
        - READY: Phase is ready for integration
        - READY_WITH_NOTES: Ready with specific integration notes
        - NOT_READY: Integration issues must be resolved
        
        ## INTEGRATION_ISSUES
        List specific integration problems:
        - Interface mismatches
        - Dependency conflicts  
        - Data flow problems
        - Configuration issues
        
        ## INTEGRATION_RECOMMENDATIONS
        - Changes needed for smooth integration
        - Additional interfaces or adapters needed
        - Configuration adjustments required
        - Testing strategy recommendations
        
        Ensure this phase will integrate smoothly with the rest of the system.
        """
    
    def _get_code_validation_prompt(self) -> str:
        """System prompt for code validation."""
        return """You are the GPT Validator Agent specialized in code quality validation. Your role is to 
        thoroughly assess code for quality, completeness, security, and maintainability. You have expertise 
        in multiple programming languages and frameworks. Always provide specific, actionable feedback that 
        helps improve code quality and prevents issues in production."""
    
    def _get_structure_validation_prompt(self) -> str:
        """System prompt for structure validation."""
        return """You are the GPT Validator Agent specialized in project structure validation. You understand 
        best practices for organizing code across different frameworks and technologies. Your role is to ensure 
        that file and directory structures support maintainable, scalable development and follow industry 
        conventions."""
    
    def _get_integration_validation_prompt(self) -> str:
        """System prompt for integration validation."""
        return """You are the GPT Validator Agent specialized in integration validation. Your role is to ensure 
        that micro-phases will integrate smoothly with each other and the overall system. You understand APIs, 
        data flow, dependencies, and the challenges of modular development. Focus on preventing integration 
        issues before they occur."""
    
    def get_capabilities(self) -> List[TaskType]:
        """GPT Validator Agent capabilities."""
        return [
            TaskType.CODE_VALIDATION,
            TaskType.STRUCTURE_VALIDATION,
            TaskType.INTEGRATION_VALIDATION
        ]
    
    async def validate_code_files(self, files: Dict[str, str], criteria: List[str]) -> ValidationResult:
        """Helper method to validate code files against criteria."""
        issues = []
        suggestions = []
        
        for file_path, content in files.items():
            # Basic validation checks
            if not content.strip():
                issues.append(f"{file_path}: File is empty")
                continue
            
            # Check for common issues
            if "TODO" in content or "FIXME" in content:
                issues.append(f"{file_path}: Contains TODO/FIXME comments")
            
            # Check for basic syntax (simplified)
            if file_path.endswith('.py'):
                if 'import ' not in content and 'from ' not in content:
                    suggestions.append(f"{file_path}: Consider adding necessary imports")
            
            if file_path.endswith('.js') or file_path.endswith('.jsx'):
                if 'export' not in content:
                    suggestions.append(f"{file_path}: Consider adding proper exports")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            validation_type="code_validation",
            issues_found=issues,
            suggestions=suggestions,
            files_checked=list(files.keys()),
            metadata={"criteria_checked": criteria}
        )