"""
OpenAI GPT agent implementation with project management focus.
"""

import json
from typing import Dict, Any, List

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType
from ..core.config import OpenAIConfig


class GPTAgent(BaseAgent):
    """
    OpenAI GPT agent specialized for project management tasks.
    Handles requirements refinement, plan comparison, and test generation.
    """
    
    def __init__(self, config: OpenAIConfig):
        super().__init__(config, AgentRole.PROJECT_MANAGER)
        self.system_prompts = {
            TaskType.REQUIREMENTS_REFINEMENT: self._get_requirements_prompt(),
            TaskType.BRAINSTORMING: self._get_brainstorming_prompt(),
            TaskType.PLAN_COMPARISON: self._get_comparison_prompt(),
            TaskType.CONSULTATION: self._get_consultation_prompt(),
            TaskType.VOTING: self._get_voting_prompt(),
            TaskType.TESTING: self._get_testing_prompt()
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
        
        return """You are an AI Project Manager specializing in software development orchestration. 
        Your role is to manage multi-agent workflows, refine requirements, compare technical plans, 
        and make executive decisions when needed. Always provide clear, actionable responses."""
    
    def _format_prompt(self, task: AgentTask) -> str:
        """Format prompt based on task type."""
        if task.task_type == TaskType.REQUIREMENTS_REFINEMENT:
            return self._format_requirements_prompt(task)
        elif task.task_type == TaskType.BRAINSTORMING:
            return self._format_brainstorming_prompt(task)
        elif task.task_type == TaskType.TECHNICAL_PLANNING:
            return self._format_feature_breakdown_prompt(task)
        elif task.task_type == TaskType.PLAN_COMPARISON:
            return self._format_comparison_prompt(task)
        elif task.task_type == TaskType.CONSULTATION:
            return self._format_consultation_prompt(task)
        elif task.task_type == TaskType.VOTING:
            return self._format_voting_prompt(task)
        elif task.task_type == TaskType.TESTING:
            return self._format_testing_prompt(task)
        else:
            return task.prompt
    
    def _format_requirements_prompt(self, task: AgentTask) -> str:
        """Format requirements refinement prompt."""
        return f"""
        Please analyze and refine the following project requirements into a structured project brief:
        
        Original Request: {task.prompt}
        
        Context: {json.dumps(task.context, indent=2)}
        
        Please provide a detailed analysis with these REQUIRED sections:
        
        ## CORE_FEATURES
        - Essential features for the application
        - Key functionality that must be implemented
        - User-facing capabilities and interactions
        - Business logic requirements
        
        ## USER_STORIES
        - User personas and target audience
        - Specific user scenarios and workflows
        - User journey through the application
        - User value propositions
        
        ## TECHNICAL_REQUIREMENTS
        - Technology stack preferences
        - Performance and scalability needs
        - Security and compliance requirements
        - Integration and API requirements
        - Database and storage needs
        
        ## SUCCESS_CRITERIA
        - Measurable goals and KPIs
        - Acceptance criteria for features
        - Quality standards and benchmarks
        - Project completion milestones
        
        Format your response with clear headings and comprehensive details for each section.
        This will guide the technical development phases.
        """
    
    def _format_feature_breakdown_prompt(self, task: AgentTask) -> str:
        """Format feature breakdown prompt for technical planning."""
        refined_requirements = task.context.get('refined_requirements', task.prompt)
        
        return f"""
        Break down the refined requirements into specific implementable features:
        
        REFINED REQUIREMENTS:
        {refined_requirements}
        
        Please provide a detailed feature breakdown with these REQUIRED sections:
        
        ## AUTHENTICATION_FEATURES
        - User registration and login system
        - Password management and security
        - Session management and tokens
        - User profile management
        - Permission and role systems
        
        ## CORE_BUSINESS_FEATURES
        - Main application functionality
        - Data management and processing
        - Business logic operations
        - Core workflows and processes
        - Integration points and APIs
        
        ## UI_FEATURES
        - User interface components
        - Dashboard and navigation
        - Forms and data entry
        - Data visualization and reporting
        - Responsive design requirements
        
        ## API_FEATURES
        - REST API endpoints
        - Data validation and serialization
        - Authentication middleware
        - Error handling and logging
        - API documentation requirements
        
        For each feature category, specify:
        - Individual feature components
        - Implementation priority (Critical/High/Medium/Low)
        - Dependencies between features
        - Acceptance criteria for each feature
        
        This breakdown will guide the phased implementation approach.
        """
    
    def _format_brainstorming_prompt(self, task: AgentTask) -> str:
        """Format brainstorming prompt."""
        return f"""
        Lead a strategic brainstorming session for this project:
        
        Project Requirements: {task.prompt}
        
        Context: {json.dumps(task.context, indent=2)}
        
        Please provide strategic insights covering:
        
        ## MARKET_ANALYSIS
        - Target market and user segments
        - Market opportunity and size
        - Current market trends
        - User pain points this project addresses
        
        ## COMPETITIVE_ADVANTAGES
        - Unique selling propositions
        - Differentiating features
        - Competitive positioning strategy
        - Barriers to entry for competitors
        
        ## CORE_FEATURES
        - Essential features for MVP
        - Feature prioritization framework
        - User journey and key interactions
        - Technical capabilities needed
        
        Focus on strategic value and market positioning. This brainstorming will guide technical planning.
        """
    
    def _format_consultation_prompt(self, task: AgentTask) -> str:
        """Format consultation prompt for code review."""
        backend_code = task.context.get('backend_code', '')
        frontend_code = task.context.get('frontend_code', '')
        requirements = task.context.get('requirements', '')
        strategy = task.context.get('strategy', '')
        
        return f"""
        Conduct a comprehensive code review of the implemented project:
        
        PROJECT REQUIREMENTS:
        {requirements}
        
        PROJECT STRATEGY:
        {strategy}
        
        BACKEND CODE:
        {backend_code}
        
        FRONTEND CODE:
        {frontend_code}
        
        Provide a thorough code review covering:
        
        ## STRENGTHS
        - What is implemented well
        - Code quality highlights
        - Good architectural decisions
        - Proper implementation patterns
        
        ## IMPROVEMENT_AREAS
        - Code quality issues
        - Security concerns
        - Performance optimizations
        - Missing error handling
        
        ## SPECIFIC_RECOMMENDATIONS
        - Concrete improvement suggestions
        - Code refactoring opportunities
        - Additional features or enhancements
        - Best practice implementations
        
        Focus on actionable feedback that will improve the codebase.
        """
    
    def _format_comparison_prompt(self, task: AgentTask) -> str:
        """Format plan comparison prompt."""
        claude_plan = task.context.get('claude_plan', '')
        gemini_plan = task.context.get('gemini_plan', '')
        gpt_brainstorm = task.context.get('gpt_brainstorm', '')
        claude_brainstorm = task.context.get('claude_brainstorm', '')
        
        # If we have brainstorming results, this is strategy synthesis
        if gpt_brainstorm and claude_brainstorm:
            return f"""
            Synthesize the brainstorming results into a comprehensive project strategy:
            
            PROJECT REQUIREMENTS:
            {task.prompt}
            
            STRATEGIC BRAINSTORMING (GPT):
            {gpt_brainstorm}
            
            TECHNICAL BRAINSTORMING (CLAUDE):
            {claude_brainstorm}
            
            Create a unified project strategy with these sections:
            
            ## PROJECT_VISION
            - Clear vision statement for the project
            - Target audience and user value proposition
            - Long-term goals and success metrics
            - Market positioning and competitive advantage
            
            ## KEY_FEATURES
            - Essential features for the MVP
            - Core functionality prioritization
            - User experience highlights
            - Unique selling points
            
            ## TECHNICAL_DIRECTION
            - Overall technical approach
            - Architecture and technology stack decisions
            - Development methodology
            - Implementation timeline and milestones
            
            Synthesize both strategic and technical perspectives into a coherent project strategy.
            """
        
        # Otherwise, this is traditional plan comparison
        return f"""
        Compare the following technical plans from two expert agents:
        
        CLAUDE'S BACKEND PLAN:
        {claude_plan}
        
        GEMINI'S FRONTEND PLAN:
        {gemini_plan}
        
        Please analyze:
        1. Areas of agreement between the plans
        2. Conflicts or disagreements
        3. Technical trade-offs
        4. Integration concerns
        5. Specific points that need clarification
        
        Format your response with clear sections for AGREEMENTS and DISAGREEMENTS.
        For disagreements, specify exactly what needs to be resolved.
        """
    
    def _format_voting_prompt(self, task: AgentTask) -> str:
        """Format voting prompt for tie-breaking."""
        options = task.context.get('voting_options', [])
        justifications = task.context.get('justifications', {})
        
        prompt = f"""
        As the project manager, you need to cast the deciding vote between these options:
        
        """
        
        for i, option in enumerate(options, 1):
            prompt += f"OPTION {i}: {option}\n"
            if f"option_{i}" in justifications:
                prompt += f"Justification: {justifications[f'option_{i}']}\n\n"
        
        prompt += """
        Consider:
        1. Technical feasibility
        2. Project timeline impact
        3. Maintainability
        4. Risk factors
        5. Team expertise
        
        Provide your decision in this format:
        VOTE: [Option Number]
        REASONING: [Your detailed reasoning]
        """
        
        return prompt
    
    def _format_testing_prompt(self, task: AgentTask) -> str:
        """Format testing implementation prompt."""
        backend_code = task.context.get('backend_code', '')
        frontend_code = task.context.get('frontend_code', '')
        
        return f"""
        Generate comprehensive automated tests for the following implementation:
        
        BACKEND CODE:
        {backend_code}
        
        FRONTEND CODE:
        {frontend_code}
        
        Generate:
        1. Unit tests for backend components
        2. Integration tests for API endpoints
        3. Frontend component tests
        4. End-to-end test scenarios
        5. Performance test cases
        
        Use appropriate testing frameworks and follow best practices.
        Provide complete, runnable test code with setup instructions.
        """
    
    def _get_requirements_prompt(self) -> str:
        """System prompt for requirements refinement."""
        return """You are an expert Project Manager responsible for refining user requirements into 
        clear, actionable technical specifications. Focus on clarity, completeness, and technical feasibility. 
        Always ask clarifying questions when requirements are ambiguous."""
    
    def _get_brainstorming_prompt(self) -> str:
        """System prompt for brainstorming."""
        return """You are a strategic Project Manager leading brainstorming sessions. Your role is to think 
        about market positioning, competitive advantages, and core features. Always include market_analysis, 
        competitive_advantages, and core_features in your brainstorming responses."""
    
    def _get_consultation_prompt(self) -> str:
        """System prompt for consultation/code review."""
        return """You are an expert Software Architect conducting code reviews. Focus on code quality, 
        security, performance, and maintainability. Provide specific, actionable feedback that includes 
        strengths, improvement_areas, and specific_recommendations."""
    
    def _get_comparison_prompt(self) -> str:
        """System prompt for plan comparison."""
        return """You are responsible for comparing technical plans from different experts. 
        Identify conflicts objectively, understand trade-offs, and highlight integration points that need coordination. 
        Be thorough but concise in your analysis."""
    
    def _get_voting_prompt(self) -> str:
        """System prompt for voting/tie-breaking."""
        return """You are the executive decision-maker for technical disputes. 
        Make balanced decisions based on technical merit, project constraints, and risk assessment. 
        Provide clear reasoning for your decisions."""
    
    def _get_testing_prompt(self) -> str:
        """System prompt for test generation."""
        return """You are a Test Automation Expert responsible for generating comprehensive test suites. 
        Focus on test coverage, edge cases, and realistic scenarios. Generate production-ready test code 
        with proper setup and teardown procedures."""
    
    def get_capabilities(self) -> List[TaskType]:
        """GPT agent capabilities."""
        return [
            TaskType.REQUIREMENTS_REFINEMENT,
            TaskType.BRAINSTORMING,
            TaskType.PLAN_COMPARISON,
            TaskType.CONSULTATION,
            TaskType.VOTING,
            TaskType.TESTING
        ]