# AI Orchestration System

A comprehensive multi-agent workflow system that coordinates GPT (Project Manager), Claude (Backend Expert), and Gemini (Frontend Expert) to collaboratively design and implement complete software projects.

## 🌟 Features

- **Multi-Agent Coordination**: Three specialized AI agents working together
- **Complete Workflow**: From requirements to deployed code
- **YAML-Based Configuration**: Dynamic workflow definitions
- **Resilient API Calls**: Robust retry logic with tenacity
- **Git Integration**: Automatic repository creation and GitHub publishing
- **Comprehensive Logging**: Detailed monitoring and metrics
- **Modular Architecture**: Clean, maintainable Python codebase

## 🏗️ Architecture

### Agent Roles

- **GPT-4 (Project Manager)**: Requirements refinement, plan comparison, conflict resolution, test generation
- **Claude (Backend Expert)**: Backend architecture, API development, database design
- **Gemini (Frontend Expert)**: Frontend design, user interface, user experience

### Workflow Phases

1. **Requirements Refinement**: GPT analyzes and clarifies user requirements
2. **Technical Planning**: Claude and Gemini create independent technical plans
3. **Plan Comparison**: GPT compares plans and identifies conflicts
4. **Conflict Resolution**: Agents justify their approaches
5. **Voting**: Democratic decision-making process
6. **Implementation**: Parallel backend and frontend development
7. **Testing**: Comprehensive test suite generation
8. **Output**: Structured project files with Git integration

## 🚀 Quick Start

### Installation

```bash
git clone <repository-url>
cd ai-orchestrator
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Add your API keys to `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### Usage

#### Command Line Interface

```bash
# Generate a project
python main.py generate "Create a todo application with user authentication"

# Check workflow status
python main.py status <session-id>

# Run system diagnostics
python main.py doctor --check-apis --check-git

# View metrics
python main.py metrics
```

#### Python API

```python
import asyncio
from ai_orchestrator import AIOrchestrator, setup_logging

async def main():
    setup_logging()
    
    orchestrator = AIOrchestrator()
    session_id = await orchestrator.start_workflow(
        "Create a simple blog platform with user management"
    )
    
    # Monitor progress
    status = await orchestrator.get_workflow_status(session_id)
    print(f"Current phase: {status['current_phase']}")

asyncio.run(main())
```

## 📁 Project Structure

```
ai_orchestrator/
├── agents/                 # AI agent implementations
│   ├── base_agent.py      # Base agent class with retry logic
│   ├── gpt_agent.py       # OpenAI GPT agent
│   ├── claude_agent.py    # Anthropic Claude agent
│   └── gemini_agent.py    # Google Gemini agent
├── core/                  # Core system components
│   ├── config.py          # Pydantic configuration management
│   ├── orchestrator.py    # Main workflow orchestrator
│   └── workflow_engine.py # YAML-based workflow engine
├── utils/                 # Utility modules
│   ├── logging_config.py  # Logging and metrics
│   ├── file_manager.py    # File output management
│   └── git_integration.py # Git and GitHub integration
├── workflows/             # YAML workflow definitions
│   └── default.yaml       # Default multi-agent workflow
└── cli.py                 # Command-line interface
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `GOOGLE_API_KEY` | Google API key | Yes |
| `GITHUB_TOKEN` | GitHub personal access token | Optional |
| `OUTPUT_DIR` | Output directory for generated projects | No |
| `WORKFLOW_CONFIG` | Path to workflow YAML file | No |

### Workflow Configuration

The system uses YAML files to define workflows. The default workflow includes:

- Agent role definitions
- Phase sequences and dependencies
- Parallel execution groups
- Conditional logic
- Error handling strategies
- Output configuration

Example workflow phase:
```yaml
- name: "backend_implementation"
  description: "Claude implements backend code"
  agent: "claude" 
  task_type: "implementation"
  parallel: true
  parallel_group: "implementation"
  timeout: 900
  inputs:
    - name: "technical_plan"
      source: "workflow_state.claude_plan"
  outputs:
    - name: "backend_implementation"
      destination: "workflow_state"
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=ai_orchestrator

# Run specific test category
pytest tests/test_agents.py
```

## 📊 Monitoring

The system provides comprehensive monitoring and metrics:

### Metrics Collected
- API response times
- Phase execution durations
- Error rates per agent
- Token usage tracking
- Workflow success rates

### Logging Levels
- **DEBUG**: Detailed execution information
- **INFO**: General workflow progress
- **WARNING**: Non-critical issues
- **ERROR**: Failures and exceptions

### Performance Monitoring
- Health checks
- Performance thresholds
- Automated alerting
- Resource utilization tracking

## 🔌 Extensions

### Git Integration

Automatic Git repository creation and GitHub publishing:

```python
from ai_orchestrator.utils.git_integration import ProjectPublisher

publisher = ProjectPublisher()
result = publisher.publish_project(project, project_path, push_to_github=True)
```

### Custom Agents

Extend the base agent class for custom AI services:

```python
from ai_orchestrator.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def _make_api_request(self, prompt: str, **kwargs) -> str:
        # Implement custom API integration
        pass
```

### Workflow Customization

Create custom workflows by modifying the YAML configuration:

```yaml
name: "Custom Development Workflow"
phases:
  - name: "custom_phase"
    agent: "custom_agent"
    task_type: "custom_task"
    # ... phase configuration
```

## 🚨 Error Handling

The system implements multiple layers of error handling:

1. **Retry Logic**: Exponential backoff with jitter
2. **Circuit Breakers**: Prevent cascading failures
3. **Graceful Degradation**: Continue workflow when possible
4. **Error Recovery**: Automatic recovery strategies
5. **Human Escalation**: Critical failure notifications

## 🔒 Security

- Environment-based API key management
- Request/response sanitization
- Rate limiting and abuse prevention
- Secure Git operations
- Optional GitHub integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run linting
black ai_orchestrator/
flake8 ai_orchestrator/
mypy ai_orchestrator/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙋 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/ai-orchestrator/ai-orchestrator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ai-orchestrator/ai-orchestrator/discussions)

## 🗺️ Roadmap

- [ ] Web-based dashboard
- [ ] Additional AI model integrations
- [ ] Template system for project types
- [ ] Real-time collaboration features
- [ ] Advanced analytics and reporting
- [ ] Plugin system for extensibility

---

**Built with ❤️ by the AI Orchestration Team**