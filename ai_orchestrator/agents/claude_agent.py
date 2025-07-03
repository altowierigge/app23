"""
Anthropic Claude agent implementation with backend expertise.
"""

import json
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType, MicroPhase
from ..core.config import AnthropicConfig


class ClaudeAgent(BaseAgent):
    """
    Anthropic Claude agent specialized for backend development.
    Handles technical planning, implementation, and justification for backend systems.
    """
    
    def __init__(self, config: AnthropicConfig):
        super().__init__(config, AgentRole.FULLSTACK_DEVELOPER)
        self.prompt_enhancer = None  # Will be set by coordinator if available
        self.system_prompts = {
            TaskType.TECHNICAL_PLANNING: self._get_planning_prompt(),
            TaskType.BRAINSTORMING: self._get_brainstorming_prompt(),
            TaskType.IMPLEMENTATION: self._get_implementation_prompt(),
            TaskType.JUSTIFICATION: self._get_justification_prompt(),
            TaskType.VOTING: self._get_voting_prompt(),
            # New micro-phase prompts
            TaskType.MICRO_PHASE_PLANNING: self._get_micro_phase_planning_prompt(),
            TaskType.MICRO_PHASE_IMPLEMENTATION: self._get_micro_phase_implementation_prompt()
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
        
        # Optimize temperature based on task type for better response quality
        task_temperature = self._get_task_temperature(task_type)
        
        payload = {
            "model": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "temperature": task_temperature,
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
    
    def _get_task_temperature(self, task_type: Optional[TaskType] = None) -> float:
        """Get optimized temperature based on task type for better response quality."""
        if task_type == TaskType.MICRO_PHASE_IMPLEMENTATION:
            return 0.1  # Very low for code implementation
        elif task_type == TaskType.TECHNICAL_PLANNING:
            return 0.1  # Very low for technical planning
        elif task_type in [TaskType.BRAINSTORMING, TaskType.MICRO_PHASE_PLANNING]:
            return 0.3  # Slightly higher for creative planning
        else:
            return 0.2  # Default low temperature for structured responses
    
    def _get_system_prompt(self, task_type: Optional[TaskType] = None) -> str:
        """Get system prompt based on task type."""
        if task_type and task_type in self.system_prompts:
            return self.system_prompts[task_type]
        
        return """You are an AI Software Developer capable of implementing ANY type of software in ANY language:
        - Web applications (React, Vue, Django, Rails, PHP, etc.)
        - CLI tools (Python, Rust, Go, C++, Bash, etc.)
        - Games (Unity, Pygame, JavaScript, Godot, etc.)
        - Mobile apps (React Native, Flutter, Swift, Kotlin, etc.)
        - APIs and microservices (FastAPI, Express, Spring, etc.)
        - Data processing scripts (Python, R, SQL, etc.)
        - Machine learning projects (TensorFlow, PyTorch, Scikit-learn, etc.)
        - Browser extensions (JavaScript, TypeScript, etc.)
        - Desktop applications (Electron, Qt, Tkinter, etc.)
        - Bots (Discord.py, Telegram API, Slack API, etc.)
        - And any other software project
        
        Your role is to:
        - Adapt to the project requirements without forcing unnecessary features
        - Write actual, working code (not templates)
        - Follow best practices for the chosen tech stack
        - Create complete, functional applications
        - Only add features that are actually requested or needed
        
        You work collaboratively with GPT Manager to create unified project visions and deliver high-quality software incrementally."""
    
    async def _format_prompt(self, task: AgentTask) -> str:
        """Format prompt based on task type with plan file enhancement."""
        base_prompt = None
        
        if task.task_type == TaskType.TECHNICAL_PLANNING:
            base_prompt = self._format_planning_prompt(task)
            # Enhance with brainstorming context
            if self.prompt_enhancer and 'unified_features' in task.context:
                base_prompt = await self.prompt_enhancer.enhance_architecture_prompt(
                    base_prompt, task.session_id, task.context['unified_features']
                )
        elif task.task_type == TaskType.BRAINSTORMING:
            base_prompt = self._format_brainstorming_prompt(task)
        elif task.task_type == TaskType.IMPLEMENTATION:
            base_prompt = self._format_implementation_prompt(task)
        elif task.task_type == TaskType.JUSTIFICATION:
            base_prompt = self._format_justification_prompt(task)
        elif task.task_type == TaskType.VOTING:
            base_prompt = self._format_voting_prompt(task)
        elif task.task_type == TaskType.MICRO_PHASE_PLANNING:
            base_prompt = self._format_micro_phase_planning_prompt(task)
            # Enhance with architecture plan
            if self.prompt_enhancer and 'approved_architecture' in task.context:
                base_prompt = await self.prompt_enhancer.enhance_micro_phase_planning_prompt(
                    base_prompt, task.session_id, task.context['approved_architecture']
                )
        elif task.task_type == TaskType.MICRO_PHASE_IMPLEMENTATION:
            base_prompt = self._format_micro_phase_implementation_prompt(task)
            # Enhance with implementation guide and plan files
            if self.prompt_enhancer and 'micro_phase' in task.context:
                micro_phase = task.context['micro_phase']
                implementation_guide = task.context.get('implementation_guide', {})
                base_prompt = await self.prompt_enhancer.enhance_implementation_prompt(
                    base_prompt, task.session_id, micro_phase, implementation_guide
                )
        else:
            base_prompt = task.prompt
        
        return base_prompt
    
    async def execute_task(self, task: AgentTask) -> 'AgentResponse':
        """Execute task with enhanced prompts from plan files."""
        import time
        from .base_agent import AgentResponse
        
        start_time = time.time()
        self.logger.info(f"Executing task: {task.task_type.value} (Session: {task.session_id})")
        
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Format prompt with plan file enhancement
            formatted_prompt = await self._format_prompt(task)
            
            # Make resilient API call with enhanced prompt
            response_content = await self._resilient_api_call(formatted_prompt, task)
            
            # Create successful response
            response = AgentResponse(
                content=response_content,
                task_type=task.task_type,
                agent_role=self.role,
                metadata={
                    "execution_time": time.time() - start_time,
                    "session_id": task.session_id,
                    "model": self.config.model_name,
                    "prompt_length": len(formatted_prompt),
                    "enhanced_with_plan_files": self.prompt_enhancer is not None
                },
                timestamp=time.time(),
                success=True
            )
            
            self.logger.info(f"Task completed successfully: {task.task_type.value}")
            return response
            
        except Exception as e:
            # Create error response
            error_response = AgentResponse(
                content=f"Task execution failed: {str(e)}",
                task_type=task.task_type,
                agent_role=self.role,
                metadata={
                    "execution_time": time.time() - start_time,
                    "session_id": task.session_id,
                    "error": str(e)
                },
                timestamp=time.time(),
                success=False
            )
            
            self.logger.error(f"Task failed: {task.task_type.value} - {str(e)}")
            return error_response
    
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
    
    def _format_micro_phase_planning_prompt(self, task: AgentTask) -> str:
        """Format micro-phase planning prompt."""
        approved_architecture = task.context.get('approved_architecture', '')
        unified_features = task.context.get('unified_features', '')
        
        return f"""
        Break down the approved architecture into micro-phases for implementation:
        
        APPROVED ARCHITECTURE:
        {approved_architecture}
        
        UNIFIED FEATURE LIST:
        {unified_features}
        
        PROJECT REQUIREMENTS:
        {task.prompt}
        
        Create a comprehensive micro-phase breakdown with these requirements:
        
        ## MICRO_PHASE_STRATEGY
        - Break the project into small, manageable phases
        - Each phase should be implementable in 1-3 hours
        - Phases should be logically independent where possible
        - Consider dependencies and proper sequencing
        
        ## PHASE_BREAKDOWN
        For each micro-phase, provide:
        
        ### Phase Name: [descriptive_name]
        - **Description**: What this phase implements
        - **Phase Type**: backend/frontend/database/auth/integration
        - **Files to Generate**: List of specific files to create
        - **Dependencies**: Which previous phases are required
        - **Priority**: Critical/High/Medium/Low
        - **Estimated Duration**: Time estimate in minutes
        - **Acceptance Criteria**: Specific requirements for completion
        - **Branch Name**: Git branch name for this phase
        
        ## SUGGESTED_SEQUENCE
        Recommend the optimal implementation sequence:
        1. Foundation phases (project setup, database models)
        2. Authentication and security
        3. Core business logic
        4. API endpoints
        5. Frontend components
        6. Integration and testing
        
        ## DEPENDENCY_ANALYSIS
        - Map dependencies between phases
        - Identify phases that can run in parallel
        - Highlight critical path phases
        - Suggest risk mitigation for complex dependencies
        
        ## VALIDATION_STRATEGY
        For each phase:
        - How will completion be validated?
        - What testing is required?
        - What integration checks are needed?
        - How will quality be ensured?
        
        Create a logical, implementable breakdown that enables efficient development.
        """
    
    def _format_micro_phase_implementation_prompt(self, task: AgentTask) -> str:
        """Format micro-phase implementation prompt."""
        micro_phase = task.context.get('micro_phase', {})
        previous_phases = task.context.get('previous_phases', [])
        project_architecture = task.context.get('project_architecture', '')
        
        return f"""
        Implement this specific micro-phase:
        
        MICRO-PHASE DETAILS:
        {json.dumps(micro_phase, indent=2)}
        
        PROJECT ARCHITECTURE:
        {project_architecture}
        
        PREVIOUS PHASES COMPLETED:
        {json.dumps(previous_phases, indent=2)}
        
        PROJECT REQUIREMENTS:
        {task.prompt}
        
        Generate complete, production-ready code for this micro-phase:
        
        ## IMPLEMENTATION_REQUIREMENTS
        - Generate ALL files specified in the micro-phase
        - Ensure code integrates with previous phases
        - Follow the approved architecture patterns
        - Include proper error handling and validation
        - Add necessary imports and dependencies
        
        ## CODE_GENERATION_FORMAT
        Use this exact format for each file:
        
        ===== filename.ext =====
        [Complete file content here]
        
        ## QUALITY_STANDARDS
        - Write clean, readable, well-commented code
        - Follow language-specific best practices
        - Include proper type hints/annotations
        - Implement comprehensive error handling
        - Add input validation where needed
        
        ## INTEGRATION_CONSIDERATIONS
        - Ensure compatibility with existing code
        - Maintain consistent naming conventions
        - Use established patterns from previous phases
        - Include necessary configuration updates
        
        ## TESTING_IMPLEMENTATION
        If this phase includes testing:
        - Write comprehensive unit tests
        - Include integration test stubs
        - Add test data and fixtures
        - Ensure tests cover edge cases
        
        ## FILE_COMPLETENESS
        Generate complete, runnable files that:
        - Include all necessary imports
        - Have proper function/class definitions
        - Include docstrings and comments
        - Handle errors appropriately
        - Are ready for immediate use
        
        Focus on this micro-phase only. Do not implement features from other phases.
        Ensure all acceptance criteria for this phase are met in the implementation.
        """
    
    def _get_micro_phase_planning_prompt(self) -> str:
        """System prompt for micro-phase planning."""
        return """You are a Senior Full-Stack Developer breaking down complex projects into 
        manageable micro-phases. Your expertise in both backend and frontend development allows 
        you to create logical, implementable phases that minimize dependencies and maximize 
        development efficiency. Focus on creating phases that are independently testable and 
        deployable."""
    
    def _get_micro_phase_implementation_prompt(self) -> str:
        """System prompt for micro-phase implementation."""
        return """You are a Senior Full-Stack Developer implementing specific micro-phases. 
        Generate complete, production-ready code that follows best practices and integrates 
        seamlessly with existing components. Focus on code quality, security, and maintainability. 
        Each implementation should be immediately usable and properly tested."""
    
    def get_capabilities(self) -> List[TaskType]:
        """Claude agent capabilities."""
        return [
            TaskType.TECHNICAL_PLANNING,
            TaskType.BRAINSTORMING,
            TaskType.IMPLEMENTATION,
            TaskType.JUSTIFICATION,
            TaskType.VOTING,
            TaskType.MICRO_PHASE_PLANNING,
            TaskType.MICRO_PHASE_IMPLEMENTATION
        ]
    
    async def create_micro_phases(self, architecture: Dict[str, Any], features: List[str]) -> List[MicroPhase]:
        """Create comprehensive micro-phase breakdown for complete application development."""
        
        # Generate comprehensive micro-phases covering all aspects of application development
        return [
            # Phase 1: Project Foundation
            MicroPhase(
                id="phase_001",
                name="Project Foundation",
                description="Set up basic project structure, build tools, and development environment",
                phase_type="foundation",
                files_to_generate=["package.json", "requirements.txt", "pyproject.toml", "tsconfig.json", "vite.config.ts"],
                dependencies=[],
                priority=1,
                estimated_duration=120,
                acceptance_criteria=["Project builds successfully", "Dependencies installed", "Development server runs"],
                branch_name="feature/foundation-setup",
                implementation_approach="Create modern project structure with proper tooling and configuration"
            ),
            
            # Phase 2: Database Models & Schema
            MicroPhase(
                id="phase_002", 
                name="Database Models & Schema",
                description="Implement core database models, relationships, and migration system",
                phase_type="database",
                files_to_generate=["models/user.py", "models/base.py", "models/__init__.py", "migrations/", "database.py"],
                dependencies=["phase_001"],
                priority=1,
                estimated_duration=150,
                acceptance_criteria=["Models defined", "Migrations work", "Database connects", "Relationships established"],
                branch_name="feature/database-models",
                implementation_approach="Design normalized database schema with proper relationships and constraints"
            ),
            
            # Phase 3: Authentication & Security Infrastructure
            MicroPhase(
                id="phase_003",
                name="Authentication & Security Infrastructure", 
                description="Implement JWT authentication, password hashing, role-based access control",
                phase_type="security",
                files_to_generate=["auth/jwt.py", "auth/middleware.py", "auth/decorators.py", "security/validation.py"],
                dependencies=["phase_002"],
                priority=1,
                estimated_duration=180,
                acceptance_criteria=["JWT tokens work", "Password hashing secure", "RBAC implemented", "Input validation active"],
                branch_name="feature/authentication",
                implementation_approach="Implement secure authentication with industry best practices"
            ),
            
            # Phase 4: Core API Endpoints
            MicroPhase(
                id="phase_004",
                name="Core API Endpoints",
                description="Implement RESTful API endpoints with proper error handling and validation",
                phase_type="api",
                files_to_generate=["api/users.py", "api/auth.py", "api/main.py", "schemas/", "middleware/cors.py"],
                dependencies=["phase_003"],
                priority=1,
                estimated_duration=200,
                acceptance_criteria=["All CRUD operations work", "Proper HTTP status codes", "Request validation", "Error handling"],
                branch_name="feature/api-endpoints",
                implementation_approach="Create RESTful API with OpenAPI documentation and proper status codes"
            ),
            
            # Phase 5: Business Logic Implementation
            MicroPhase(
                id="phase_005",
                name="Business Logic Implementation",
                description="Implement core application business logic and domain services",
                phase_type="business",
                files_to_generate=["services/", "utils/", "core/business_logic.py", "validators/", "processors/"],
                dependencies=["phase_004"],
                priority=1,
                estimated_duration=240,
                acceptance_criteria=["Business rules enforced", "Data processing works", "Service layer complete", "Domain logic separated"],
                branch_name="feature/business-logic",
                implementation_approach="Implement clean architecture with separated business logic and domain services"
            ),
            
            # Phase 6: Frontend Foundation & Routing
            MicroPhase(
                id="phase_006",
                name="Frontend Foundation & Routing",
                description="Set up React application structure, routing, and state management",
                phase_type="frontend",
                files_to_generate=["src/App.tsx", "src/router/", "src/store/", "src/hooks/", "src/types/"],
                dependencies=["phase_001"],
                priority=1,
                estimated_duration=160,
                acceptance_criteria=["React app runs", "Routing works", "State management setup", "TypeScript configured"],
                branch_name="feature/frontend-foundation",
                implementation_approach="Create modern React application with TypeScript, routing, and state management"
            ),
            
            # Phase 7: UI Components & Design System
            MicroPhase(
                id="phase_007",
                name="UI Components & Design System",
                description="Create reusable UI components, design system, and responsive layouts",
                phase_type="ui",
                files_to_generate=["src/components/", "src/styles/", "src/assets/", "tailwind.config.js"],
                dependencies=["phase_006"],
                priority=1,
                estimated_duration=220,
                acceptance_criteria=["Component library complete", "Responsive design works", "Design system consistent", "Accessibility features"],
                branch_name="feature/ui-components",
                implementation_approach="Build comprehensive component library with modern CSS framework and accessibility"
            ),
            
            # Phase 8: Frontend Pages & Features
            MicroPhase(
                id="phase_008",
                name="Frontend Pages & Features",
                description="Implement all application pages, forms, and user interactions",
                phase_type="frontend",
                files_to_generate=["src/pages/", "src/forms/", "src/features/", "src/layouts/"],
                dependencies=["phase_007"],
                priority=1,
                estimated_duration=250,
                acceptance_criteria=["All pages functional", "Forms validated", "User flows complete", "Navigation working"],
                branch_name="feature/frontend-pages",
                implementation_approach="Create all user-facing pages with proper form handling and user experience"
            ),
            
            # Phase 9: API Integration & Data Management
            MicroPhase(
                id="phase_009",
                name="API Integration & Data Management",
                description="Connect frontend to backend APIs with proper error handling and caching",
                phase_type="integration",
                files_to_generate=["src/api/", "src/services/", "src/hooks/api/", "src/utils/http.ts"],
                dependencies=["phase_008", "phase_004"],
                priority=1,
                estimated_duration=180,
                acceptance_criteria=["API calls work", "Error handling robust", "Loading states", "Data caching implemented"],
                branch_name="feature/api-integration",
                implementation_approach="Implement robust API layer with error handling, retries, and caching"
            ),
            
            # Phase 10: Authentication Frontend
            MicroPhase(
                id="phase_010",
                name="Authentication Frontend",
                description="Implement login, registration, and protected routes in frontend",
                phase_type="auth",
                files_to_generate=["src/auth/", "src/guards/", "src/contexts/AuthContext.tsx"],
                dependencies=["phase_009", "phase_003"],
                priority=1,
                estimated_duration=160,
                acceptance_criteria=["Login/logout works", "Protected routes", "Token management", "Session handling"],
                branch_name="feature/frontend-auth",
                implementation_approach="Create secure authentication flow with token management and route protection"
            ),
            
            # Phase 11: Unit Testing Suite
            MicroPhase(
                id="phase_011",
                name="Unit Testing Suite",
                description="Implement comprehensive unit tests for backend and frontend",
                phase_type="testing",
                files_to_generate=["tests/", "src/__tests__/", "jest.config.js", "pytest.ini"],
                dependencies=["phase_005", "phase_008"],
                priority=2,
                estimated_duration=200,
                acceptance_criteria=["80%+ test coverage", "All critical paths tested", "Tests pass consistently", "Mock strategies implemented"],
                branch_name="feature/unit-tests",
                implementation_approach="Create comprehensive test suite with high coverage and proper mocking"
            ),
            
            # Phase 12: Integration Testing
            MicroPhase(
                id="phase_012",
                name="Integration Testing",
                description="Implement API integration tests and end-to-end testing",
                phase_type="testing",
                files_to_generate=["tests/integration/", "e2e/", "cypress.config.js", "test_fixtures/"],
                dependencies=["phase_011", "phase_009"],
                priority=2,
                estimated_duration=180,
                acceptance_criteria=["API tests pass", "E2E flows tested", "Database tests work", "Test automation setup"],
                branch_name="feature/integration-tests",
                implementation_approach="Implement full integration and E2E testing with automated test runners"
            ),
            
            # Phase 13: Performance Optimization
            MicroPhase(
                id="phase_013",
                name="Performance Optimization",
                description="Optimize application performance, implement caching, and monitoring",
                phase_type="optimization",
                files_to_generate=["src/utils/performance.ts", "cache/", "monitoring/", "optimization/"],
                dependencies=["phase_010"],
                priority=2,
                estimated_duration=160,
                acceptance_criteria=["Load times optimized", "Caching implemented", "Performance monitoring", "Resource optimization"],
                branch_name="feature/performance",
                implementation_approach="Implement performance optimizations with caching, lazy loading, and monitoring"
            ),
            
            # Phase 14: Security Hardening
            MicroPhase(
                id="phase_014",
                name="Security Hardening",
                description="Implement additional security measures, HTTPS, rate limiting, and security headers",
                phase_type="security",
                files_to_generate=["security/", "middleware/security.py", "config/security.py"],
                dependencies=["phase_003"],
                priority=1,
                estimated_duration=140,
                acceptance_criteria=["HTTPS enforced", "Rate limiting active", "Security headers set", "Vulnerability tests pass"],
                branch_name="feature/security-hardening",
                implementation_approach="Implement comprehensive security measures including CORS, CSP, and rate limiting"
            ),
            
            # Phase 15: Docker & Containerization
            MicroPhase(
                id="phase_015",
                name="Docker & Containerization",
                description="Create Docker containers for development and production deployment",
                phase_type="deployment",
                files_to_generate=["Dockerfile", "docker-compose.yml", "docker-compose.prod.yml", ".dockerignore"],
                dependencies=["phase_013"],
                priority=2,
                estimated_duration=120,
                acceptance_criteria=["Containers build successfully", "Multi-stage builds", "Production optimized", "Environment variables"],
                branch_name="feature/docker",
                implementation_approach="Create optimized Docker containers with multi-stage builds and proper configurations"
            ),
            
            # Phase 16: Production Deployment & CI/CD
            MicroPhase(
                id="phase_016",
                name="Production Deployment & CI/CD",
                description="Set up production deployment pipeline with CI/CD automation",
                phase_type="deployment",
                files_to_generate=[".github/workflows/", "deploy/", "scripts/deploy.sh", "k8s/"],
                dependencies=["phase_015", "phase_012"],
                priority=2,
                estimated_duration=180,
                acceptance_criteria=["CI/CD pipeline works", "Automated deployments", "Production monitoring", "Rollback capability"],
                branch_name="feature/production-deployment",
                implementation_approach="Create automated deployment pipeline with testing, building, and production deployment"
            ),
            
            # Phase 17: Documentation & API Docs
            MicroPhase(
                id="phase_017",
                name="Documentation & API Docs",
                description="Create comprehensive documentation, API docs, and user guides",
                phase_type="documentation",
                files_to_generate=["docs/", "README.md", "API.md", "DEPLOYMENT.md", "openapi.json"],
                dependencies=["phase_016"],
                priority=2,
                estimated_duration=100,
                acceptance_criteria=["API docs complete", "User documentation", "Setup instructions", "Architecture docs"],
                branch_name="feature/documentation",
                implementation_approach="Create comprehensive documentation with API specs, user guides, and development docs"
            )
        ]