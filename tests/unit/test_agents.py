"""
Unit tests for AI agents.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from ai_orchestrator.agents.base_agent import BaseAgent, AgentTask, TaskType, AgentRole
from ai_orchestrator.agents.gpt_agent import GPTAgent
from ai_orchestrator.agents.claude_agent import ClaudeAgent
from ai_orchestrator.agents.gemini_agent import GeminiAgent
from ai_orchestrator.core.config import OpenAIConfig, AnthropicConfig, GoogleConfig


class MockAgent(BaseAgent):
    """Mock agent for testing base functionality."""
    
    async def _make_api_request(self, prompt: str, **kwargs) -> str:
        return f"Mock response for: {prompt}"
    
    def _format_prompt(self, task: AgentTask) -> str:
        return f"Formatted: {task.prompt}"


class TestBaseAgent:
    """Test BaseAgent class."""
    
    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.max_tokens = 1000
        config.temperature = 0.7
        config.timeout = 60
        config.max_retries = 3
        config.retry_strategy = "exponential"
        config.base_delay = 1.0
        config.max_delay = 60.0
        config.requests_per_minute = 60
        config.requests_per_hour = 1000
        return config
    
    @pytest.fixture
    def mock_agent(self, mock_config):
        return MockAgent(mock_config, AgentRole.PROJECT_MANAGER)
    
    @pytest.mark.asyncio
    async def test_execute_task_success(self, mock_agent):
        """Test successful task execution."""
        task = AgentTask(
            task_type=TaskType.REQUIREMENTS_REFINEMENT,
            prompt="Test prompt",
            context={},
            requirements={},
            session_id="test-session"
        )
        
        response = await mock_agent.execute_task(task)
        
        assert response.success == True
        assert response.task_type == TaskType.REQUIREMENTS_REFINEMENT
        assert response.agent_role == AgentRole.PROJECT_MANAGER
        assert "Mock response" in response.content
    
    @pytest.mark.asyncio
    async def test_execute_task_failure(self, mock_agent):
        """Test task execution failure."""
        # Mock the API request to raise an exception
        mock_agent._make_api_request = AsyncMock(side_effect=Exception("API Error"))
        
        task = AgentTask(
            task_type=TaskType.REQUIREMENTS_REFINEMENT,
            prompt="Test prompt",
            context={},
            requirements={},
            session_id="test-session"
        )
        
        response = await mock_agent.execute_task(task)
        
        assert response.success == False
        assert response.error_message == "API Error"
    
    def test_get_capabilities(self, mock_agent):
        """Test agent capabilities."""
        capabilities = mock_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert TaskType.REQUIREMENTS_REFINEMENT in capabilities
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_agent):
        """Test rate limiting functionality."""
        # Rate limiter should allow requests within limits
        await mock_agent.rate_limiter.acquire()
        # Should not raise an exception
    
    @pytest.mark.asyncio
    async def test_cleanup(self, mock_agent):
        """Test resource cleanup."""
        await mock_agent.cleanup()
        # Should not raise an exception


class TestGPTAgent:
    """Test GPTAgent class."""
    
    @pytest.fixture
    def openai_config(self):
        config = MagicMock(spec=OpenAIConfig)
        config.api_key = "test-openai-key"
        config.model_name = "gpt-4"
        config.base_url = "https://api.openai.com/v1"
        config.max_tokens = 1000
        config.temperature = 0.7
        config.timeout = 60
        config.max_retries = 3
        config.retry_strategy = "exponential"
        config.base_delay = 1.0
        config.max_delay = 60.0
        config.requests_per_minute = 500
        config.requests_per_hour = 10000
        return config
    
    @pytest.fixture
    def gpt_agent(self, openai_config):
        return GPTAgent(openai_config)
    
    def test_initialization(self, gpt_agent):
        """Test GPT agent initialization."""
        assert gpt_agent.role == AgentRole.PROJECT_MANAGER
        assert TaskType.REQUIREMENTS_REFINEMENT in gpt_agent.get_capabilities()
        assert TaskType.PLAN_COMPARISON in gpt_agent.get_capabilities()
        assert TaskType.VOTING in gpt_agent.get_capabilities()
        assert TaskType.TESTING in gpt_agent.get_capabilities()
    
    def test_headers(self, gpt_agent):
        """Test API headers generation."""
        headers = gpt_agent._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-openai-key"
        assert headers["Content-Type"] == "application/json"
    
    def test_system_prompt_selection(self, gpt_agent):
        """Test system prompt selection based on task type."""
        requirements_prompt = gpt_agent._get_system_prompt(TaskType.REQUIREMENTS_REFINEMENT)
        comparison_prompt = gpt_agent._get_system_prompt(TaskType.PLAN_COMPARISON)
        
        assert "requirements" in requirements_prompt.lower()
        assert "comparison" in comparison_prompt.lower()
        assert requirements_prompt != comparison_prompt
    
    @pytest.mark.asyncio
    async def test_api_request_format(self, gpt_agent, mock_openai_response):
        """Test API request formatting."""
        with patch.object(gpt_agent.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_openai_response
            mock_post.return_value = mock_response
            
            result = await gpt_agent._make_api_request(
                "test prompt", 
                task_type=TaskType.REQUIREMENTS_REFINEMENT
            )
            
            assert result == "Mock GPT response for testing"
            mock_post.assert_called_once()
            
            # Check the request payload
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['model'] == 'gpt-4'
            assert len(payload['messages']) == 2
            assert payload['messages'][1]['content'] == 'test prompt'


class TestClaudeAgent:
    """Test ClaudeAgent class."""
    
    @pytest.fixture
    def anthropic_config(self):
        config = MagicMock(spec=AnthropicConfig)
        config.api_key = "test-anthropic-key"
        config.model_name = "claude-3-sonnet"
        config.base_url = "https://api.anthropic.com"
        config.max_tokens = 1000
        config.temperature = 0.7
        config.timeout = 60
        config.max_retries = 3
        config.retry_strategy = "exponential"
        config.base_delay = 1.0
        config.max_delay = 60.0
        config.requests_per_minute = 50
        config.requests_per_hour = 1000
        return config
    
    @pytest.fixture
    def claude_agent(self, anthropic_config):
        return ClaudeAgent(anthropic_config)
    
    def test_initialization(self, claude_agent):
        """Test Claude agent initialization."""
        assert claude_agent.role == AgentRole.BACKEND_EXPERT
        assert TaskType.TECHNICAL_PLANNING in claude_agent.get_capabilities()
        assert TaskType.IMPLEMENTATION in claude_agent.get_capabilities()
    
    def test_headers(self, claude_agent):
        """Test API headers generation."""
        headers = claude_agent._get_headers()
        assert "x-api-key" in headers
        assert headers["x-api-key"] == "test-anthropic-key"
        assert "anthropic-version" in headers
    
    @pytest.mark.asyncio
    async def test_api_request_format(self, claude_agent, mock_anthropic_response):
        """Test API request formatting."""
        with patch.object(claude_agent.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_anthropic_response
            mock_post.return_value = mock_response
            
            result = await claude_agent._make_api_request(
                "test prompt",
                task_type=TaskType.TECHNICAL_PLANNING
            )
            
            assert result == "Mock Claude response for testing"
            mock_post.assert_called_once()


class TestGeminiAgent:
    """Test GeminiAgent class."""
    
    @pytest.fixture
    def google_config(self):
        config = MagicMock(spec=GoogleConfig)
        config.api_key = "test-google-key"
        config.model_name = "gemini-pro"
        config.base_url = "https://generativelanguage.googleapis.com/v1beta"
        config.max_tokens = 1000
        config.temperature = 0.7
        config.timeout = 60
        config.max_retries = 3
        config.retry_strategy = "exponential"
        config.base_delay = 1.0
        config.max_delay = 60.0
        config.requests_per_minute = 60
        config.requests_per_hour = 1000
        return config
    
    @pytest.fixture
    def gemini_agent(self, google_config):
        return GeminiAgent(google_config)
    
    def test_initialization(self, gemini_agent):
        """Test Gemini agent initialization."""
        assert gemini_agent.role == AgentRole.FRONTEND_EXPERT
        assert TaskType.TECHNICAL_PLANNING in gemini_agent.get_capabilities()
        assert TaskType.IMPLEMENTATION in gemini_agent.get_capabilities()
    
    @pytest.mark.asyncio
    async def test_api_request_format(self, gemini_agent, mock_google_response):
        """Test API request formatting."""
        with patch.object(gemini_agent.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_google_response
            mock_post.return_value = mock_response
            
            result = await gemini_agent._make_api_request(
                "test prompt",
                task_type=TaskType.TECHNICAL_PLANNING
            )
            
            assert result == "Mock Gemini response for testing"
            mock_post.assert_called_once()