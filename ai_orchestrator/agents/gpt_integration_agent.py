"""
GPT Integration Agent - Final Assembly for micro-phase workflow.
Handles production deployment coordination and final integration.
"""

import json
from typing import Dict, Any, List

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType
from ..core.config import OpenAIConfig


class GPTIntegrationAgent(BaseAgent):
    """
    GPT Integration Agent (#4) - Final Assembly
    
    Responsibilities:
    - Multi-branch integration
    - Final build validation
    - Production readiness assessment
    - Release management
    """
    
    def __init__(self, config: OpenAIConfig):
        super().__init__(config, AgentRole.GPT_INTEGRATION_AGENT)
        self.system_prompts = {
            TaskType.INTEGRATION_VALIDATION: self._get_integration_validation_prompt(),
            TaskType.FINAL_ASSEMBLY: self._get_final_assembly_prompt()
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
            "temperature": 0.1  # Low temperature for consistent integration decisions
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
        
        return """You are the GPT Integration Agent, responsible for final assembly and production deployment. 
        Your role is to coordinate the integration of all micro-phases into a cohesive, production-ready 
        application. You ensure that all components work together seamlessly and meet production quality 
        standards. Always prioritize system stability and user experience."""
    
    def _format_prompt(self, task: AgentTask) -> str:
        """Format prompt based on task type."""
        if task.task_type == TaskType.INTEGRATION_VALIDATION:
            return self._format_integration_validation_prompt(task)
        elif task.task_type == TaskType.FINAL_ASSEMBLY:
            return self._format_final_assembly_prompt(task)
        else:
            return task.prompt
    
    def _format_integration_validation_prompt(self, task: AgentTask) -> str:
        """Format integration validation prompt."""
        completed_phases = task.context.get('completed_phases', [])
        integration_results = task.context.get('integration_results', {})
        test_results = task.context.get('test_results', {})
        performance_metrics = task.context.get('performance_metrics', {})
        
        return f"""
        Validate the integration of all completed micro-phases:
        
        COMPLETED PHASES: {json.dumps(completed_phases, indent=2)}
        
        INTEGRATION RESULTS: {json.dumps(integration_results, indent=2)}
        
        TEST RESULTS: {json.dumps(test_results, indent=2)}
        
        PERFORMANCE METRICS: {json.dumps(performance_metrics, indent=2)}
        
        Perform comprehensive integration validation covering:
        
        ## SYSTEM_INTEGRATION_ASSESSMENT
        - Do all micro-phases work together correctly?
        - Are data flows functioning as expected?
        - Are API integrations working properly?
        - Is the user experience seamless across features?
        - Are there any integration gaps or conflicts?
        
        ## FUNCTIONAL_VALIDATION
        - Are all core features working end-to-end?
        - Do user workflows complete successfully?
        - Are error handling and edge cases properly covered?
        - Is the application behavior consistent and predictable?
        - Are all acceptance criteria met across all phases?
        
        ## PERFORMANCE_VALIDATION
        - Are response times within acceptable limits?
        - Is the application scalable under load?
        - Are database queries optimized?
        - Is memory usage reasonable?
        - Are there any performance bottlenecks?
        
        ## SECURITY_VALIDATION
        - Are all security measures properly integrated?
        - Is authentication and authorization working correctly?
        - Are data validation and sanitization comprehensive?
        - Are there any security vulnerabilities in the integration?
        - Is sensitive data properly protected across all components?
        
        ## DATA_INTEGRITY_VALIDATION
        - Is data consistency maintained across all components?
        - Are database transactions working correctly?
        - Is data synchronization functioning properly?
        - Are backup and recovery procedures in place?
        - Is data migration handling correct?
        
        ## CONFIGURATION_VALIDATION
        - Are all environment configurations consistent?
        - Are feature flags working correctly?
        - Is logging and monitoring integrated properly?
        - Are error reporting systems functioning?
        - Are deployment configurations correct?
        
        ## INTEGRATION_ISSUES
        List any integration problems found:
        - Component interaction failures
        - Data flow inconsistencies
        - Performance degradation
        - Security vulnerabilities
        - Configuration conflicts
        
        ## VALIDATION_DECISION
        - READY_FOR_PRODUCTION: All integration checks pass
        - READY_WITH_MINOR_FIXES: Minor issues need addressing
        - NEEDS_SIGNIFICANT_WORK: Major integration problems exist
        - REQUIRES_ARCHITECTURE_REVIEW: Fundamental issues found
        
        ## REMEDIATION_RECOMMENDATIONS
        For any issues found:
        - Specific steps to resolve problems
        - Which phases need modification
        - Additional testing or validation needed
        - Timeline for fixes and re-validation
        
        Ensure the integrated system meets production quality standards.
        """
    
    def _format_final_assembly_prompt(self, task: AgentTask) -> str:
        """Format final assembly and release preparation prompt."""
        project_metadata = task.context.get('project_metadata', {})
        deployment_target = task.context.get('deployment_target', 'production')
        release_requirements = task.context.get('release_requirements', {})
        quality_gates = task.context.get('quality_gates', {})
        
        return f"""
        Coordinate final assembly and production release preparation:
        
        PROJECT METADATA: {json.dumps(project_metadata, indent=2)}
        
        DEPLOYMENT TARGET: {deployment_target}
        
        RELEASE REQUIREMENTS: {json.dumps(release_requirements, indent=2)}
        
        QUALITY GATES: {json.dumps(quality_gates, indent=2)}
        
        Coordinate final assembly covering:
        
        ## RELEASE_READINESS_ASSESSMENT
        - Are all micro-phases successfully integrated?
        - Have all quality gates been satisfied?
        - Are all tests passing consistently?
        - Is documentation complete and up-to-date?
        - Are all stakeholder approvals obtained?
        
        ## PRODUCTION_DEPLOYMENT_STRATEGY
        - What deployment method should be used?
        - Are there any special deployment considerations?
        - What rollback procedures are in place?
        - How should database migrations be handled?
        - What monitoring should be in place post-deployment?
        
        ## FINAL_BUILD_CONFIGURATION
        - What build settings should be used for production?
        - Are all dependencies properly pinned and secure?
        - Are environment-specific configurations correct?
        - Is asset optimization (minification, compression) applied?
        - Are debug features and verbose logging disabled?
        
        ## QUALITY_ASSURANCE_FINAL_CHECK
        - Run final comprehensive testing suite
        - Validate all user acceptance criteria
        - Perform security penetration testing
        - Execute performance and load testing
        - Verify disaster recovery procedures
        
        ## DOCUMENTATION_COMPLETENESS
        - Is user documentation complete and accurate?
        - Are API documentation and examples current?
        - Is deployment documentation comprehensive?
        - Are troubleshooting guides available?
        - Is change log and release notes prepared?
        
        ## MONITORING_AND_OBSERVABILITY
        - Are logging systems properly configured?
        - Is application performance monitoring set up?
        - Are error tracking and alerting systems active?
        - Is business metrics collection implemented?
        - Are health check endpoints functional?
        
        ## BACKUP_AND_RECOVERY
        - Are backup procedures tested and documented?
        - Is data recovery process validated?
        - Are disaster recovery plans in place?
        - Is business continuity planning complete?
        - Are rollback procedures tested?
        
        ## RELEASE_EXECUTION_PLAN
        Provide step-by-step release plan:
        
        ### Pre-Release Steps
        1. Final validation checkpoint
        2. Stakeholder notification
        3. Backup creation
        4. Deployment window scheduling
        
        ### Release Steps
        1. Deploy to staging for final validation
        2. Execute production deployment
        3. Verify deployment success
        4. Enable monitoring and alerting
        
        ### Post-Release Steps
        1. Monitor system performance
        2. Validate user experience
        3. Communicate release completion
        4. Document lessons learned
        
        ## RISK_ASSESSMENT_AND_MITIGATION
        - What are the potential risks of this release?
        - What mitigation strategies are in place?
        - What is the rollback plan if issues occur?
        - Who are the key contacts for issue resolution?
        - What are the communication protocols for incidents?
        
        ## SUCCESS_CRITERIA_VALIDATION
        - How will release success be measured?
        - What metrics indicate successful deployment?
        - What user feedback channels are available?
        - How will performance be monitored initially?
        - What constitutes a successful release milestone?
        
        ## ASSEMBLY_DECISION
        - READY_FOR_RELEASE: All criteria met, proceed with deployment
        - READY_WITH_CONDITIONS: Minor conditions must be met first
        - NOT_READY: Significant work needed before release
        - REQUIRES_REVIEW: Need additional stakeholder input
        
        ## FINAL_RECOMMENDATIONS
        - Any last-minute optimizations or improvements
        - Suggestions for future development cycles
        - Process improvements for next releases
        - Technical debt items to address post-release
        
        Ensure the final product meets all production standards and is ready for successful deployment.
        """
    
    def _get_integration_validation_prompt(self) -> str:
        """System prompt for integration validation."""
        return """You are the GPT Integration Agent specialized in system integration validation. You have 
        expertise in complex system architectures, integration patterns, and production deployment. Your role 
        is to ensure that all micro-phases work together seamlessly and meet production quality standards. 
        Focus on system-wide validation and integration integrity."""
    
    def _get_final_assembly_prompt(self) -> str:
        """System prompt for final assembly."""
        return """You are the GPT Integration Agent responsible for final assembly and release coordination. 
        You understand production deployment, release management, and quality assurance processes. Your role 
        is to ensure the final product is production-ready and meets all stakeholder requirements. Always 
        prioritize system stability, security, and user experience."""
    
    def get_capabilities(self) -> List[TaskType]:
        """GPT Integration Agent capabilities."""
        return [
            TaskType.INTEGRATION_VALIDATION,
            TaskType.FINAL_ASSEMBLY
        ]
    
    async def assess_release_readiness(self, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to assess if project is ready for release."""
        phases = project_state.get('completed_phases', [])
        tests = project_state.get('test_results', {})
        
        readiness_score = 0
        total_checks = 5
        
        # Check phase completion
        if len(phases) > 0:
            readiness_score += 1
        
        # Check test passage
        if tests.get('passing_tests', 0) > tests.get('failing_tests', 1):
            readiness_score += 1
        
        # Add more sophisticated checks here
        readiness_score += 3  # Placeholder for other checks
        
        return {
            "readiness_score": readiness_score / total_checks,
            "is_ready": readiness_score >= 4,
            "blocking_issues": [],
            "recommendations": []
        }
    
    async def create_release_plan(self, project_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to create a release execution plan."""
        return {
            "release_version": "1.0.0",
            "deployment_strategy": "blue_green",
            "rollback_plan": "immediate_rollback_on_error",
            "monitoring_checklist": [
                "Verify application startup",
                "Check database connectivity", 
                "Validate API endpoints",
                "Monitor error rates",
                "Check performance metrics"
            ],
            "success_criteria": [
                "All health checks passing",
                "Error rate < 1%",
                "Response time < 500ms",
                "User authentication working"
            ]
        }