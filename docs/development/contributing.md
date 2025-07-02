# Contributing to AI Orchestration System

Thank you for your interest in contributing to the AI Orchestration System! This guide will help you get started with development and contributing to the project.

## 🚀 Quick Start for Contributors

### 1. Development Environment Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/ai-orchestrator.git
cd ai-orchestrator

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e ".[dev]"  # Install in development mode

# Install pre-commit hooks
pre-commit install
```

### 2. Verify Development Setup

```bash
# Run system diagnostics
python main.py doctor --check-all

# Run test suite
./scripts/run-tests.sh

# Start development server
python main.py serve --port 8000

# Test in development mode
docker-compose -f docker-compose.dev.yml up
```

## 🏗️ Project Structure for Contributors

### Core Modules

```
ai_orchestrator/
├── agents/              # AI agent implementations
│   ├── base_agent.py   # Abstract base class
│   ├── gpt_agent.py    # OpenAI GPT integration
│   ├── claude_agent.py # Anthropic Claude integration
│   └── gemini_agent.py # Google Gemini integration
├── core/               # Core orchestration logic
│   ├── config.py       # Configuration management
│   ├── orchestrator.py # Main workflow coordinator
│   └── workflow_engine.py # YAML workflow execution
├── utils/              # Utility modules
│   ├── logging_config.py # Logging and metrics
│   ├── file_manager.py   # Code generation and file handling
│   ├── git_integration.py # Git and GitHub operations
│   └── validation.py     # System validation
├── web/                # Web interface
│   ├── app.py          # FastAPI application
│   ├── templates/      # HTML templates
│   └── static/         # Static assets
└── workflows/          # YAML workflow definitions
    └── default.yaml    # Default workflow configuration
```

### Key Design Patterns

#### **Agent Pattern**
All AI agents inherit from `BaseAgent` and implement:
```python
class MyAgent(BaseAgent):
    async def _make_api_request(self, prompt: str, **kwargs) -> str:
        # Implement API-specific request logic
        pass
    
    def _format_prompt(self, task: AgentTask) -> str:
        # Format prompts for this agent's requirements
        pass
```

#### **Configuration Pattern**
All configuration uses Pydantic models:
```python
class MyConfig(BaseSettings):
    setting_name: str = Field(default="default", env="ENV_VAR_NAME")
    
    class Config:
        env_file = ".env"
```

#### **Async/Await Pattern**
All I/O operations are asynchronous:
```python
async def my_function():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
    return response.json()
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/               # Unit tests
│   ├── test_agents.py
│   ├── test_config.py
│   └── test_orchestrator.py
├── integration/        # Integration tests
│   ├── test_workflow.py
│   └── test_api.py
├── e2e/               # End-to-end tests
│   └── test_complete_workflow.py
└── conftest.py        # Shared fixtures
```

### Writing Tests

#### **Unit Test Example**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from ai_orchestrator.agents.gpt_agent import GPTAgent

@pytest.mark.asyncio
async def test_gpt_agent_success():
    # Arrange
    config = MagicMock()
    config.api_key = "test-key"
    agent = GPTAgent(config)
    
    # Mock the API call
    agent.client.post = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}]
    }
    agent.client.post.return_value = mock_response
    
    # Act
    result = await agent._make_api_request("test prompt")
    
    # Assert
    assert result == "Test response"
    agent.client.post.assert_called_once()
```

#### **Integration Test Example**
```python
@pytest.mark.asyncio
async def test_complete_workflow():
    orchestrator = AIOrchestrator()
    session_id = await orchestrator.start_workflow("Create a simple app")
    
    # Wait for completion or timeout
    timeout = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = await orchestrator.get_workflow_status(session_id)
        if status['current_phase'] in ['completed', 'failed']:
            break
        await asyncio.sleep(5)
    
    assert status['current_phase'] == 'completed'
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agents.py

# Run with coverage
pytest --cov=ai_orchestrator --cov-report=html

# Run integration tests (slower)
pytest tests/integration/ -v

# Run tests with live logs
pytest -s --log-cli-level=INFO
```

## 🔧 Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/agent-improvements

# Make changes with tests
# ... code changes ...

# Run tests locally
./scripts/run-tests.sh

# Commit with conventional commits
git commit -m "feat: add retry logic to base agent"
```

### 2. Code Quality

#### **Pre-commit Hooks**
Automatically run on every commit:
- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Tests**: Basic test suite

#### **Manual Quality Checks**
```bash
# Format code
black ai_orchestrator/ tests/

# Check linting
flake8 ai_orchestrator/ tests/ --max-line-length=100

# Type checking
mypy ai_orchestrator/ --ignore-missing-imports

# Security scan
bandit -r ai_orchestrator/

# Dependency check
pip-audit
```

### 3. Pull Request Process

#### **Before Submitting**
- [ ] All tests pass locally
- [ ] Code is properly formatted (Black)
- [ ] No linting errors (Flake8)
- [ ] Type hints added (MyPy clean)
- [ ] Documentation updated
- [ ] Changelog entry added

#### **PR Template**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🌟 Contribution Areas

### 🤖 AI Agent Development

#### **Adding New AI Models**
```python
# 1. Create new agent class
class NewModelAgent(BaseAgent):
    def __init__(self, config: NewModelConfig):
        super().__init__(config, AgentRole.SPECIALIST)
    
    async def _make_api_request(self, prompt: str, **kwargs) -> str:
        # Implement API integration
        pass

# 2. Add configuration
class NewModelConfig(AIModelConfig):
    api_key: str = Field(..., env="NEWMODEL_API_KEY")
    model_name: str = "newmodel-latest"

# 3. Register in orchestrator
class AIOrchestrator:
    def __init__(self):
        # ... existing agents ...
        self.newmodel_agent = NewModelAgent(self.config.newmodel)
        self.agent_map["newmodel"] = self.newmodel_agent
```

#### **Improving Agent Capabilities**
- Enhanced prompt engineering
- Better error handling
- Response validation
- Multi-modal support (text, images, code)

### 🔄 Workflow Engine Enhancements

#### **New Workflow Features**
```yaml
# Example: Add conditional branching
phases:
  - name: "quality_check"
    agent: "claude"
    task_type: "code_review"
    condition: "enable_quality_gate"
    on_failure:
      action: "retry"
      max_attempts: 3
      escalate_to: "human_review"
```

#### **Custom Task Types**
```python
class TaskType(str, Enum):
    # Existing types...
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
```

### 🌐 Web Interface Improvements

#### **New Dashboard Features**
- Real-time collaboration tools
- Project templates and wizards
- Advanced metrics and analytics
- Custom workflow builders

#### **API Enhancements**
- GraphQL endpoint
- Webhook integrations
- Batch operations
- Advanced filtering and search

### 🔧 Infrastructure Improvements

#### **Performance Optimizations**
- Response caching
- Connection pooling
- Async optimizations
- Memory usage improvements

#### **DevOps Enhancements**
- Kubernetes deployment
- CI/CD improvements
- Monitoring integrations
- Security hardening

## 📖 Documentation Contributions

### Types of Documentation Needed

1. **API Documentation**
   - Endpoint descriptions
   - Request/response examples
   - Error handling guides

2. **User Guides**
   - Tutorial videos
   - Best practices
   - Use case examples

3. **Developer Documentation**
   - Architecture deep-dives
   - Plugin development guides
   - Performance tuning

### Documentation Standards

```markdown
# Title (H1)

Brief description of the feature/component.

## Overview (H2)

What this does and why it's useful.

## Quick Start (H2)

Minimal example to get started.

## Detailed Usage (H2)

Comprehensive examples and options.

## API Reference (H2)

Detailed parameter and response documentation.

## Examples (H2)

Real-world usage examples.

## Troubleshooting (H2)

Common issues and solutions.
```

## 🐛 Bug Reports

### Creating Effective Bug Reports

```markdown
**Bug Description**
Clear description of what's wrong

**Steps to Reproduce**
1. Step one
2. Step two
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: Ubuntu 22.04
- Python: 3.11.0
- Docker: 24.0.0
- Version: commit hash

**Logs**
```
[Relevant log entries]
```

**Additional Context**
Any other relevant information
```

### Debug Information

```bash
# Generate debug report
python main.py doctor --check-all > debug-report.txt

# Include system information
uname -a >> debug-report.txt
python --version >> debug-report.txt
docker --version >> debug-report.txt

# Sanitize sensitive information before sharing
sed -i 's/sk-[a-zA-Z0-9]\{32,\}/[REDACTED]/g' debug-report.txt
```

## 🔒 Security Considerations

### Security Guidelines for Contributors

1. **Never commit secrets**
   - Use `.env` files (git-ignored)
   - Sanitize logs and debug output
   - Use environment variables for sensitive data

2. **Input validation**
   - Validate all user inputs
   - Use Pydantic models for data validation
   - Sanitize data before AI model processing

3. **Dependencies**
   - Keep dependencies updated
   - Run security scans (`pip-audit`)
   - Review new dependency licenses

### Reporting Security Issues

**DO NOT** create public GitHub issues for security vulnerabilities.

Instead:
1. Email security@ai-orchestrator.dev
2. Include detailed description
3. Provide reproduction steps
4. Allow 90 days for responsible disclosure

## 📋 Code Style Guidelines

### Python Code Style

```python
# Use type hints everywhere
def process_data(items: List[Dict[str, Any]]) -> Optional[str]:
    """Process data items and return result.
    
    Args:
        items: List of data dictionaries
        
    Returns:
        Processed result or None if failed
        
    Raises:
        ValueError: If items list is empty
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    
    # Use descriptive variable names
    processed_results = []
    
    for item_data in items:
        # Process each item
        result = self._process_single_item(item_data)
        processed_results.append(result)
    
    return "\n".join(processed_results) if processed_results else None

# Use dataclasses for structured data
@dataclass
class ProcessingResult:
    """Result of data processing operation."""
    success: bool
    data: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
```

### Documentation Style

```python
class ExampleClass:
    """Brief class description.
    
    Longer description explaining the purpose and usage
    of this class in the system.
    
    Attributes:
        attribute_name: Description of the attribute
        
    Example:
        >>> example = ExampleClass("value")
        >>> result = example.process()
        >>> print(result)
        'processed_value'
    """
    
    def __init__(self, value: str):
        """Initialize the example class.
        
        Args:
            value: The initial value to process
            
        Raises:
            ValueError: If value is empty or None
        """
        if not value:
            raise ValueError("Value cannot be empty")
        self.value = value
```

## 🎯 Release Process

### Version Management

We use semantic versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Pre-release**
   - [ ] All tests pass
   - [ ] Documentation updated
   - [ ] Changelog updated
   - [ ] Version bumped
   - [ ] Security scan clean

2. **Release**
   - [ ] Create release branch
   - [ ] Tag version
   - [ ] Build and test containers
   - [ ] Update Docker Hub
   - [ ] Create GitHub release

3. **Post-release**
   - [ ] Update documentation site
   - [ ] Announce on community channels
   - [ ] Monitor for issues

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different perspectives and experiences

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord/Slack**: Real-time community chat
- **Email**: security@ai-orchestrator.dev for security issues

### Recognition

Contributors are recognized through:
- GitHub contributor graphs
- Release notes acknowledgments
- Community showcase
- Maintainer promotions for significant contributors

Thank you for contributing to the AI Orchestration System! Your contributions help make AI-powered development accessible to everyone.