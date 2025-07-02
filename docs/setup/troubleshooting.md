# Troubleshooting Guide

Common issues and solutions for the AI Orchestration System.

## 🚨 Quick Diagnostics

### System Health Check
```bash
# Run comprehensive diagnostics
python main.py doctor --check-apis --check-git --check-github

# Check specific components
python main.py doctor --check-apis     # API connectivity only
python main.py doctor --check-git      # Git configuration only
```

### API Health Check
```bash
# Test API endpoint
curl http://localhost:8000/api/health | jq

# Expected healthy response:
{
  "overall_status": "healthy",
  "checks": {
    "api_keys": {
      "openai": true,
      "anthropic": true,
      "google": true
    }
  }
}
```

## 🔑 API Key Issues

### ❌ "API key not configured"

**Symptoms:**
- Health check shows API key failures
- Projects fail during agent execution
- 401 Unauthorized errors in logs

**Solutions:**

1. **Check Environment Variables:**
```bash
# Verify .env file exists and contains keys
cat .env | grep API_KEY

# Should show (with actual keys):
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
```

2. **Validate API Key Format:**
```bash
# OpenAI keys start with 'sk-'
# Anthropic keys start with 'sk-ant-'  
# Google keys start with 'AIza'

# Test key loading
python -c "
from ai_orchestrator.core.config import get_config
config = get_config()
print('OpenAI:', config.openai.api_key[:10] if config.openai.api_key else 'Not set')
print('Anthropic:', config.anthropic.api_key[:10] if config.anthropic.api_key else 'Not set')
print('Google:', config.google.api_key[:10] if config.google.api_key else 'Not set')
"
```

3. **Test API Connectivity:**
```bash
# Validate keys with actual API calls
python -c "
import asyncio
from ai_orchestrator.utils.validation import APIKeyValidator

async def test():
    validator = APIKeyValidator()
    results = await validator.validate_all_api_keys()
    for service, valid in results.items():
        print(f'{service}: {'✅' if valid else '❌'}')

asyncio.run(test())
"
```

### ❌ "Invalid API key" or 401 Errors

**Common Causes:**
- Expired API keys
- Incorrect key format
- Insufficient API credits
- Rate limiting

**Solutions:**

1. **Regenerate API Keys:**
   - **OpenAI**: https://platform.openai.com/api-keys
   - **Anthropic**: https://console.anthropic.com/
   - **Google**: https://console.cloud.google.com/

2. **Check API Credits:**
```bash
# Check OpenAI usage
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check Anthropic credits (via dashboard)
# Check Google Cloud billing
```

3. **Verify Permissions:**
   - Ensure API keys have required scopes
   - Check organization access
   - Verify model access permissions

## 🔗 Connection Issues

### ❌ "Connection timeout" or Network Errors

**Symptoms:**
- Workflows hang during AI agent calls
- Intermittent failures
- Long response times

**Solutions:**

1. **Check Network Connectivity:**
```bash
# Test basic connectivity
ping api.openai.com
ping api.anthropic.com
ping generativelanguage.googleapis.com

# Test HTTPS connectivity
curl -I https://api.openai.com/v1/models
```

2. **Configure Proxy (if needed):**
```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Or in .env file:
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

3. **Adjust Timeout Settings:**
```env
# In .env file - increase timeouts
API_TIMEOUT=120  # seconds
MAX_RETRIES=5
```

### ❌ "Rate limit exceeded"

**Symptoms:**
- 429 errors in logs
- Workflows slow or failing
- API responses delayed

**Solutions:**

1. **Check Rate Limits:**
```python
# View current rate limit settings
from ai_orchestrator.core.config import get_config
config = get_config()

print(f"OpenAI: {config.openai.requests_per_minute}/min")
print(f"Anthropic: {config.anthropic.requests_per_minute}/min") 
print(f"Google: {config.google.requests_per_minute}/min")
```

2. **Adjust Rate Limits:**
```env
# In .env file - reduce request rates
OPENAI_REQUESTS_PER_MINUTE=20
ANTHROPIC_REQUESTS_PER_MINUTE=10
GOOGLE_REQUESTS_PER_MINUTE=15
```

3. **Upgrade API Plans:**
   - Increase rate limits with paid plans
   - Use multiple API keys for rotation
   - Implement request queuing

## 🐳 Docker Issues

### ❌ Docker Container Won't Start

**Symptoms:**
- Container exits immediately
- "Port already in use" errors
- Health checks failing

**Solutions:**

1. **Check Port Conflicts:**
```bash
# Find processes using port 8000
lsof -i :8000

# Kill conflicting processes
kill $(lsof -t -i:8000)

# Or use different port
docker-compose up -d -p 8001:8000
```

2. **View Container Logs:**
```bash
# Check container logs
docker-compose logs ai-orchestrator

# Follow logs in real-time
docker-compose logs -f ai-orchestrator

# Check specific container
docker logs ai-orchestrator-ai-orchestrator-1
```

3. **Verify Environment Variables:**
```bash
# Check environment in container
docker-compose exec ai-orchestrator env | grep API_KEY

# Verify .env file is being loaded
docker-compose config
```

### ❌ Container Health Check Failures

**Symptoms:**
- Container marked as unhealthy
- Service restarts frequently
- API endpoints unreachable

**Solutions:**

1. **Manual Health Check:**
```bash
# Test health endpoint manually
docker-compose exec ai-orchestrator curl http://localhost:8000/api/health

# Check if service is running
docker-compose exec ai-orchestrator ps aux
```

2. **Increase Health Check Timeout:**
```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
  interval: 60s  # Increase interval
  timeout: 30s   # Increase timeout
  retries: 5     # Increase retries
  start_period: 120s  # Increase start period
```

## 💾 File System Issues

### ❌ "Permission denied" or Write Errors

**Symptoms:**
- Cannot create output files
- Docker volume mount errors
- Project generation fails

**Solutions:**

1. **Check Directory Permissions:**
```bash
# Check output directory permissions
ls -la output/

# Fix permissions
chmod 755 output/
chown $USER:$USER output/
```

2. **Docker Volume Permissions:**
```bash
# Fix Docker volume permissions
docker-compose exec ai-orchestrator chown -R app:app /app/output

# Or in docker-compose.yml
volumes:
  - ./output:/app/output:Z  # Add :Z for SELinux
```

3. **Create Missing Directories:**
```bash
# Ensure directories exist
mkdir -p output logs

# Set proper ownership
sudo chown -R $USER:$USER output logs
```

### ❌ "Disk space" or Storage Issues

**Solutions:**

1. **Check Disk Space:**
```bash
# Check available space
df -h

# Check output directory size
du -sh output/

# Clean old projects
find output/ -type d -mtime +30 -exec rm -rf {} \;
```

2. **Configure Cleanup:**
```env
# In .env file - enable automatic cleanup
AUTO_CLEANUP_ENABLED=true
CLEANUP_DAYS=7
MAX_PROJECTS=50
```

## 🔧 Configuration Issues

### ❌ "Invalid configuration" Errors

**Symptoms:**
- Application won't start
- Validation errors during startup
- YAML parsing errors

**Solutions:**

1. **Validate Configuration:**
```bash
# Check YAML syntax
python -c "
import yaml
with open('workflows/default.yaml') as f:
    yaml.safe_load(f)
print('YAML is valid')
"

# Validate configuration
python -c "
from ai_orchestrator.core.config import get_config
config = get_config()
print('Configuration loaded successfully')
"
```

2. **Reset to Defaults:**
```bash
# Backup current config
cp .env .env.backup

# Reset to example
cp .env.example .env

# Edit with minimal config
nano .env
```

3. **Check Required Settings:**
```bash
# Verify required environment variables
python -c "
from ai_orchestrator.utils.validation import ConfigValidator
validator = ConfigValidator()
is_valid, errors = validator.validate_startup_config()
if not is_valid:
    for error in errors:
        print(f'❌ {error}')
else:
    print('✅ Configuration is valid')
"
```

## 🔄 Workflow Issues

### ❌ Workflows Hang or Fail

**Symptoms:**
- Projects stuck in one phase
- No progress updates
- Agent timeouts

**Solutions:**

1. **Check Agent Status:**
```bash
# View detailed logs
tail -f logs/ai_orchestrator.log | grep -E "(ERROR|WARNING|agent)"

# Check active sessions
curl http://localhost:8000/api/projects | jq '.projects[] | {session_id, current_phase, progress}'
```

2. **Restart Stuck Workflows:**
```bash
# Stop specific project (via API)
curl -X DELETE http://localhost:8000/api/projects/{session_id}

# Or restart entire service
docker-compose restart ai-orchestrator
```

3. **Adjust Timeouts:**
```env
# In .env file - increase timeouts
PHASE_TIMEOUT=900      # 15 minutes per phase
SESSION_TIMEOUT=7200   # 2 hours total
AGENT_TIMEOUT=300      # 5 minutes per agent call
```

### ❌ "Agent disagreement" or Voting Failures

**Solutions:**

1. **Enable Tie-Breaking:**
```env
# In .env file
ENABLE_VOTING=true
ALLOW_TIE_BREAKING=true
REQUIRE_CONSENSUS=false
```

2. **Simplify Requirements:**
   - Use clearer, more specific project descriptions
   - Avoid conflicting technical requirements
   - Specify preferred technologies

3. **Check Agent Performance:**
```bash
# View agent-specific metrics
curl http://localhost:8000/api/agents/gpt/performance
curl http://localhost:8000/api/agents/claude/performance
curl http://localhost:8000/api/agents/gemini/performance
```

## 📊 Performance Issues

### ❌ Slow Response Times

**Symptoms:**
- Long workflow execution times
- High API response times
- Dashboard loading slowly

**Solutions:**

1. **Check System Resources:**
```bash
# Monitor system usage
top -p $(pgrep -f "python.*ai_orchestrator")

# Check memory usage
docker stats ai-orchestrator

# Monitor disk I/O
iostat -x 1
```

2. **Optimize Configuration:**
```env
# Reduce parallel operations
MAX_CONCURRENT_AGENTS=1

# Decrease token limits
MAX_TOKENS=2000

# Enable caching
ENABLE_RESPONSE_CACHE=true
CACHE_TTL=3600
```

3. **Database Optimization:**
```bash
# If using PostgreSQL, optimize
docker-compose exec postgres psql -U ai_orchestrator -c "VACUUM ANALYZE;"

# Check Redis memory usage
docker-compose exec redis redis-cli info memory
```

## 🔍 Debugging Techniques

### Enable Debug Logging
```env
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

### View Detailed Logs
```bash
# Application logs
tail -f logs/ai_orchestrator.log

# Error logs only
tail -f logs/errors.log

# Metrics logs
tail -f logs/metrics.log

# Filter by session
grep "session-abc123" logs/ai_orchestrator.log
```

### Interactive Debugging
```python
# Debug configuration
from ai_orchestrator.core.config import get_config
config = get_config()
print(f"Environment: {config.environment}")
print(f"Debug mode: {config.debug}")

# Debug agents
from ai_orchestrator import AIOrchestrator
orchestrator = AIOrchestrator()
print(f"Agents initialized: {len(orchestrator.agent_map)}")

# Test individual agent
import asyncio
from ai_orchestrator.agents import AgentTask, TaskType

async def test_agent():
    task = AgentTask(
        task_type=TaskType.REQUIREMENTS_REFINEMENT,
        prompt="Create a simple calculator",
        context={},
        requirements={},
        session_id="debug"
    )
    response = await orchestrator.gpt_agent.execute_task(task)
    print(f"Success: {response.success}")
    print(f"Content: {response.content[:100]}...")

asyncio.run(test_agent())
```

## 🆘 Getting Additional Help

### Log Analysis
```bash
# Generate system report
python main.py doctor --check-all > system-report.txt

# Package logs for support
tar -czf ai-orchestrator-logs.tar.gz logs/ .env.example
```

### Community Support
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check latest documentation
- **Examples**: Review working examples
- **Discord/Slack**: Community chat (if available)

### Professional Support
- **Consultation**: Architecture and deployment guidance
- **Custom Development**: Feature additions and modifications
- **Training**: Team onboarding and best practices

Remember to remove sensitive information (API keys, tokens) before sharing logs or configuration files for support.