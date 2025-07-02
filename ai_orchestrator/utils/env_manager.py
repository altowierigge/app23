"""
Secure environment file management for API key configuration.
"""

import os
import re
import tempfile
import shutil
from typing import Dict, Optional, Tuple
from pathlib import Path

from ..utils.logging_config import get_logger

logger = get_logger("env_manager")


class EnvFileManager:
    """Manages secure updating of .env files."""
    
    def __init__(self, env_file_path: str = ".env"):
        self.env_file_path = Path(env_file_path)
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def read_env_file(self) -> Dict[str, str]:
        """Read and parse the .env file."""
        env_vars = {}
        
        if not self.env_file_path.exists():
            logger.warning(f"Environment file {self.env_file_path} does not exist")
            return env_vars
        
        try:
            with open(self.env_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        env_vars[key] = value
                    else:
                        logger.warning(f"Invalid line {line_num} in {self.env_file_path}: {line}")
        
        except Exception as e:
            logger.error(f"Error reading {self.env_file_path}: {str(e)}")
            raise
        
        return env_vars
    
    def create_backup(self) -> Optional[Path]:
        """Create a backup of the current .env file."""
        if not self.env_file_path.exists():
            return None
        
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f".env.backup.{timestamp}"
            
            shutil.copy2(self.env_file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return None
    
    def update_api_keys(self, api_keys: Dict[str, str]) -> Tuple[bool, str]:
        """
        Securely update API keys in the .env file.
        
        Args:
            api_keys: Dictionary with keys: openai_key, anthropic_key, google_key
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate input
            if not isinstance(api_keys, dict):
                return False, "Invalid input: api_keys must be a dictionary"
            
            # Filter out empty keys
            filtered_keys = {k: v for k, v in api_keys.items() if v and v.strip()}
            
            if not filtered_keys:
                return False, "No valid API keys provided"
            
            # Create backup
            backup_path = self.create_backup()
            
            # Read current environment
            current_env = self.read_env_file()
            
            # Map input keys to environment variable names
            key_mapping = {
                'openai_key': 'OPENAI_API_KEY',
                'anthropic_key': 'ANTHROPIC_API_KEY', 
                'google_key': 'GOOGLE_API_KEY'
            }
            
            # Update the environment variables
            updated_vars = []
            for input_key, env_var_name in key_mapping.items():
                if input_key in filtered_keys:
                    current_env[env_var_name] = filtered_keys[input_key]
                    updated_vars.append(env_var_name)
            
            # Write updated .env file atomically
            success = self._write_env_file_atomic(current_env)
            
            if success:
                logger.info(f"Successfully updated API keys: {', '.join(updated_vars)}")
                return True, f"Successfully updated {len(updated_vars)} API key(s)"
            else:
                # Restore from backup if write failed
                if backup_path and backup_path.exists():
                    shutil.copy2(backup_path, self.env_file_path)
                    logger.info("Restored from backup after write failure")
                return False, "Failed to write updated environment file"
        
        except Exception as e:
            logger.error(f"Error updating API keys: {str(e)}")
            return False, f"Error updating API keys: {str(e)}"
    
    def _write_env_file_atomic(self, env_vars: Dict[str, str]) -> bool:
        """
        Atomically write the environment file to prevent corruption.
        """
        try:
            # Create temporary file in the same directory
            with tempfile.NamedTemporaryFile(
                mode='w', 
                dir=self.env_file_path.parent,
                prefix='.env.tmp.',
                suffix='.tmp',
                delete=False,
                encoding='utf-8'
            ) as tmp_file:
                
                # Write header comment
                tmp_file.write("# AI Orchestrator Configuration\n")
                tmp_file.write("# Generated automatically - modify with caution\n\n")
                
                # Group related variables
                sections = {
                    "AI API Keys": [
                        "OPENAI_API_KEY",
                        "ANTHROPIC_API_KEY", 
                        "GOOGLE_API_KEY"
                    ],
                    "Environment Configuration": [
                        "ENVIRONMENT",
                        "DEBUG",
                        "LOG_LEVEL"
                    ],
                    "Output Configuration": [
                        "OUTPUT_DIR",
                        "TEMPLATE_DIR",
                        "WORKFLOW_CONFIG"
                    ],
                    "Session Configuration": [
                        "SESSION_TIMEOUT",
                        "MAX_CONCURRENT_AGENTS"
                    ],
                    "Workflow Settings": [
                        "ENABLE_VOTING",
                        "REQUIRE_CONSENSUS",
                        "ALLOW_TIE_BREAKING"
                    ],
                    "Git Configuration": [
                        "GIT_ENABLED",
                        "GIT_AUTO_COMMIT",
                        "GIT_AUTO_PUSH",
                        "GITHUB_TOKEN"
                    ],
                    "Rate Limiting": [
                        "OPENAI_REQUESTS_PER_MINUTE",
                        "ANTHROPIC_REQUESTS_PER_MINUTE", 
                        "GOOGLE_REQUESTS_PER_MINUTE"
                    ]
                }
                
                # Write variables by section
                for section_name, section_vars in sections.items():
                    section_written = False
                    
                    for var_name in section_vars:
                        if var_name in env_vars:
                            if not section_written:
                                tmp_file.write(f"# {section_name}\n")
                                section_written = True
                            
                            value = env_vars[var_name]
                            # Escape quotes in values
                            if '"' in value or "'" in value or ' ' in value:
                                escaped = value.replace('"', '\"')
                                value = f'"{escaped}"'
                            
                            tmp_file.write(f"{var_name}={value}\n")
                    
                    if section_written:
                        tmp_file.write("\n")
                
                # Write any remaining variables not in sections
                remaining_vars = set(env_vars.keys()) - {
                    var for section_vars in sections.values() 
                    for var in section_vars
                }
                
                if remaining_vars:
                    tmp_file.write("# Additional Configuration\n")
                    for var_name in sorted(remaining_vars):
                        value = env_vars[var_name]
                        if '"' in value or "'" in value or ' ' in value:
                            escaped = value.replace('"', '\"')
                            value = f'"{escaped}"'
                        tmp_file.write(f"{var_name}={value}\n")
                
                tmp_file_path = tmp_file.name
            
            # Atomically replace the original file
            shutil.move(tmp_file_path, self.env_file_path)
            
            # Set appropriate permissions (readable by owner only)
            os.chmod(self.env_file_path, 0o600)
            
            return True
        
        except Exception as e:
            logger.error(f"Error writing environment file: {str(e)}")
            # Clean up temporary file if it exists
            try:
                if 'tmp_file_path' in locals():
                    os.unlink(tmp_file_path)
            except:
                pass
            return False
    
    def validate_api_key_format(self, key_type: str, api_key: str) -> Tuple[bool, str]:
        """
        Validate API key format - RELAXED MODE (accepts any non-empty text).
        
        Args:
            key_type: Type of API key (openai, anthropic, google)
            api_key: The API key to validate
            
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        if not api_key or not api_key.strip():
            return False, "API key cannot be empty"
        
        api_key = api_key.strip()
        
        # RELAXED VALIDATION - Accept any non-empty text
        # This allows testing with placeholder keys or any custom text
        
        # Skip strict format validation for testing
        # Original strict validation is commented out below:
        
        # format_rules = {
        #     'openai': {
        #         'prefix': 'sk-',
        #         'min_length': 20,
        #         'pattern': r'^sk-[a-zA-Z0-9_\-\.]+$'
        #     },
        #     'anthropic': {
        #         'prefix': 'sk-ant-',
        #         'min_length': 20,
        #         'pattern': r'^sk-ant-[a-zA-Z0-9-]+$'
        #     },
        #     'google': {
        #         'prefix': 'AIza',
        #         'min_length': 20,
        #         'pattern': r'^AIza[a-zA-Z0-9_-]+$'
        #     }
        # }
        
        # Validate key type is known
        valid_types = ['openai', 'anthropic', 'google']
        if key_type not in valid_types:
            return False, f"Unknown API key type: {key_type}"
        
        # Accept any non-empty text as valid
        return True, f"API key accepted (relaxed mode) - Length: {len(api_key)} chars"


# Global instance
env_manager = EnvFileManager()


def update_api_keys(api_keys: Dict[str, str]) -> Tuple[bool, str]:
    """Convenience function to update API keys."""
    return env_manager.update_api_keys(api_keys)


def validate_api_key(key_type: str, api_key: str) -> Tuple[bool, str]:
    """Convenience function to validate API key format."""
    return env_manager.validate_api_key_format(key_type, api_key)


def save_github_settings_to_env(settings: Dict[str, str]) -> Tuple[bool, str]:
    """
    Save GitHub settings to the .env file.
    
    Args:
        settings: Dictionary of GitHub settings to save
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Read current environment
        current_env = env_manager.read_env_file()
        
        # Update with new settings
        for key, value in settings.items():
            current_env[key] = value
        
        # Write updated environment file
        success = env_manager._write_env_file_atomic(current_env)
        
        if success:
            logger.info(f"Successfully saved GitHub settings")
            return True, "GitHub settings saved successfully"
        else:
            return False, "Failed to write updated environment file"
        
    except Exception as e:
        logger.error(f"Failed to save GitHub settings: {str(e)}")
        return False, f"Failed to save GitHub settings: {str(e)}"