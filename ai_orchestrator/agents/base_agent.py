"""
Base agent class with resilient API calls using tenacity for retry logic.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

from ..core.config import AIModelConfig, RetryStrategy
from ..utils.process_monitor import get_process_monitor


class AgentRole(str, Enum):
    PROJECT_MANAGER_CONSULTANT = "project_manager_consultant"
    FULLSTACK_DEVELOPER = "fullstack_developer"
    # New specialized GPT roles
    GPT_MANAGER = "gpt_manager"
    GPT_VALIDATOR = "gpt_validator"
    GPT_GIT_AGENT = "gpt_git_agent"
    GPT_INTEGRATION_AGENT = "gpt_integration_agent"
    # Legacy roles (for backward compatibility)
    PROJECT_MANAGER = "project_manager"
    BACKEND_EXPERT = "backend_expert"
    FRONTEND_EXPERT = "frontend_expert"


class TaskType(str, Enum):
    REQUIREMENTS_REFINEMENT = "requirements_refinement"
    BRAINSTORMING = "brainstorming"
    TECHNICAL_PLANNING = "technical_planning"
    PLAN_COMPARISON = "plan_comparison"
    CONSULTATION = "consultation"
    JUSTIFICATION = "justification"
    VOTING = "voting"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    # New micro-phase task types
    MICRO_PHASE_PLANNING = "micro_phase_planning"
    MICRO_PHASE_VALIDATION = "micro_phase_validation"
    MICRO_PHASE_IMPLEMENTATION = "micro_phase_implementation"
    CODE_VALIDATION = "code_validation"
    STRUCTURE_VALIDATION = "structure_validation"
    GIT_OPERATION = "git_operation"
    BRANCH_MANAGEMENT = "branch_management"
    PULL_REQUEST_CREATION = "pull_request_creation"
    INTEGRATION_VALIDATION = "integration_validation"
    FINAL_ASSEMBLY = "final_assembly"


@dataclass
class AgentResponse:
    """Standardized response from an agent."""
    content: str
    task_type: TaskType
    agent_role: AgentRole
    metadata: Dict[str, Any]
    timestamp: float
    success: bool
    error_message: Optional[str] = None


@dataclass 
class AgentTask:
    """Task definition for an agent."""
    task_type: TaskType
    prompt: str
    context: Dict[str, Any]
    requirements: Dict[str, Any]
    session_id: str
    # New micro-phase fields
    micro_phase_id: Optional[str] = None
    phase_dependencies: Optional[List[str]] = None


@dataclass
class MicroPhase:
    """Micro-phase definition for granular development."""
    id: str
    name: str
    description: str
    phase_type: str  # "backend", "frontend", "database", "auth", etc.
    files_to_generate: List[str]
    dependencies: List[str]
    priority: int
    estimated_duration: int  # in minutes
    acceptance_criteria: List[str]
    branch_name: str
    implementation_approach: str = ""


@dataclass
class ValidationResult:
    """Result of code/structure validation."""
    is_valid: bool
    validation_type: str
    issues_found: List[str]
    suggestions: List[str]
    files_checked: List[str]
    metadata: Dict[str, Any]


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, requests_per_minute: int, requests_per_hour: int):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = []
        self.hour_requests = []
    
    async def acquire(self):
        """Acquire rate limit permission."""
        now = time.time()
        
        # Clean old requests
        self.minute_requests = [req_time for req_time in self.minute_requests if now - req_time < 60]
        self.hour_requests = [req_time for req_time in self.hour_requests if now - req_time < 3600]
        
        # Check limits
        if len(self.minute_requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.minute_requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        if len(self.hour_requests) >= self.requests_per_hour:
            sleep_time = 3600 - (now - self.hour_requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Record request
        self.minute_requests.append(now)
        self.hour_requests.append(now)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents with resilient API calling capabilities.
    """
    
    def __init__(self, config: AIModelConfig, role: AgentRole):
        self.config = config
        self.role = role
        self.logger = logging.getLogger(f"agent.{role.value}")
        self.rate_limiter = RateLimiter(
            config.requests_per_minute,
            config.requests_per_hour
        )
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            headers=self._get_headers()
        )
        
        # Configure retry decorator based on strategy
        self.retry_decorator = self._configure_retry()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests. Override in subclasses."""
        return {
            "Content-Type": "application/json",
            "User-Agent": f"AI-Orchestrator-{self.role.value}/1.0"
        }
    
    def _configure_retry(self):
        """Configure tenacity retry decorator based on config."""
        wait_strategy = wait_exponential(
            multiplier=self.config.base_delay,
            max=self.config.max_delay
        )
        
        if self.config.retry_strategy == RetryStrategy.FIXED:
            wait_strategy = wait_fixed(self.config.base_delay)
        elif self.config.retry_strategy == RetryStrategy.LINEAR:
            wait_strategy = wait_fixed(self.config.base_delay)
        
        return retry(
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_strategy,
            retry=retry_if_exception_type((
                httpx.HTTPError,
                httpx.TimeoutException,
                ConnectionError,
                asyncio.TimeoutError
            )),
            before_sleep=before_sleep_log(self.logger, logging.WARNING),
            after=after_log(self.logger, logging.INFO)
        )
    
    @abstractmethod
    async def _make_api_request(self, prompt: str, **kwargs) -> str:
        """Make API request to the specific AI service. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _format_prompt(self, task: AgentTask) -> str:
        """Format the prompt for the specific AI service. Must be implemented by subclasses."""
        pass
    
    async def execute_task(self, task: AgentTask) -> AgentResponse:
        """
        Execute a task with resilient API calling and structured response.
        """
        start_time = time.time()
        self.logger.info(f"Executing task: {task.task_type.value} (Session: {task.session_id})")
        
        # Get process monitor
        process_monitor = get_process_monitor()
        agent_name = self.role.value if hasattr(self.role, 'value') else str(self.role)
        
        try:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Format prompt based on task
            formatted_prompt = self._format_prompt(task)
            
            # Log agent request
            process_monitor.log_agent_request(
                session_id=task.session_id,
                agent_name=agent_name,
                prompt=formatted_prompt[:500],  # Truncate for display
                metadata={
                    "task_type": task.task_type.value,
                    "model": self.config.model_name,
                    "prompt_length": len(formatted_prompt)
                }
            )
            
            # Make resilient API call
            response_content = await self._resilient_api_call(formatted_prompt, task)
            
            # Log agent response
            process_monitor.log_agent_response(
                session_id=task.session_id,
                agent_name=agent_name,
                response=response_content[:500],  # Truncate for display
                metadata={
                    "task_type": task.task_type.value,
                    "model": self.config.model_name,
                    "response_length": len(response_content),
                    "execution_time": time.time() - start_time
                }
            )
            
            # Create successful response
            response = AgentResponse(
                content=response_content,
                task_type=task.task_type,
                agent_role=self.role,
                metadata={
                    "execution_time": time.time() - start_time,
                    "session_id": task.session_id,
                    "model": self.config.model_name,
                    "prompt_length": len(formatted_prompt)
                },
                timestamp=time.time(),
                success=True
            )
            
            self.logger.info(
                f"Task completed successfully: {task.task_type.value} "
                f"(Duration: {response.metadata['execution_time']:.2f}s)"
            )
            
            return response
            
        except Exception as e:
            # Log error to process monitor
            process_monitor.log_error(
                session_id=task.session_id,
                source=agent_name,
                error=str(e),
                metadata={
                    "task_type": task.task_type.value,
                    "model": self.config.model_name,
                    "execution_time": time.time() - start_time,
                    "error_type": type(e).__name__
                }
            )
            
            # Create error response
            self.logger.error(f"Task failed: {task.task_type.value} - {str(e)}")
            
            return AgentResponse(
                content="",
                task_type=task.task_type,
                agent_role=self.role,
                metadata={
                    "execution_time": time.time() - start_time,
                    "session_id": task.session_id,
                    "error_type": type(e).__name__
                },
                timestamp=time.time(),
                success=False,
                error_message=str(e)
            )
    
    async def _resilient_api_call(self, prompt: str, task: AgentTask) -> str:
        """
        Make a resilient API call with retry logic.
        """
        @self.retry_decorator
        async def _call():
            # Pass task_type to the API request
            kwargs = task.requirements.copy()
            kwargs['task_type'] = task.task_type
            return await self._make_api_request(prompt, **kwargs)
        
        return await _call()
    
    def get_capabilities(self) -> List[TaskType]:
        """Return list of task types this agent can handle."""
        return [
            TaskType.REQUIREMENTS_REFINEMENT,
            TaskType.TECHNICAL_PLANNING,
            TaskType.PLAN_COMPARISON,
            TaskType.JUSTIFICATION,
            TaskType.VOTING,
            TaskType.IMPLEMENTATION,
            TaskType.TESTING
        ]
    
    async def validate_response(self, response: str, task_type: TaskType) -> bool:
        """
        Validate response format based on task type.
        Override in subclasses for specific validation.
        """
        if not response or not response.strip():
            return False
        
        # Basic validation rules
        if task_type == TaskType.VOTING:
            return "vote:" in response.lower()
        elif task_type == TaskType.TECHNICAL_PLANNING:
            return len(response) > 100  # Ensure substantial planning content
        
        return True
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.client.aclose()
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(role={self.role.value}, model={self.config.model_name})"