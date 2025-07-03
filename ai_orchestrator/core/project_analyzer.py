"""
Smart project analyzer that understands any type of software project.
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..agents import GPTManagerAgent, AgentTask, TaskType
from ..utils.logging_config import get_logger


class ProjectType(Enum):
    """Supported project types - can be extended."""
    WEB_APP = "web_app"
    CLI_TOOL = "cli_tool"
    API_SERVICE = "api_service"
    GAME = "game"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    BROWSER_EXTENSION = "browser_extension"
    BOT = "bot"  # Discord, Telegram, Slack, etc.
    LIBRARY = "library"
    DATA_PIPELINE = "data_pipeline"
    ML_PROJECT = "ml_project"
    SCRIPT = "script"
    MICROSERVICE = "microservice"
    PLUGIN = "plugin"
    OTHER = "other"


@dataclass
class ProjectAnalysis:
    """Complete analysis of a project request."""
    project_type: ProjectType
    project_name: str
    description: str
    components: List[str]
    tech_stack: Dict[str, str]  # {"language": "Python", "framework": "FastAPI", etc.}
    architecture: Dict[str, Any]
    features: List[str]
    constraints: List[str]
    estimated_complexity: str  # "simple", "moderate", "complex"
    suggested_phases: List[Dict[str, Any]]


class ProjectAnalyzer:
    """Analyzes user requests to understand project requirements."""
    
    def __init__(self, gpt_manager: GPTManagerAgent):
        self.gpt_manager = gpt_manager
        self.logger = get_logger("project_analyzer")
        
    async def analyze(self, user_request: str, session_id: str) -> ProjectAnalysis:
        """
        Analyze user request to understand project requirements.
        
        Returns complete project analysis including type, components, and suggested workflow.
        """
        self.logger.info(f"Analyzing project request: {user_request[:100]}...")
        
        # Use GPT Manager to analyze the request
        analysis_prompt = self._create_analysis_prompt(user_request)
        
        task = AgentTask(
            task_type=TaskType.REQUIREMENTS_REFINEMENT,
            prompt=analysis_prompt,
            context={"user_request": user_request},
            requirements={},
            session_id=session_id
        )
        
        response = await self.gpt_manager.execute_task(task)
        
        # Parse the response into structured analysis
        return self._parse_analysis_response(response.content, user_request)
    
    def _create_analysis_prompt(self, user_request: str) -> str:
        """Create prompt for project analysis."""
        return f"""
        Analyze this software project request and provide a detailed breakdown:
        
        User Request: "{user_request}"
        
        Please analyze and provide:
        
        1. **Project Type**: What kind of software is this? (web app, CLI tool, game, API, bot, etc.)
        
        2. **Project Name**: Suggest a suitable project name
        
        3. **Core Components**: List the main components needed
        
        4. **Technical Stack**: 
           - Programming language(s)
           - Framework(s) 
           - Database (if needed)
           - Other technologies
        
        5. **Architecture Overview**:
           - High-level structure
           - Key modules/services
           - Data flow
        
        6. **Required Features**: List all features mentioned or implied
        
        7. **Constraints**: Any specific requirements or limitations
        
        8. **Complexity**: Rate as simple/moderate/complex with justification
        
        9. **Development Phases**: Suggest the workflow phases needed for this project
           For each phase specify:
           - Phase name
           - Description
           - Which agent should handle it (GPT Manager for planning/review, Claude for implementation)
           - Estimated duration
           - Dependencies on other phases
        
        Format your response as a structured analysis that can be parsed.
        Be specific and comprehensive. Consider ALL aspects of the project.
        """
    
    def _parse_analysis_response(self, response: str, user_request: str) -> ProjectAnalysis:
        """Parse GPT response into structured ProjectAnalysis."""
        # This is a simplified parser - in production, use more robust parsing
        
        # Detect project type
        project_type = self._detect_project_type(response, user_request)
        
        # Extract components
        components = self._extract_components(response)
        
        # Extract tech stack
        tech_stack = self._extract_tech_stack(response)
        
        # Extract features
        features = self._extract_features(response)
        
        # Extract suggested phases
        phases = self._extract_phases(response)
        
        # Build analysis
        return ProjectAnalysis(
            project_type=project_type,
            project_name=self._extract_project_name(response, user_request),
            description=user_request,
            components=components,
            tech_stack=tech_stack,
            architecture=self._extract_architecture(response),
            features=features,
            constraints=self._extract_constraints(response),
            estimated_complexity=self._extract_complexity(response),
            suggested_phases=phases
        )
    
    def _detect_project_type(self, response: str, user_request: str) -> ProjectType:
        """Detect the project type from analysis."""
        text = (response + " " + user_request).lower()
        
        # Pattern matching for project types
        patterns = {
            ProjectType.CLI_TOOL: r'(cli|command line|terminal|console)\s*(tool|app|utility|application)',
            ProjectType.WEB_APP: r'(web|website|webapp|frontend|react|vue|angular)',
            ProjectType.API_SERVICE: r'(api|rest|graphql|backend service|microservice)',
            ProjectType.GAME: r'(game|gaming|player|level|sprite|pygame|unity)',
            ProjectType.MOBILE_APP: r'(mobile|android|ios|react native|flutter)',
            ProjectType.BOT: r'(bot|discord|telegram|slack|chatbot)',
            ProjectType.BROWSER_EXTENSION: r'(extension|chrome|firefox|browser)',
            ProjectType.DATA_PIPELINE: r'(data pipeline|etl|data processing|analytics)',
            ProjectType.ML_PROJECT: r'(machine learning|ml model|neural network|model training|ai model)',
            ProjectType.SCRIPT: r'(script|automation|scraper|utility script)'
        }
        
        for project_type, pattern in patterns.items():
            if re.search(pattern, text):
                return project_type
                
        return ProjectType.OTHER
    
    def _extract_components(self, response: str) -> List[str]:
        """Extract project components from response."""
        # Look for components section
        components = []
        
        # Simple extraction - improve with better parsing
        if "components" in response.lower():
            # Extract bullet points or numbered items after "components"
            lines = response.split('\\n')
            in_components = False
            for line in lines:
                if 'component' in line.lower() and ':' in line:
                    in_components = True
                    continue
                if in_components and line.strip().startswith(('-', '*', '•', '1', '2', '3')):
                    components.append(line.strip().lstrip('-*•123456789. '))
                elif in_components and not line.strip():
                    break
                    
        return components or ["Main Application", "Configuration", "Tests"]
    
    def _extract_tech_stack(self, response: str) -> Dict[str, str]:
        """Extract technology stack from response."""
        tech_stack = {}
        
        # Common technology patterns
        languages = re.findall(r'(Python|JavaScript|TypeScript|Java|C\\+\\+|Go|Rust|Ruby|PHP|C#)', response, re.I)
        if languages:
            tech_stack["language"] = languages[0]
            
        # Frameworks
        frameworks = re.findall(r'(React|Vue|Angular|Django|Flask|FastAPI|Express|Spring|Rails)', response, re.I)
        if frameworks:
            tech_stack["framework"] = frameworks[0]
            
        # Databases
        databases = re.findall(r'(PostgreSQL|MySQL|MongoDB|Redis|SQLite|Firebase)', response, re.I)
        if databases:
            tech_stack["database"] = databases[0]
            
        return tech_stack
    
    def _extract_features(self, response: str) -> List[str]:
        """Extract required features from response."""
        features = []
        
        # Look for features section
        lines = response.split('\\n')
        in_features = False
        for line in lines:
            if 'feature' in line.lower() and ':' in line:
                in_features = True
                continue
            if in_features and line.strip().startswith(('-', '*', '•', '1', '2', '3')):
                features.append(line.strip().lstrip('-*•123456789. '))
            elif in_features and not line.strip():
                break
                
        return features
    
    def _extract_phases(self, response: str) -> List[Dict[str, Any]]:
        """Extract suggested workflow phases from response."""
        phases = []
        
        # Look for phases section
        lines = response.split('\\n')
        in_phases = False
        current_phase = {}
        
        for line in lines:
            if 'phase' in line.lower() and any(word in line.lower() for word in ['development', 'workflow', 'step']):
                in_phases = True
                continue
                
            if in_phases:
                # Detect phase headers (numbered or bulleted)
                if re.match(r'^(\\d+\\.?|\\-|\\*)\\s*\\w+', line.strip()):
                    if current_phase:
                        phases.append(current_phase)
                    current_phase = {
                        "name": line.strip().lstrip('0123456789.-* ').split(':')[0].strip(),
                        "description": "",
                        "agent": "claude" if "implement" in line.lower() else "gpt_manager"
                    }
                elif current_phase and line.strip():
                    current_phase["description"] += line.strip() + " "
                    
        if current_phase:
            phases.append(current_phase)
            
        # If no phases found, create default based on project type
        if not phases:
            phases = self._create_default_phases(self._detect_project_type(response, ""))
            
        return phases
    
    def _create_default_phases(self, project_type: ProjectType) -> List[Dict[str, Any]]:
        """Create default phases based on project type."""
        base_phases = [
            {
                "name": "requirements_analysis",
                "description": "Analyze and refine project requirements",
                "agent": "gpt_manager"
            },
            {
                "name": "architecture_design", 
                "description": "Design system architecture and structure",
                "agent": "claude"
            }
        ]
        
        # Add type-specific phases
        if project_type == ProjectType.WEB_APP:
            base_phases.extend([
                {"name": "backend_implementation", "description": "Implement backend logic", "agent": "claude"},
                {"name": "frontend_implementation", "description": "Implement user interface", "agent": "claude"},
                {"name": "integration", "description": "Integrate all components", "agent": "claude"}
            ])
        elif project_type == ProjectType.CLI_TOOL:
            base_phases.extend([
                {"name": "core_logic", "description": "Implement core functionality", "agent": "claude"},
                {"name": "cli_interface", "description": "Build command-line interface", "agent": "claude"},
                {"name": "packaging", "description": "Package for distribution", "agent": "claude"}
            ])
        elif project_type == ProjectType.GAME:
            base_phases.extend([
                {"name": "game_engine", "description": "Set up game engine and core systems", "agent": "claude"},
                {"name": "gameplay", "description": "Implement game mechanics", "agent": "claude"},
                {"name": "assets_integration", "description": "Add graphics and sound", "agent": "claude"}
            ])
        else:
            base_phases.extend([
                {"name": "implementation", "description": "Implement core functionality", "agent": "claude"},
                {"name": "testing", "description": "Add tests and validation", "agent": "claude"}
            ])
            
        base_phases.append({
            "name": "documentation",
            "description": "Generate documentation and usage guides",
            "agent": "gpt_manager"
        })
        
        return base_phases
    
    def _extract_project_name(self, response: str, user_request: str) -> str:
        """Extract or generate project name."""
        # Try to find project name in response
        name_match = re.search(r'project\\s+name[:\\s]+([^\\n]+)', response, re.I)
        if name_match:
            return name_match.group(1).strip().strip('"\\''')
            
        # Generate from user request
        words = user_request.lower().split()
        if 'create' in words:
            idx = words.index('create')
            if idx + 2 < len(words):
                return f"{words[idx+1]}_{words[idx+2]}"
                
        return "custom_project"
    
    def _extract_architecture(self, response: str) -> Dict[str, Any]:
        """Extract architecture details from response."""
        return {
            "style": "microservices" if "microservice" in response.lower() else "monolithic",
            "layers": self._extract_components(response),
            "patterns": []  # Could extract patterns like MVC, etc.
        }
    
    def _extract_constraints(self, response: str) -> List[str]:
        """Extract project constraints from response."""
        constraints = []
        
        # Look for constraints keywords
        constraint_keywords = ['constraint', 'requirement', 'must', 'should', 'limitation']
        lines = response.split('\\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in constraint_keywords):
                constraints.append(line.strip())
                
        return constraints
    
    def _extract_complexity(self, response: str) -> str:
        """Extract complexity estimation from response."""
        if any(word in response.lower() for word in ['simple', 'basic', 'straightforward']):
            return "simple"
        elif any(word in response.lower() for word in ['complex', 'advanced', 'sophisticated']):
            return "complex"
        else:
            return "moderate"