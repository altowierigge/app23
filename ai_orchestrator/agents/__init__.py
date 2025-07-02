"""
AI Agents module for the orchestration system.
"""

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType, AgentResponse
from .gpt_agent import GPTAgent
from .claude_agent import ClaudeAgent

__all__ = [
    'BaseAgent',
    'AgentRole',
    'AgentTask', 
    'TaskType',
    'AgentResponse',
    'GPTAgent',
    'ClaudeAgent'
]