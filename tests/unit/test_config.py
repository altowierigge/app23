"""
Unit tests for configuration management.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

from ai_orchestrator.core.config import (
    OrchestratorConfig, 
    OpenAIConfig, 
    AnthropicConfig, 
    GoogleConfig,
    LogLevel,
    RetryStrategy
)


class TestOrchestratorConfig:
    """Test OrchestratorConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            config = OrchestratorConfig()
            
            assert config.environment == "development"
            assert config.debug == False
            assert config.log_level == LogLevel.INFO
            assert config.output_dir == "./output"
    
    def test_environment_override(self):
        """Test environment variable overrides."""
        env_vars = {
            "ENVIRONMENT": "production",
            "DEBUG": "true",
            "LOG_LEVEL": "ERROR",
            "OUTPUT_DIR": "/custom/output"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = OrchestratorConfig()
            
            assert config.environment == "production"
            assert config.debug == True
            assert config.log_level == LogLevel.ERROR
            assert config.output_dir == "/custom/output"
    
    def test_api_key_configuration(self):
        """Test API key configuration."""
        env_vars = {
            "OPENAI_API_KEY": "test-openai-key",
            "ANTHROPIC_API_KEY": "test-anthropic-key", 
            "GOOGLE_API_KEY": "test-google-key"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = OrchestratorConfig()
            
            assert config.openai.api_key == "test-openai-key"
            assert config.anthropic.api_key == "test-anthropic-key"
            assert config.google.api_key == "test-google-key"
    
    def test_directory_creation(self, temp_dir):
        """Test that directories are created if they don't exist."""
        output_dir = os.path.join(temp_dir, "test_output")
        template_dir = os.path.join(temp_dir, "test_templates")
        
        env_vars = {
            "OUTPUT_DIR": output_dir,
            "TEMPLATE_DIR": template_dir
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = OrchestratorConfig()
            
            assert os.path.exists(output_dir)
            assert os.path.exists(template_dir)
    
    def test_log_level_validation(self):
        """Test log level validation."""
        with patch.dict(os.environ, {"LOG_LEVEL": "invalid"}, clear=True):
            with pytest.raises(ValueError):
                OrchestratorConfig()


class TestOpenAIConfig:
    """Test OpenAI configuration."""
    
    def test_default_model(self):
        """Test default OpenAI model configuration."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            config = OpenAIConfig()
            
            assert config.model_name == "gpt-4"
            assert config.base_url == "https://api.openai.com/v1"
            assert config.max_tokens == 4000
            assert config.temperature == 0.7
    
    def test_retry_configuration(self):
        """Test retry configuration."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            config = OpenAIConfig()
            
            assert config.max_retries == 3
            assert config.retry_strategy == RetryStrategy.EXPONENTIAL
            assert config.base_delay == 1.0
            assert config.max_delay == 60.0


class TestAnthropicConfig:
    """Test Anthropic configuration."""
    
    def test_default_model(self):
        """Test default Anthropic model configuration."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
            config = AnthropicConfig()
            
            assert config.model_name == "claude-3-sonnet-20240229"
            assert config.base_url == "https://api.anthropic.com"


class TestGoogleConfig:
    """Test Google configuration."""
    
    def test_default_model(self):
        """Test default Google model configuration.""" 
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True):
            config = GoogleConfig()
            
            assert config.model_name == "gemini-pro"
            assert config.base_url == "https://generativelanguage.googleapis.com/v1beta"