"""
Anthropic Claude agent implementation with backend expertise.
"""

import json
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType
from ..core.config import AnthropicConfig


class ClaudeAgent(BaseAgent):
    """
    Anthropic Claude agent specialized for backend development.
    Handles technical planning, implementation, and justification for backend systems.
    """
    
    def __init__(self, config: AnthropicConfig):
        super().__init__(config, AgentRole.BACKEND_EXPERT)
        self.system_prompts = {
            TaskType.TECHNICAL_PLANNING: self._get_planning_prompt(),
            TaskType.BRAINSTORMING: self._get_brainstorming_prompt(),
            TaskType.IMPLEMENTATION: self._get_implementation_prompt(),
            TaskType.JUSTIFICATION: self._get_justification_prompt(),
            TaskType.VOTING: self._get_voting_prompt()
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Anthropic API headers."""
        headers = super()._get_headers()
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
            headers["anthropic-version"] = "2023-06-01"
        return headers
    
    async def _make_api_request(self, prompt: str, **kwargs) -> str:
        """Make request to Anthropic API."""
        task_type = kwargs.get('task_type', None)
        system_prompt = self._get_system_prompt(task_type)
        
        payload = {
            "model": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = await self.client.post(
            f"{self.config.base_url}/v1/messages",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return data["content"][0]["text"]
    
    def _get_system_prompt(self, task_type: Optional[TaskType] = None) -> str:
        """Get system prompt based on task type."""
        if task_type and task_type in self.system_prompts:
            return self.system_prompts[task_type]
        
        return """You are a Senior Backend Engineer with expertise in scalable architecture, 
        database design, API development, and system integration. You excel at designing robust, 
        maintainable backend systems and can justify your technical decisions clearly."""
    
    def _format_prompt(self, task: AgentTask) -> str:
        """Format prompt based on task type."""
        if task.task_type == TaskType.TECHNICAL_PLANNING:
            return self._format_planning_prompt(task)
        elif task.task_type == TaskType.BRAINSTORMING:
            return self._format_brainstorming_prompt(task)
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
        Create a comprehensive backend technical plan for the following project:
        
        Project Brief: {task.prompt}
        
        Requirements: {json.dumps(task.requirements, indent=2)}
        Context: {json.dumps(task.context, indent=2)}
        
        Please provide a detailed technical plan including:
        
        1. BACKEND_TECH_STACK
           - Backend framework selection and justification
           - Programming language choices
           - Runtime environment and dependencies
           - Third-party libraries and services
           - System architecture pattern (monolithic, microservices, etc.)
        
        2. FRONTEND_TECH_STACK
           - Frontend framework selection and justification
           - Client-side state management
           - UI component structure and organization
           - User interface design patterns
           - Build tools and development environment
        
        3. DATABASE_DESIGN
           - Database type selection (SQL/NoSQL)
           - Schema design and data modeling
           - Data relationships and constraints
           - Migration and versioning strategy
           - Indexing and performance optimization
        
        4. FILE_STRUCTURE
           - Project directory organization
           - Code module structure
           - Configuration file placement
           - Asset and resource organization
           - Build and deployment artifacts
        
        5. API_DESIGN
           - RESTful endpoint structure
           - Authentication and authorization strategy
           - Data validation and serialization
           - API versioning approach
           - Documentation and testing strategy
        
        6. INFRASTRUCTURE
           - Deployment architecture
           - Scalability considerations
           - Monitoring and logging
           - DevOps and CI/CD pipeline
        
        7. SECURITY
           - Security best practices
           - Data protection measures
           - Vulnerability mitigation
           - Access control implementation
        
        8. TESTING STRATEGY
           - Unit testing approach
           - Integration testing
           - Performance testing
           - Quality assurance processes
        
        9. IMPLEMENTATION_TIMELINE
           - Development phases
           - Key milestones
           - Dependencies and risks
        
        Provide specific recommendations with justifications for each section. Use the EXACT section headers shown above.
        """
    
    def _format_implementation_prompt(self, task: AgentTask) -> str:
        """Format implementation prompt based on context."""
        # Check if this is for a specific phase
        phase_name = task.context.get('phase_name', '')
        
        if 'database' in phase_name.lower():
            return self._format_database_implementation_prompt(task)
        elif 'project_foundation' in phase_name.lower():
            return self._format_foundation_implementation_prompt(task)
        elif 'auth' in phase_name.lower():
            return self._format_authentication_implementation_prompt(task)
        else:
            # Default implementation prompt
            return self._format_generic_implementation_prompt(task)
    
    def _format_foundation_implementation_prompt(self, task: AgentTask) -> str:
        """Format prompt for project foundation files."""
        technical_plan = task.context.get('technical_architecture', '')
        
        return f"""
        Create actual project files based on this technical plan:
        
        TECHNICAL PLAN:
        {technical_plan}
        
        PROJECT REQUIREMENTS:
        {task.prompt}
        
        Generate ACTUAL FILE CONTENTS with the following structure:
        
        ===== package.json =====
        {{
          "name": "project-name",
          "version": "1.0.0",
          "description": "Generated project",
          "main": "src/App.js",
          "scripts": {{
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test"
          }},
          "dependencies": {{
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-scripts": "5.0.1",
            "axios": "^1.4.0"
          }}
        }}
        
        ===== requirements.txt =====
        fastapi==0.104.1
        uvicorn==0.24.0
        pydantic==2.5.0
        sqlalchemy==2.0.23
        psycopg2-binary==2.9.9
        python-multipart==0.0.6
        python-jose[cryptography]==3.3.0
        passlib[bcrypt]==1.7.4
        
        ===== docker-compose.yml =====
        version: '3.8'
        services:
          backend:
            build: ./backend
            ports:
              - "8000:8000"
            environment:
              - DATABASE_URL=postgresql://user:password@db:5432/dbname
            depends_on:
              - db
          frontend:
            build: ./frontend
            ports:
              - "3000:3000"
            depends_on:
              - backend
          db:
            image: postgres:15
            environment:
              POSTGRES_DB: dbname
              POSTGRES_USER: user
              POSTGRES_PASSWORD: password
            volumes:
              - postgres_data:/var/lib/postgresql/data
        volumes:
          postgres_data:
        
        ===== main.py =====
        from fastapi import FastAPI, HTTPException, Depends
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI(title="Generated API", version="1.0.0")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        class Item(BaseModel):
            name: str
            description: str = None
            
        @app.get("/")
        async def root():
            return {{"message": "Hello World"}}
            
        @app.get("/health")
        async def health_check():
            return {{"status": "healthy"}}
        
        if __name__ == "__main__":
            uvicorn.run(app, host="0.0.0.0", port=8000)
        
        ===== index.html =====
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Generated App</title>
        </head>
        <body>
            <div id="root"></div>
            <script src="/static/js/bundle.js"></script>
        </body>
        </html>
        
        IMPORTANT: Use the EXACT format above with ===== filename ===== separators.
        Include all required files: package.json, requirements.txt, docker-compose.yml, main.py, index.html
        """
    
    def _format_database_implementation_prompt(self, task: AgentTask) -> str:
        """Format prompt specifically for database implementation."""
        technical_architecture = task.context.get('technical_architecture', '')
        feature_list = task.context.get('feature_list', '')
        
        return f"""
        Implement complete database models and schemas based on:
        
        TECHNICAL ARCHITECTURE:
        {technical_architecture}
        
        FEATURE LIST:
        {feature_list}
        
        PROJECT REQUIREMENTS:
        {task.prompt}
        
        Generate the following database implementation components:
        
        1. USER_MODEL - Complete user model with authentication fields
        2. MAIN_BUSINESS_MODELS - Core business entities based on the project requirements
        3. RELATIONSHIPS - Properly defined relationships between models
        4. MIGRATIONS - Database migration setup
        
        Use this format for your response:
        
        ## USER_MODEL
        ===== models/user.py =====
        [Complete user model implementation with fields like id, email, password_hash, created_at, etc.]
        
        ## MAIN_BUSINESS_MODELS
        ===== models/[model_name].py =====
        [Implementation of main business models based on requirements]
        
        ## RELATIONSHIPS
        [Explain the relationships between models]
        
        ## MIGRATIONS
        ===== alembic/env.py =====
        [Migration configuration]
        
        ===== models/__init__.py =====
        [Model exports and base configuration]
        
        Include all necessary imports, field definitions, relationships, and methods.
        Ensure models are complete and production-ready with proper validation.
        """
    
    def _format_authentication_implementation_prompt(self, task: AgentTask) -> str:
        """Format prompt specifically for authentication implementation."""
        technical_architecture = task.context.get('technical_architecture', '')
        database_implementation = task.context.get('database_implementation', '')
        
        return f"""
        Implement complete user authentication system based on:
        
        TECHNICAL ARCHITECTURE:
        {technical_architecture}
        
        DATABASE IMPLEMENTATION:
        {database_implementation}
        
        PROJECT REQUIREMENTS:
        {task.prompt}
        
        Generate the following authentication components:
        
        1. USER_REGISTRATION - Complete user registration functionality
        2. USER_LOGIN - User login with JWT tokens
        3. JWT_TOKENS - Token generation and validation
        4. PASSWORD_HASHING - Secure password handling
        5. AUTH_MIDDLEWARE - Authentication middleware for protected routes
        
        Use this format and include ALL required features:
        
        ## USER_REGISTRATION
        ===== auth/registration.py =====
        [Complete user registration implementation with validation, email verification, etc.]
        
        ## USER_LOGIN
        ===== auth/login.py =====
        [Complete login implementation with JWT token generation]
        
        ## JWT_TOKENS
        ===== auth/jwt_handler.py =====
        [JWT token creation, validation, and refresh functionality]
        
        ## PASSWORD_HASHING
        ===== auth/password.py =====
        [Secure password hashing using bcrypt or similar]
        
        ## AUTH_MIDDLEWARE
        ===== auth/middleware.py =====
        [Authentication middleware for protecting routes]
        
        ## API ENDPOINTS
        ===== routes/auth.py =====
        [Authentication API endpoints: /auth/register, /auth/login, /auth/logout]
        
        Include proper error handling, validation, and security best practices.
        Ensure all required features are clearly implemented and documented.
        """
    
    def _format_generic_implementation_prompt(self, task: AgentTask) -> str:
        """Generic implementation prompt."""
        context = task.context or {}
        
        return f"""
        Implement the following based on the requirements:
        
        PROJECT REQUIREMENTS:
        {task.prompt}
        
        CONTEXT:
        {json.dumps(context, indent=2)}
        
        Generate complete, production-ready code with proper structure and documentation.
        Use the format:
        
        ===== filename.ext =====
        [file content]
        
        Include all necessary files for a working implementation.
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
        
        1. TECHNICAL MERITS
           - Why your approach is technically superior
           - Specific advantages and benefits
        
        2. TRADE-OFF ANALYSIS
           - Acknowledge limitations of your approach
           - Compare pros and cons objectively
        
        3. RISK ASSESSMENT
           - Potential risks and mitigation strategies
           - Long-term maintenance considerations
        
        4. IMPLEMENTATION FEASIBILITY
           - Development complexity
           - Timeline and resource requirements
        
        5. SCALABILITY & PERFORMANCE
           - How your approach handles growth
           - Performance implications
        
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
        As a backend expert, consider:
        1. Backend architecture implications
        2. Database and data flow impact
        3. API design consequences
        4. Security and performance factors
        5. Development and maintenance complexity
        
        Provide your vote in this format:
        VOTE: [Option Number]
        BACKEND_REASONING: [Your detailed technical reasoning from a backend perspective]
        """
        
        return prompt
    
    def _format_brainstorming_prompt(self, task: AgentTask) -> str:
        """Format brainstorming prompt for technical insights."""
        gpt_brainstorm = task.context.get('gpt_brainstorm', '')
        
        return f"""
        Respond to this strategic brainstorming with technical insights:
        
        Project Requirements: {task.prompt}
        
        GPT's Strategic Analysis:
        {gpt_brainstorm}
        
        As a senior backend engineer, provide technical brainstorming covering:
        
        ## TECHNICAL_APPROACH
        - Backend architecture patterns that would work well
        - Technology stack recommendations
        - Database and data flow considerations
        - API design approach
        
        ## ARCHITECTURE_IDEAS  
        - System design concepts
        - Scalability patterns
        - Integration strategies
        - Performance optimization opportunities
        
        ## IMPLEMENTATION_STRATEGY
        - Development methodology recommendations
        - Key technical milestones
        - Risk mitigation through architecture
        - Testing and deployment strategies
        
        Build on the strategic vision with concrete technical insights.
        """
    
    def _get_brainstorming_prompt(self) -> str:
        """System prompt for brainstorming."""
        return """You are a Senior Backend Engineer contributing technical insights to brainstorming 
        sessions. Focus on technical_approach, architecture_ideas, and implementation_strategy. 
        Complement strategic thinking with practical technical solutions."""
    
    def _get_planning_prompt(self) -> str:
        """System prompt for technical planning."""
        return """You are a Senior Backend Architect responsible for designing scalable, 
        maintainable backend systems. Focus on best practices, security, performance, and 
        long-term maintainability. Consider modern patterns and proven technologies."""
    
    def _get_implementation_prompt(self) -> str:
        """System prompt for implementation."""
        return """You are a Senior Backend Developer implementing production-ready code. 
        Write clean, well-documented, secure code following best practices. Include proper 
        error handling, logging, and configuration management."""
    
    def _get_justification_prompt(self) -> str:
        """System prompt for justification."""
        return """You are providing technical justification for backend architecture decisions. 
        Be objective, thorough, and consider both immediate and long-term implications. 
        Address trade-offs honestly while advocating for your approach."""
    
    def _get_voting_prompt(self) -> str:
        """System prompt for voting."""
        return """You are voting on technical approaches from a backend perspective. 
        Consider architecture, scalability, maintainability, and development complexity. 
        Make informed decisions based on technical merit and project requirements."""
    
    def get_capabilities(self) -> List[TaskType]:
        """Claude agent capabilities."""
        return [
            TaskType.TECHNICAL_PLANNING,
            TaskType.BRAINSTORMING,
            TaskType.IMPLEMENTATION,
            TaskType.JUSTIFICATION,
            TaskType.VOTING
        ]