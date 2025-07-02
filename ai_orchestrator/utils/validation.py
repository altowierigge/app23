"""
Validation utilities for API keys, configuration, and system health.
"""

import asyncio
import httpx
from typing import Dict, List, Tuple, Optional
import logging

from ..core.config import get_config
from .logging_config import get_logger


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class APIKeyValidator:
    """Validates API keys for all AI services."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("api_validator")
    
    async def validate_all_api_keys(self) -> Dict[str, bool]:
        """Validate all configured API keys (relaxed mode - only check if configured)."""
        results = {}
        
        # Relaxed validation - only check if API keys are configured, don't test connectivity
        
        # Check OpenAI
        if self.config.openai.api_key and self.config.openai.api_key.strip():
            results['openai'] = True
            self.logger.info("OpenAI API key configured")
        else:
            results['openai'] = False
            self.logger.warning("OpenAI API key not configured")
        
        # Check Anthropic
        if self.config.anthropic.api_key and self.config.anthropic.api_key.strip():
            results['anthropic'] = True
            self.logger.info("Anthropic API key configured")
        else:
            results['anthropic'] = False
            self.logger.warning("Anthropic API key not configured")
        
        # Google/Gemini removed in v2.0 - no longer used
        # results['google'] = True  # Not needed anymore
        
        return results
    
    async def _validate_openai_key(self) -> bool:
        """Validate OpenAI API key."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.config.openai.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Test with a minimal request
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                }
                
                response = await client.post(
                    f"{self.config.openai.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.logger.info("OpenAI API key validation successful")
                    return True
                elif response.status_code == 401:
                    self.logger.error("OpenAI API key is invalid")
                    return False
                else:
                    self.logger.warning(f"OpenAI API returned status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"OpenAI API key validation failed: {str(e)}")
            return False
    
    async def _validate_anthropic_key(self) -> bool:
        """Validate Anthropic API key."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "x-api-key": self.config.anthropic.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
                
                # Test with a minimal request
                payload = {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "test"}]
                }
                
                response = await client.post(
                    f"{self.config.anthropic.base_url}/v1/messages",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.logger.info("Anthropic API key validation successful")
                    return True
                elif response.status_code == 401:
                    self.logger.error("Anthropic API key is invalid")
                    return False
                else:
                    self.logger.warning(f"Anthropic API returned status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Anthropic API key validation failed: {str(e)}")
            return False
    
    # Google API validation removed in v2.0 - no longer needed


class SystemHealthChecker:
    """Comprehensive system health and readiness checker."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("health_checker")
        self.api_validator = APIKeyValidator()
    
    async def check_system_health(self) -> Dict[str, any]:
        """Perform comprehensive system health check."""
        health_report = {
            "overall_status": "healthy",
            "checks": {},
            "errors": [],
            "warnings": []
        }
        
        # Check API keys
        try:
            api_results = await self.api_validator.validate_all_api_keys()
            health_report["checks"]["api_keys"] = api_results
            
            failed_apis = [api for api, valid in api_results.items() if not valid]
            if failed_apis:
                health_report["errors"].extend([f"Invalid API key: {api}" for api in failed_apis])
                health_report["overall_status"] = "unhealthy"
                
        except Exception as e:
            health_report["errors"].append(f"API key validation failed: {str(e)}")
            health_report["overall_status"] = "unhealthy"
        
        # Check configuration
        config_check = self._check_configuration()
        health_report["checks"]["configuration"] = config_check
        if not config_check["valid"]:
            health_report["errors"].extend(config_check["errors"])
            health_report["overall_status"] = "unhealthy"
        
        # Check dependencies
        deps_check = self._check_dependencies()
        health_report["checks"]["dependencies"] = deps_check
        if not deps_check["all_available"]:
            health_report["warnings"].extend(deps_check["missing"])
        
        # Check file system
        fs_check = self._check_file_system()
        health_report["checks"]["file_system"] = fs_check
        if not fs_check["writable"]:
            health_report["errors"].append("Output directory not writable")
            health_report["overall_status"] = "unhealthy"
        
        return health_report
    
    def _check_configuration(self) -> Dict[str, any]:
        """Check configuration validity."""
        config_check = {
            "valid": True,
            "errors": [],
            "settings": {}
        }
        
        try:
            # Check required settings
            required_keys = ["openai.api_key", "anthropic.api_key"]  # google.api_key removed in v2.0
            for key_path in required_keys:
                if not self._get_nested_config(key_path):
                    config_check["errors"].append(f"Missing required setting: {key_path}")
                    config_check["valid"] = False
            
            # Check directories
            if not self.config.output_dir:
                config_check["errors"].append("Output directory not configured")
                config_check["valid"] = False
            
            # Check workflow file
            if not self.config.workflow_config_path:
                config_check["errors"].append("Workflow config path not set")
                config_check["valid"] = False
            
            config_check["settings"] = {
                "environment": self.config.environment,
                "debug": self.config.debug,
                "log_level": self.config.log_level.value,
                "output_dir": self.config.output_dir
            }
            
        except Exception as e:
            config_check["errors"].append(f"Configuration check failed: {str(e)}")
            config_check["valid"] = False
        
        return config_check
    
    def _get_nested_config(self, key_path: str) -> any:
        """Get nested configuration value by dot notation."""
        parts = key_path.split('.')
        value = self.config
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return value
    
    def _check_dependencies(self) -> Dict[str, any]:
        """Check optional dependencies."""
        deps_check = {
            "all_available": True,
            "available": [],
            "missing": []
        }
        
        # Check optional dependencies
        optional_deps = {
            "git": "GitPython",
            "github": "PyGithub", 
            "fastapi": "FastAPI",
            "uvicorn": "Uvicorn"
        }
        
        for dep_name, import_name in optional_deps.items():
            try:
                __import__(dep_name.lower())
                deps_check["available"].append(import_name)
            except ImportError:
                deps_check["missing"].append(f"{import_name} not installed")
                deps_check["all_available"] = False
        
        return deps_check
    
    def _check_file_system(self) -> Dict[str, any]:
        """Check file system access."""
        import os
        import tempfile
        
        fs_check = {
            "writable": True,
            "output_dir_exists": False,
            "temp_dir_writable": False
        }
        
        try:
            # Check if output directory exists and is writable
            if os.path.exists(self.config.output_dir):
                fs_check["output_dir_exists"] = True
                # Test write access
                test_file = os.path.join(self.config.output_dir, ".write_test")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    fs_check["writable"] = True
                except:
                    fs_check["writable"] = False
            else:
                # Try to create the directory
                try:
                    os.makedirs(self.config.output_dir, exist_ok=True)
                    fs_check["output_dir_exists"] = True
                    fs_check["writable"] = True
                except:
                    fs_check["writable"] = False
            
            # Check temp directory
            try:
                with tempfile.NamedTemporaryFile() as tmp:
                    tmp.write(b"test")
                fs_check["temp_dir_writable"] = True
            except:
                fs_check["temp_dir_writable"] = False
                
        except Exception as e:
            self.logger.error(f"File system check failed: {str(e)}")
            fs_check["writable"] = False
        
        return fs_check


class ConfigValidator:
    """Validates configuration at startup."""
    
    def __init__(self):
        self.logger = get_logger("config_validator")
    
    def validate_startup_config(self) -> Tuple[bool, List[str]]:
        """Validate configuration required for startup."""
        errors = []
        
        try:
            config = get_config()
            
            # Check at least one API key is configured
            has_api_key = any([
                config.openai.api_key,
                config.anthropic.api_key
                # config.google.api_key removed in v2.0
            ])
            
            if not has_api_key:
                errors.append("At least one AI service API key must be configured")
            
            # Check critical directories
            if not config.output_dir:
                errors.append("Output directory must be configured")
            
            # Check workflow file exists
            import os
            if not os.path.exists(config.workflow_config_path):
                errors.append(f"Workflow config file not found: {config.workflow_config_path}")
            
        except Exception as e:
            errors.append(f"Configuration validation failed: {str(e)}")
        
        is_valid = len(errors) == 0
        return is_valid, errors