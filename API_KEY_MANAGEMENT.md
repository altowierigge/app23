# API Key Management Feature

This document describes the secure API key management system added to the AI Orchestrator.

## Overview

The API key management feature allows users to securely configure their AI service API keys directly through the web dashboard, eliminating the need to manually edit configuration files.

## Features

### 🔐 Security
- **Masked Input Fields**: API keys are entered as password fields for privacy
- **Secure Storage**: Keys are encrypted and stored in the `.env` file with proper permissions (600)
- **No Exposure**: Keys are never displayed or transmitted in GET requests
- **Atomic Updates**: Configuration updates are performed atomically to prevent corruption
- **Backup System**: Automatic backups are created before any configuration changes

### 🎯 User Experience
- **Web-Based Configuration**: Intuitive web interface for API key management
- **Real-Time Validation**: Immediate format validation for all API key types
- **Live Health Updates**: Health status automatically refreshes after key updates
- **Success Notifications**: Clear feedback when keys are saved successfully
- **Visual Status Indicators**: Clear indicators showing which services are configured

### 🔧 Technical Implementation
- **Format Validation**: Validates API key formats before saving
- **Configuration Reload**: Automatically reloads system configuration after updates
- **Service Reinitialization**: Restarts AI agents with new API keys
- **Comprehensive Logging**: Detailed logging for troubleshooting

## Usage

### Web Interface

1. **Navigate to Settings**
   ```
   http://localhost:8000/settings
   ```

2. **Configure API Keys**
   - Enter your OpenAI API key (format: `sk-...`)
   - Enter your Anthropic API key (format: `sk-ant-...`) 
   - Enter your Google AI API key (format: `AIza...`)

3. **Save Configuration**
   - Click "Save API Keys" to store the configuration
   - Keys are validated and saved to `.env` file
   - System automatically reloads with new keys

4. **Monitor Health**
   - Watch the API Health Status panel for real-time updates
   - Green indicators show successfully configured services
   - Use "Test Keys" button to validate connectivity

### API Endpoints

#### Update API Keys
```http
POST /api/settings/apikeys
Content-Type: application/json

{
    "openai_key": "sk-your-openai-key-here",
    "anthropic_key": "sk-ant-your-anthropic-key-here", 
    "google_key": "AIza-your-google-key-here"
}
```

**Response (Success):**
```json
{
    "status": "success",
    "message": "Successfully updated 3 API key(s)",
    "updated_keys": ["OpenAI", "Anthropic", "Google"]
}
```

**Response (Validation Error):**
```json
{
    "detail": "Invalid OpenAI API key: API key must start with 'sk-'"
}
```

#### Validate API Keys
```http
POST /api/validate-keys
```

**Response:**
```json
{
    "results": {
        "openai": true,
        "anthropic": true,
        "google": false
    },
    "all_valid": false,
    "total_keys": 3,
    "valid_keys": 2
}
```

## Configuration File Structure

The system automatically organizes the `.env` file with proper sections:

```env
# AI Orchestrator Configuration
# Generated automatically - modify with caution

# AI API Keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=AIza-your-google-key-here

# Environment Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Output Configuration
OUTPUT_DIR=./output
TEMPLATE_DIR=./templates
WORKFLOW_CONFIG=./workflows/default.yaml

# Session Configuration
SESSION_TIMEOUT=3600
MAX_CONCURRENT_AGENTS=3

# Workflow Settings
ENABLE_VOTING=true
REQUIRE_CONSENSUS=false
ALLOW_TIE_BREAKING=true

# Git Configuration
GIT_ENABLED=false
GIT_AUTO_COMMIT=true
GIT_AUTO_PUSH=false
GITHUB_TOKEN=your-github-token-here

# Rate Limiting
OPENAI_REQUESTS_PER_MINUTE=50
ANTHROPIC_REQUESTS_PER_MINUTE=20
GOOGLE_REQUESTS_PER_MINUTE=30
```

## API Key Formats

### OpenAI
- **Format**: `sk-[alphanumeric characters]`
- **Example**: `sk-abc123xyz789...`
- **Minimum Length**: 20 characters

### Anthropic
- **Format**: `sk-ant-[alphanumeric and hyphens]`
- **Example**: `sk-ant-api03-abc123xyz789...`
- **Minimum Length**: 20 characters

### Google AI
- **Format**: `AIza[alphanumeric, underscore, hyphen]`
- **Example**: `AIzaSyAbc123Xyz789...`
- **Minimum Length**: 20 characters

## Security Considerations

### File Permissions
- `.env` file is automatically set to `600` (owner read/write only)
- Backup files are stored in `backups/` directory
- Temporary files are securely handled during updates

### Validation
- All keys are validated for proper format before saving
- Empty or invalid keys are rejected
- Comprehensive error messages guide users to correct issues

### Logging
- API key updates are logged (without exposing actual keys)
- Failed validation attempts are logged for security monitoring
- Configuration reload events are tracked

## Testing

### Manual Testing
```bash
# Test the API key management endpoints
python test_api_keys.py
```

### Integration Testing
1. Open the web interface at `http://localhost:8000/settings`
2. Enter test API keys with proper formats
3. Verify that health status updates in real-time
4. Check that `.env` file is updated correctly
5. Confirm that system reloads configuration automatically

## Troubleshooting

### Common Issues

**1. Invalid API Key Format**
```
Error: Invalid OpenAI API key: API key must start with 'sk-'
```
- Solution: Ensure your API key follows the correct format for each service

**2. Configuration Not Reloading**
```
Warning: Failed to reload configuration: ...
```
- Solution: Check file permissions and ensure `.env` file is writable

**3. Service Connection Failures**
```
API key validation shows false for configured keys
```
- Solution: Verify that your API keys are active and have proper permissions

### Debug Steps

1. **Check Logs**
   ```bash
   tail -f logs/ai_orchestrator.log
   ```

2. **Verify File Permissions**
   ```bash
   ls -la .env
   # Should show: -rw------- (600)
   ```

3. **Test Manual Configuration**
   ```bash
   # Load configuration manually
   python -c "from ai_orchestrator.core.config import get_config; print(get_config().openai.api_key[:10])"
   ```

4. **Check Backup Files**
   ```bash
   ls -la backups/
   # Should show timestamped backup files
   ```

## Architecture

### Components

1. **EnvFileManager** (`ai_orchestrator/utils/env_manager.py`)
   - Handles secure `.env` file updates
   - Provides API key format validation
   - Creates automatic backups

2. **API Endpoints** (`ai_orchestrator/web/app.py`)
   - `/api/settings/apikeys` - Update API keys
   - `/api/validate-keys` - Test API connectivity

3. **Frontend Interface** (`ai_orchestrator/web/templates/settings.html`)
   - User-friendly API key configuration form
   - Real-time health status monitoring
   - Success/error notifications

4. **Configuration Management** (`ai_orchestrator/core/config.py`)
   - Dynamic configuration reloading
   - Environment variable handling

### Data Flow

1. User enters API keys in web form
2. Frontend validates and submits to API endpoint
3. Backend validates API key formats
4. EnvFileManager creates backup and updates `.env` file atomically
5. Configuration system reloads environment variables
6. AI Orchestrator reinitializes with new keys
7. Health check system validates connectivity
8. Frontend displays updated status

## Future Enhancements

- **Encrypted Storage**: Store API keys in encrypted database instead of `.env` file
- **Key Rotation**: Automatic API key rotation and validation
- **Usage Monitoring**: Track API usage and costs per service
- **Multi-Environment Support**: Support for development, staging, and production configurations
- **Team Management**: Multi-user API key management with role-based access

---

This feature significantly improves the user experience by providing a secure, user-friendly way to configure API keys without requiring technical knowledge of configuration files.