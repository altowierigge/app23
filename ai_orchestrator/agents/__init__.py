"""
AI Agents module for the orchestration system.
"""

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType, AgentResponse, MicroPhase, ValidationResult
from .gpt_agent import GPTAgent
from .claude_agent import ClaudeAgent
from .gpt_manager_agent import GPTManagerAgent
from .gpt_validator_agent import GPTValidatorAgent
from .gpt_git_agent import GPTGitAgent
from .gpt_integration_agent import GPTIntegrationAgent

__all__ = [
    'BaseAgent',
    'AgentRole',
    'AgentTask', 
    'TaskType',
    'AgentResponse',
    'MicroPhase',
    'ValidationResult',
    'GPTAgent',
    'ClaudeAgent',
    'GPTManagerAgent',
    'GPTValidatorAgent',
    'GPTGitAgent',
    'GPTIntegrationAgent'
]