"""
Google Gemini agent implementation with frontend expertise.
"""

import json
from typing import Dict, Any, List

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType
from ..core.config import GoogleConfig


class GeminiAgent(BaseAgent):
    """
    Google Gemini agent specialized for frontend development.
    Handles technical planning, implementation, and justification for frontend systems.
    """
    
    def __init__(self, config: GoogleConfig):
        super().__init__(config, AgentRole.FRONTEND_EXPERT)
        self.system_prompts = {
            TaskType.TECHNICAL_PLANNING: self._get_planning_prompt(),
            TaskType.IMPLEMENTATION: self._get_implementation_prompt(),
            TaskType.JUSTIFICATION: self._get_justification_prompt(),
            TaskType.VOTING: self._get_voting_prompt()
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Google API headers."""
        headers = super()._get_headers()
        return headers
    
    async def _make_api_request(self, prompt: str, **kwargs) -> str:
        """Make request to Google Gemini API."""
        task_type = kwargs.get('task_type')
        system_prompt = self._get_system_prompt(task_type)
        
        # Note: Google Gemini API structure may vary, this is a common pattern
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"System: {system_prompt}\n\nUser: {prompt}"
                }]
            }],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens
            }
        }
        
        url = f"{self.config.base_url}/models/{self.config.model_name}:generateContent"
        params = {"key": self.config.api_key} if self.config.api_key else {}
        
        response = await self.client.post(url, json=payload, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    
    def _get_system_prompt(self, task_type: TaskType = None) -> str:
        """Get system prompt based on task type."""
        if task_type and task_type in self.system_prompts:
            return self.system_prompts[task_type]
        
        return """You are a Senior Frontend Engineer with expertise in modern web development, 
        user experience design, and frontend architecture. You excel at creating intuitive, 
        performant user interfaces and can justify your technical decisions clearly."""
    
    def _format_prompt(self, task: AgentTask) -> str:
        """Format prompt based on task type."""
        if task.task_type == TaskType.TECHNICAL_PLANNING:
            return self._format_planning_prompt(task)
        elif task.task_type == TaskType.IMPLEMENTATION:
            return self._format_implementation_prompt(task)
        elif task.task_type == TaskType.JUSTIFICATION:
            return self._format_justification_prompt(task)
        elif task.task_type == TaskType.VOTING:
            return self._format_voting_prompt(task)
        else:
            return task.prompt
    
    def _format_planning_prompt(self, task: AgentTask) -> str:
        """Format technical planning prompt."""
        return f"""
        Create a comprehensive frontend technical plan for the following project:
        
        Project Brief: {task.prompt}
        
        Requirements: {json.dumps(task.requirements, indent=2)}
        Context: {json.dumps(task.context, indent=2)}
        
        IMPORTANT: Your response must include the exact phrases "ui_architecture", "framework_choice", and "user_experience" as section headers (not in markdown format, just plain text).
        
        Please provide a detailed technical plan including:
        
        1. ui_architecture
           - Application architecture pattern (SPA, MPA, SSR, etc.)
           - Component hierarchy and structure
           - State management approach
           
        2. framework_choice
           - Framework/library selection and justification
           - Core technologies (React, Vue, Angular, etc.)
           - Build tools and bundlers
           - TypeScript or JavaScript approach
           
        3. user_experience
           - Design system approach
           - Responsive design strategy
           - Accessibility considerations
           - Performance optimization strategy
        
        4. DEVELOPMENT STACK
           - CSS framework/methodology
           - Testing frameworks
           - Development tools
        
        5. API INTEGRATION
           - HTTP client configuration
           - API data management
           - Error handling and loading states
           - Real-time communication (if needed)
        
        6. PERFORMANCE OPTIMIZATION
           - Code splitting and lazy loading
           - Asset optimization
           - Caching strategies
           - Performance monitoring
        
        7. TESTING STRATEGY
           - Unit testing approach
           - Component testing
           - End-to-end testing
           - Visual regression testing
        
        8. DEPLOYMENT & BUILD
           - Build pipeline
           - Environment configuration
           - CI/CD integration
           - Hosting strategy
        
        9. DEVELOPMENT WORKFLOW
           - Development phases
           - Key milestones
           - Dependencies with backend
        
        Provide specific technology recommendations with justifications.
        
        CRITICAL: Ensure your response contains the exact text "ui_architecture", "framework_choice", and "user_experience" somewhere in the content for validation purposes.
        """
    
    def _format_implementation_prompt(self, task: AgentTask) -> str:
        """Format implementation prompt."""
        technical_plan = task.context.get('technical_plan', '')
        backend_api = task.context.get('backend_api', '')
        
        return f"""
        Implement the frontend code based on this technical plan:
        
        TECHNICAL PLAN:
        {technical_plan}
        
        BACKEND API STRUCTURE:
        {backend_api}
        
        PROJECT REQUIREMENTS:
        {task.prompt}
        
        Generate complete, production-ready frontend code including:
        
        1. PROJECT STRUCTURE
           - Organize components logically
           - Include configuration files (package.json, etc.)
           - Set up build tooling
        
        2. CORE IMPLEMENTATION
           - React/Vue/Angular components
           - State management setup
           - API integration layer
           - Routing configuration
        
        3. USER INTERFACE
           - Responsive design implementation
           - Form handling and validation
           - Loading and error states
           - Accessibility features
        
        4. STYLING
           - CSS/SCSS organization
           - Component styling
           - Responsive breakpoints
           - Theme configuration
        
        5. TESTING SETUP
           - Test configuration
           - Component test examples
           - Testing utilities
        
        6. BUILD CONFIGURATION
           - Webpack/Vite/etc. setup
           - Environment variables
           - Development scripts
        
        7. DOCUMENTATION
           - Component documentation
           - Setup and development guide
           - Deployment instructions
        
        Provide complete, runnable code with clear file organization.
        Use modern best practices for the chosen framework.
        """
    
    def _format_justification_prompt(self, task: AgentTask) -> str:
        """Format justification prompt for disagreements."""
        disagreement = task.context.get('disagreement', '')
        my_approach = task.context.get('my_approach', '')
        alternative_approach = task.context.get('alternative_approach', '')
        
        return f"""
        There is a disagreement about the following technical decision:
        
        DISAGREEMENT: {disagreement}
        
        YOUR APPROACH: {my_approach}
        
        ALTERNATIVE APPROACH: {alternative_approach}
        
        Please provide a detailed justification for your approach, addressing:
        
        1. USER EXPERIENCE BENEFITS
           - How your approach improves user experience
           - Performance and usability advantages
        
        2. TECHNICAL ADVANTAGES
           - Framework-specific benefits
           - Code maintainability and scalability
        
        3. DEVELOPMENT EFFICIENCY
           - Developer experience improvements
           - Build and deployment considerations
        
        4. COMPATIBILITY & INTEGRATION
           - Browser compatibility
           - Backend integration implications
           - Third-party service compatibility
        
        5. FUTURE MAINTENANCE
           - Long-term maintainability
           - Update and migration paths
           - Team knowledge requirements
        
        6. PERFORMANCE IMPACT
           - Bundle size implications
           - Runtime performance
           - SEO and accessibility considerations
        
        Be objective and thorough in your justification.
        """
    
    def _format_voting_prompt(self, task: AgentTask) -> str:
        """Format voting prompt."""
        options = task.context.get('voting_options', [])
        
        prompt = f"""
        Vote on the best technical approach from these options:
        
        """
        
        for i, option in enumerate(options, 1):
            prompt += f"OPTION {i}: {option}\n\n"
        
        prompt += """
        As a frontend expert, consider:
        1. User experience implications
        2. Frontend architecture impact
        3. Performance and accessibility
        4. Development and maintenance complexity
        5. Integration with backend systems
        
        Provide your vote in this format:
        VOTE: [Option Number]
        FRONTEND_REASONING: [Your detailed technical reasoning from a frontend perspective]
        """
        
        return prompt
    
    def _get_planning_prompt(self) -> str:
        """System prompt for technical planning."""
        return """You are a Senior Frontend Architect responsible for designing modern, 
        accessible, and performant user interfaces. Focus on user experience, modern frameworks, 
        performance optimization, and maintainable code architecture."""
    
    def _get_implementation_prompt(self) -> str:
        """System prompt for implementation."""
        return """You are a Senior Frontend Developer implementing production-ready applications. 
        Write clean, modern, accessible code following best practices. Focus on performance, 
        user experience, and maintainable component architecture."""
    
    def _get_justification_prompt(self) -> str:
        """System prompt for justification."""
        return """You are providing technical justification for frontend architecture decisions. 
        Consider user experience, performance, accessibility, and development efficiency. 
        Address trade-offs honestly while advocating for your approach."""
    
    def _get_voting_prompt(self) -> str:
        """System prompt for voting."""
        return """You are voting on technical approaches from a frontend perspective. 
        Consider user experience, performance, accessibility, and development complexity. 
        Make informed decisions based on technical merit and user needs."""
    
    def get_capabilities(self) -> List[TaskType]:
        """Gemini agent capabilities."""
        return [
            TaskType.TECHNICAL_PLANNING,
            TaskType.IMPLEMENTATION,
            TaskType.JUSTIFICATION,
            TaskType.VOTING
        ]