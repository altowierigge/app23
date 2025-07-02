"""
Configuration management using Pydantic for type validation and environment variables.
"""

import os
from typing import Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class RetryStrategy(str, Enum):
    EXPONENTIAL = "exponential"
    FIXED = "fixed"
    LINEAR = "linear"


class AIModelConfig(BaseSettings):
    """Configuration for individual AI models."""
    api_key: Optional[str] = None
    model_name: str
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 60
    
    # Retry configuration
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0  # Optimized for faster execution
    max_delay: float = 30.0  # Reduced max delay for speed
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "protected_namespaces": ('settings_',)
    }


class OpenAIConfig(AIModelConfig):
    """OpenAI specific configuration."""
    api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    model_name: str = "gpt-4"
    base_url: str = "https://api.openai.com/v1"
    requests_per_minute: int = 500
    requests_per_hour: int = 10000


class AnthropicConfig(AIModelConfig):
    """Anthropic Claude specific configuration."""
    api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    model_name: str = "claude-3-5-sonnet-20241022"
    base_url: str = "https://api.anthropic.com"
    requests_per_minute: int = 50
    requests_per_hour: int = 1000


# GoogleConfig removed in v2.0 - no longer used


class GitConfig(BaseSettings):
    """Git integration configuration."""
    enabled: bool = Field(default=False, env="GIT_ENABLED")
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    auto_commit: bool = Field(default=True, env="GIT_AUTO_COMMIT")
    auto_push: bool = Field(default=False, env="GIT_AUTO_PUSH")
    repository_template: str = "ai-generated-{timestamp}"
    branch_name: str = "main"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "protected_namespaces": ('settings_',)
    }


class OrchestratorConfig(BaseSettings):
    """Main orchestrator configuration."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    
    # Output configuration
    output_dir: str = Field(default="./output", env="OUTPUT_DIR")
    project_template_dir: str = Field(default="./templates", env="TEMPLATE_DIR")
    workflow_config_path: str = Field(default="./workflows/default.yaml", env="WORKFLOW_CONFIG")
    
    @validator('workflow_config_path')
    def check_active_workflow(cls, v):
        """Check for active workflow first, then fall back to default."""
        import os
        
        # If explicitly set via env var, use that
        if os.getenv("WORKFLOW_CONFIG"):
            return v
            
        # Check for active workflow
        active_workflow = "./workflows/active.yaml"
        if os.path.exists(active_workflow):
            return active_workflow
            
        # Fall back to default
        return v
    
    # Session management
    session_timeout: int = Field(default=3600, env="SESSION_TIMEOUT")  # 1 hour
    max_concurrent_agents: int = Field(default=3, env="MAX_CONCURRENT_AGENTS")
    
    # AI model configurations (Google/Gemini removed - no longer used)
    openai: OpenAIConfig = OpenAIConfig()
    anthropic: AnthropicConfig = AnthropicConfig()
    # google: GoogleConfig = GoogleConfig()  # Deprecated in v2.0
    
    # Git integration
    git: GitConfig = GitConfig()
    
    # Workflow settings
    enable_voting: bool = Field(default=True, env="ENABLE_VOTING")
    require_consensus: bool = Field(default=True, env="REQUIRE_CONSENSUS")
    allow_tie_breaking: bool = Field(default=True, env="ALLOW_TIE_BREAKING")
    
    @validator('output_dir', 'project_template_dir')
    def ensure_directory_exists(cls, v):
        """Ensure output directories exist."""
        os.makedirs(v, exist_ok=True)
        return v
    
    @validator('log_level', pre=True)
    def validate_log_level(cls, v):
        """Validate and convert log level."""
        if isinstance(v, str):
            return LogLevel(v.upper())
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "protected_namespaces": ('settings_',)
    }


# Global configuration instance
config = OrchestratorConfig()


def get_config() -> OrchestratorConfig:
    """Get the global configuration instance with forced API key loading."""
    # Force load API keys from environment even if Pydantic filters them
    _force_load_api_keys(config)
    return config


def reload_config() -> OrchestratorConfig:
    """Reload the global configuration from environment."""
    global config
    config = OrchestratorConfig()
    _force_load_api_keys(config)  
    return config


def _force_load_api_keys(config_obj: OrchestratorConfig) -> None:
    """Force load API keys from environment, bypassing Pydantic validation."""
    import os
    from dotenv import load_dotenv
    
    # Ensure environment is loaded
    load_dotenv()
    
    # Override API keys directly from environment
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and openai_key.strip():
        config_obj.openai.api_key = openai_key.strip()
    
    anthropic_key = os.getenv('ANTHROPIC_API_KEY') 
    if anthropic_key and anthropic_key.strip():
        config_obj.anthropic.api_key = anthropic_key.strip()
        
    # Google/Gemini removed in v2.0 - no longer used
    # google_key = os.getenv('GOOGLE_API_KEY')
    # if google_key and google_key.strip():
    #     config_obj.google.api_key = google_key.strip()