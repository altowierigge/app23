"""
AI Orchestration System

A comprehensive 2-agent collaborative workflow system that coordinates GPT and Claude
to design and implement full-stack software projects with strategic planning and code review.
"""

__version__ = "2.0.0"
__author__ = "AI Orchestration Team"
__email__ = "ai-orchestrator@example.com"

from .core.orchestrator import AIOrchestrator
from .core.config import get_config, reload_config
from .agents import GPTAgent, ClaudeAgent
from .utils.logging_config import setup_logging, get_logger
from .utils.file_manager import FileOutputManager, ProjectStructure
from .utils.git_integration import GitManager, GitHubIntegration, ProjectPublisher

__all__ = [
    'AIOrchestrator',
    'get_config',
    'reload_config',
    'GPTAgent',
    'ClaudeAgent',
    'setup_logging',
    'get_logger',
    'FileOutputManager',
    'ProjectStructure',
    'GitManager',
    'GitHubIntegration',
    'ProjectPublisher'
]