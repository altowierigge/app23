"""
GPT Manager Agent - Project Orchestrator for micro-phase workflow.
Handles brainstorming, architecture approval, and micro-phase coordination.
"""

import json
from typing import Dict, Any, List

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType, MicroPhase
from ..core.config import OpenAIConfig


class GPTManagerAgent(BaseAgent):
    """
    GPT Manager Agent (#1) - Project Orchestrator
    
    Responsibilities:
    - Joint brainstorming with Claude
    - Architecture review and approval
    - Micro-phase breakdown validation
    - Issue resolution and retry coordination
    - Progress monitoring
    """
    
    def __init__(self, config: OpenAIConfig):
        super().__init__(config, AgentRole.GPT_MANAGER)
        self.system_prompts = {
            TaskType.REQUIREMENTS_REFINEMENT: self._get_requirements_refinement_prompt(),
            TaskType.BRAINSTORMING: self._get_brainstorming_prompt(),
            TaskType.PLAN_COMPARISON: self._get_architecture_review_prompt(),
            TaskType.MICRO_PHASE_PLANNING: self._get_micro_phase_validation_prompt(),
            TaskType.MICRO_PHASE_VALIDATION: self._get_phase_approval_prompt(),
            TaskType.CONSULTATION: self._get_issue_resolution_prompt()
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
            "temperature": self.config.temperature
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
        
        return """You are an AI Project Manager capable of understanding and planning ANY type of software project:
        - Web applications (React, Vue, Django, Rails, etc.)
        - CLI tools (Python, Rust, Go, etc.)
        - Games (Unity, Pygame, JavaScript, etc.)
        - Mobile apps (React Native, Flutter, etc.)
        - APIs and microservices
        - Data processing scripts
        - Machine learning projects
        - Browser extensions
        - Discord/Telegram bots
        - And any other software project
        
        Your role is to:
        1. Understand what the user wants to build
        2. Identify the best approach and tech stack
        3. Plan the project structure
        4. Guide other agents in implementation
        
        You work collaboratively with Claude to create unified project visions and deliver high-quality software.
        Always provide clear, actionable decisions and maintain project momentum."""
    
    def _format_prompt(self, task: AgentTask) -> str:
        """Format prompt based on task type."""
        if task.task_type == TaskType.REQUIREMENTS_REFINEMENT:
            return self._format_requirements_refinement_prompt(task)
        elif task.task_type == TaskType.BRAINSTORMING:
            return self._format_brainstorming_prompt(task)
        elif task.task_type == TaskType.PLAN_COMPARISON:
            return self._format_architecture_review_prompt(task)
        elif task.task_type == TaskType.MICRO_PHASE_PLANNING:
            return self._format_micro_phase_validation_prompt(task)
        elif task.task_type == TaskType.MICRO_PHASE_VALIDATION:
            return self._format_phase_approval_prompt(task)
        elif task.task_type == TaskType.CONSULTATION:
            return self._format_issue_resolution_prompt(task)
        else:
            return task.prompt
    
    def _format_brainstorming_prompt(self, task: AgentTask) -> str:
        """Format joint brainstorming prompt."""
        return f"""
        Lead a strategic brainstorming session for this project with Claude:
        
        PROJECT REQUEST: {task.prompt}
        
        CONTEXT: {json.dumps(task.context, indent=2)}
        
        Your task is to collaborate with Claude to create a unified feature list and project vision.
        
        Please provide comprehensive strategic insights covering:
        
        ## FEATURE_IDEAS
        - Brainstorm all possible features for this project
        - Include both essential and nice-to-have features
        - Consider user needs and market opportunities
        - Think about scalability and future enhancements
        
        ## MARKET_POSITIONING
        - Target audience and user personas
        - Competitive landscape analysis
        - Unique value propositions
        - Market differentiation strategies
        
        ## PROJECT_VISION
        - Clear vision statement
        - Success metrics and KPIs
        - Long-term goals and roadmap
        - Business value and impact
        
        ## COLLABORATION_POINTS
        - Questions for Claude about technical implementation
        - Areas where technical input is needed
        - Integration points to discuss
        - Architecture decisions to collaborate on
        
        This brainstorming will be shared with Claude for technical input and refinement.
        Focus on strategic vision while being open to technical constraints and opportunities.
        """
    
    def _format_architecture_review_prompt(self, task: AgentTask) -> str:
        """Format architecture review and approval prompt."""
        claude_architecture = task.context.get('claude_architecture', '')
        unified_features = task.context.get('unified_features', '')
        
        return f"""
        Review and approve the architecture proposed by Claude:
        
        UNIFIED FEATURE LIST:
        {unified_features}
        
        CLAUDE'S PROPOSED ARCHITECTURE:
        {claude_architecture}
        
        As the project manager, evaluate this architecture across these dimensions:
        
        ## ARCHITECTURE_ASSESSMENT
        - Does the architecture support all required features?
        - Are the technology choices appropriate and modern?
        - Is the architecture scalable and maintainable?
        - Are there any obvious gaps or issues?
        
        ## FEASIBILITY_ANALYSIS
        - Can this be implemented within reasonable timeframes?
        - Are the technical dependencies manageable?
        - What are the potential risks and mitigation strategies?
        - Are there simpler alternatives that might work better?
        
        ## OPTIMIZATION_SUGGESTIONS
        - What improvements could be made?
        - Are there better technology choices?
        - How can we reduce complexity or risk?
        - What additional considerations should be addressed?
        
        ## APPROVAL_DECISION
        - APPROVED: Architecture is good to proceed
        - APPROVED_WITH_CHANGES: Approved with specific modifications
        - NEEDS_REVISION: Requires significant changes before approval
        
        Provide clear, actionable feedback that Claude can use to finalize the architecture.
        """
    
    def _format_micro_phase_validation_prompt(self, task: AgentTask) -> str:
        """Format micro-phase breakdown validation prompt."""
        proposed_phases = task.context.get('proposed_micro_phases', [])
        approved_architecture = task.context.get('approved_architecture', '')
        
        return f"""
        Validate the micro-phase breakdown proposed by Claude:
        
        APPROVED ARCHITECTURE:
        {approved_architecture}
        
        PROPOSED MICRO-PHASES:
        {json.dumps(proposed_phases, indent=2)}
        
        Evaluate the micro-phase breakdown for:
        
        ## LOGICAL_SEQUENCE
        - Are phases in the correct order?
        - Are dependencies properly identified?
        - Is the flow from phase to phase logical?
        - Are there any circular dependencies?
        
        ## GRANULARITY_ASSESSMENT
        - Are phases appropriately sized (not too large or small)?
        - Can each phase be completed independently?
        - Is each phase testable and deployable?
        - Are phases focused on single concerns?
        
        ## COMPLETENESS_CHECK
        - Do the phases cover all required functionality?
        - Are there any missing phases or gaps?
        - Are integration points properly addressed?
        - Is testing coverage adequate across phases?
        
        ## OPTIMIZATION_OPPORTUNITIES
        - Can any phases be combined or split?
        - Are there phases that can run in parallel?
        - How can we optimize the development sequence?
        - What risks should we mitigate?
        
        ## VALIDATION_DECISION
        - APPROVED: Proceed with this micro-phase breakdown
        - APPROVED_WITH_MODIFICATIONS: Approved with specific changes
        - NEEDS_RESTRUCTURING: Requires significant reorganization
        
        Provide specific, actionable feedback for Claude to implement.
        """
    
    def _format_phase_approval_prompt(self, task: AgentTask) -> str:
        """Format individual phase approval prompt."""
        phase_details = task.context.get('current_phase', {})
        phase_results = task.context.get('phase_results', {})
        
        return f"""
        Review the completion of micro-phase and decide on next steps:
        
        CURRENT PHASE: {json.dumps(phase_details, indent=2)}
        
        PHASE RESULTS: {json.dumps(phase_results, indent=2)}
        
        Evaluate the phase completion:
        
        ## COMPLETION_ASSESSMENT
        - Are all phase objectives met?
        - Is the code quality acceptable?
        - Are acceptance criteria satisfied?
        - Are there any obvious issues or gaps?
        
        ## INTEGRATION_READINESS
        - Is the code ready for integration?
        - Are all required files present?
        - Are interfaces properly defined?
        - Will this integrate smoothly with other phases?
        
        ## NEXT_STEPS_DECISION
        - APPROVE_AND_CONTINUE: Phase is complete, proceed to next
        - APPROVE_WITH_FIXES: Minor issues need addressing
        - REJECT_AND_RETRY: Significant issues require rework
        - PAUSE_FOR_REVIEW: Need human or additional review
        
        ## ACTION_ITEMS
        - Specific items that need to be addressed
        - Instructions for Claude if fixes are needed
        - Any process improvements for future phases
        
        Make clear decisions that keep the project moving forward efficiently.
        """
    
    def _format_issue_resolution_prompt(self, task: AgentTask) -> str:
        """Format issue resolution and retry coordination prompt."""
        issue_details = task.context.get('issue_details', {})
        failure_context = task.context.get('failure_context', {})
        previous_attempts = task.context.get('previous_attempts', [])
        
        return f"""
        Resolve issues and coordinate retry strategy:
        
        ISSUE DETAILS: {json.dumps(issue_details, indent=2)}
        
        FAILURE CONTEXT: {json.dumps(failure_context, indent=2)}
        
        PREVIOUS ATTEMPTS: {json.dumps(previous_attempts, indent=2)}
        
        Analyze the situation and provide resolution strategy:
        
        ## ISSUE_ANALYSIS
        - What exactly went wrong?
        - What are the root causes?
        - Are there patterns in the failures?
        - What external factors might be involved?
        
        ## RESOLUTION_STRATEGY
        - What specific changes are needed?
        - Should we modify the approach or requirements?
        - Are there alternative implementation paths?
        - What resources or information do we need?
        
        ## RETRY_INSTRUCTIONS
        - Clear instructions for Claude to implement
        - Modified requirements or constraints
        - Different approach or methodology
        - Success criteria for the retry attempt
        
        ## PROCESS_IMPROVEMENTS
        - How can we prevent similar issues?
        - What early warning signs should we watch for?
        - Should we adjust our validation criteria?
        - Are there process changes needed?
        
        Provide actionable guidance that gets the project back on track efficiently.
        """
    
    def _get_brainstorming_prompt(self) -> str:
        """System prompt for brainstorming."""
        return """You are the GPT Manager Agent leading strategic brainstorming sessions. Your role is to 
        think strategically about market positioning, user needs, and feature opportunities. You collaborate 
        closely with Claude to create unified project visions. Focus on strategic value while being open 
        to technical input and constraints."""
    
    def _get_architecture_review_prompt(self) -> str:
        """System prompt for architecture review."""
        return """You are the GPT Manager Agent responsible for reviewing and approving system architecture. 
        Evaluate architectures for feasibility, scalability, and alignment with project goals. Make clear 
        approval decisions with specific feedback for improvements. Balance technical excellence with 
        practical constraints."""
    
    def _get_micro_phase_validation_prompt(self) -> str:
        """System prompt for micro-phase validation."""
        return """You are the GPT Manager Agent validating micro-phase breakdowns. Ensure phases are 
        logically sequenced, appropriately sized, and complete. Focus on enabling efficient, parallel 
        development while maintaining quality and integration integrity."""
    
    def _get_phase_approval_prompt(self) -> str:
        """System prompt for phase approval."""
        return """You are the GPT Manager Agent making phase completion decisions. Evaluate whether 
        phases meet acceptance criteria and are ready for integration. Make clear decisions that 
        maintain project momentum while ensuring quality standards."""
    
    def _get_issue_resolution_prompt(self) -> str:
        """System prompt for issue resolution."""
        return """You are the GPT Manager Agent responsible for resolving development issues and 
        coordinating retries. Analyze problems systematically, provide clear resolution strategies, 
        and ensure the project gets back on track efficiently."""
    
    def _format_requirements_refinement_prompt(self, task: AgentTask) -> str:
        """Format requirements refinement prompt for adaptive workflow."""
        return f"""
        Analyze and refine the following project request to understand what the user wants to build:
        
        USER REQUEST: {task.prompt}
        
        CONTEXT: {json.dumps(task.context, indent=2)}
        
        Your task is to understand the project requirements and provide a comprehensive analysis.
        This analysis will be used to generate an appropriate workflow for ANY type of software project.
        
        Please provide:
        
        ## PROJECT_UNDERSTANDING
        - What type of software is this? (CLI tool, web app, game, bot, API, script, etc.)
        - What is the core purpose and functionality?
        - Who are the target users?
        - What problem does this solve?
        
        ## CORE_FEATURES
        - List all features mentioned or implied in the request
        - Identify essential vs. nice-to-have features
        - Consider typical features for this type of project
        - Think about user workflows and use cases
        
        ## TECHNICAL_REQUIREMENTS
        - What programming language(s) would be appropriate?
        - What frameworks or libraries might be needed?
        - Does this need a database? What kind?
        - Are there any specific technical constraints?
        - What about deployment and distribution?
        
        ## SUCCESS_CRITERIA
        - How will we know this project is successful?
        - What are the key metrics or outcomes?
        - What does "done" look like for this project?
        - Are there any quality or performance requirements?
        
        ## PROJECT_SCOPE
        - What should be included in the initial implementation?
        - What could be added in future versions?
        - Are there any explicit limitations or boundaries?
        - What should we NOT include?
        
        Focus on understanding the true intent behind the request, not forcing it into any particular template or structure.
        Be adaptive to the specific type of project being requested.
        """
    
    def _get_requirements_refinement_prompt(self) -> str:
        """System prompt for requirements refinement."""
        return """You are an AI Project Manager specialized in understanding and refining software project requirements.
        You can work with ANY type of software project - from simple scripts to complex applications.
        Your role is to deeply understand what the user wants to build and extract clear, actionable requirements
        that can guide the development process. Always adapt your analysis to the specific type of project,
        whether it's a CLI tool, web application, game, bot, or any other software."""

    def get_capabilities(self) -> List[TaskType]:
        """GPT Manager Agent capabilities."""
        return [
            TaskType.REQUIREMENTS_REFINEMENT,
            TaskType.BRAINSTORMING,
            TaskType.PLAN_COMPARISON,
            TaskType.MICRO_PHASE_PLANNING,
            TaskType.MICRO_PHASE_VALIDATION,
            TaskType.CONSULTATION
        ]