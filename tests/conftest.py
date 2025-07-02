"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from ai_orchestrator.core.config import OrchestratorConfig
from ai_orchestrator.agents.base_agent import AgentResponse, TaskType, AgentRole


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config(temp_dir):
    """Mock configuration for testing."""
    config = MagicMock(spec=OrchestratorConfig)
    config.output_dir = temp_dir
    config.workflow_config_path = str(Path(__file__).parent.parent / "workflows" / "default.yaml")
    config.debug = True
    config.log_level = "DEBUG"
    config.enable_voting = True
    config.require_consensus = True
    config.allow_tie_breaking = True
    
    # Mock API configs
    config.openai.api_key = "test-openai-key"
    config.openai.model_name = "gpt-4"
    config.openai.max_tokens = 1000
    config.openai.temperature = 0.7
    
    config.anthropic.api_key = "test-anthropic-key"
    config.anthropic.model_name = "claude-3-sonnet"
    config.anthropic.max_tokens = 1000
    config.anthropic.temperature = 0.7
    
    config.google.api_key = "test-google-key"
    config.google.model_name = "gemini-pro"
    config.google.max_tokens = 1000
    config.google.temperature = 0.7
    
    return config


@pytest.fixture
def mock_agent_response():
    """Create a mock agent response."""
    return AgentResponse(
        content="Test response content",
        task_type=TaskType.REQUIREMENTS_REFINEMENT,
        agent_role=AgentRole.PROJECT_MANAGER,
        metadata={"test": True},
        timestamp=1234567890.0,
        success=True
    )


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [{
            "message": {
                "content": "Mock GPT response for testing"
            }
        }]
    }


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    return {
        "content": [{
            "text": "Mock Claude response for testing"
        }]
    }


@pytest.fixture
def mock_google_response():
    """Mock Google API response."""
    return {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": "Mock Gemini response for testing"
                }]
            }
        }]
    }


@pytest.fixture
def sample_user_request():
    """Sample user request for testing."""
    return "Create a simple todo application with user authentication and CRUD operations"


@pytest.fixture
def sample_workflow_state():
    """Sample workflow state for testing."""
    return {
        "session_id": "test-session-123",
        "user_request": "Create a simple todo application",
        "refined_requirements": "Detailed requirements for todo app",
        "claude_plan": "Backend technical plan",
        "gemini_plan": "Frontend technical plan",
        "backend_implementation": "# Backend code here",
        "frontend_implementation": "// Frontend code here",
        "test_implementation": "# Test code here"
    }