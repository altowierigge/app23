# Quick Start Guide

Get up and running with the AI Orchestration System in under 5 minutes!

## 🚀 Prerequisites

- **Python 3.11+** installed
- **Git** installed
- **API Keys** for at least one AI service:
  - OpenAI API key (recommended)
  - Anthropic API key
  - Google Gemini API key

## ⚡ Quick Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd ai-orchestrator

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env  # or use your preferred editor
```

**Minimum required configuration:**
```env
# At least one AI service API key is required
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  
GOOGLE_API_KEY=your_google_api_key_here

# Basic settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
OUTPUT_DIR=./output
```

### 3. Verify Setup

```bash
# Run system diagnostics
python main.py doctor --check-apis --check-git

# Expected output:
# ✅ OpenAI API key configured
# ✅ System health check passed
```

## 🎯 Quick Test

### Option 1: Web Interface (Recommended)

```bash
# Start the web service
python main.py serve --port 8000

# Open your browser to:
# http://localhost:8000
```

**Create your first project:**
1. Navigate to the dashboard
2. Enter a project description: *"Create a simple todo application with user authentication"*
3. Click "Start AI Orchestration"
4. Watch the real-time progress!

### Option 2: Command Line

```bash
# Generate a project via CLI
python main.py generate "Create a simple calculator web app"

# Monitor progress
python main.py status <session-id>

# View metrics
python main.py metrics
```

### Option 3: Python API

```python
import asyncio
from ai_orchestrator import AIOrchestrator, setup_logging

async def main():
    setup_logging()
    
    orchestrator = AIOrchestrator()
    session_id = await orchestrator.start_workflow(
        "Create a blog platform with user management"
    )
    
    print(f"Workflow started: {session_id}")

asyncio.run(main())
```

## 🐳 Docker Quick Start

If you prefer containerized deployment:

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Deploy with Docker
./scripts/deploy.sh development

# Access the dashboard
# http://localhost:8000
```

## 📊 What Happens Next?

Once you start a workflow, the system will:

1. **🤖 GPT-4** refines your requirements
2. **🧠 Claude** designs the backend architecture  
3. **✨ Gemini** creates the frontend design
4. **⚖️ AI Agents** compare and vote on approaches
5. **💻 Implementation** generates complete code
6. **🧪 Testing** creates comprehensive test suites
7. **📁 Output** saves structured project files
8. **📚 Git** optionally creates repository

## 📁 Generated Output

Your projects are saved in the `output/` directory:

```
output/
└── ai-generated-project-abc123/
    ├── backend/
    │   ├── src/
    │   ├── tests/
    │   ├── requirements.txt
    │   └── README.md
    ├── frontend/
    │   ├── src/
    │   ├── public/
    │   ├── package.json
    │   └── README.md
    ├── docs/
    │   ├── architecture.md
    │   └── api.md
    └── docker-compose.yml
```

## 🔍 Troubleshooting

### Common Issues

**❌ "API key not configured"**
```bash
# Check your .env file
cat .env | grep API_KEY

# Verify environment loading
python -c "from ai_orchestrator.core.config import get_config; print(get_config().openai.api_key[:10])"
```

**❌ "Module not found"**
```bash
# Ensure you're in the project directory
pwd

# Reinstall dependencies
pip install -r requirements.txt
```

**❌ "Port already in use"**
```bash
# Use a different port
python main.py serve --port 8001

# Or kill the existing process
lsof -ti:8000 | xargs kill
```

**❌ "Permission denied"**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Check file permissions
ls -la scripts/
```

### Health Check

```bash
# Run comprehensive diagnostics
python main.py doctor --check-apis --check-git --check-github

# Check system status via API
curl http://localhost:8000/api/health | jq
```

### Log Analysis

```bash
# View application logs
tail -f logs/ai_orchestrator.log

# View error logs
tail -f logs/errors.log

# View metrics
tail -f logs/metrics.log
```

## 🎯 Next Steps

Now that you're up and running:

1. **🎨 Explore the Dashboard** - Try different project types
2. **📖 Read the User Guide** - Learn advanced features
3. **🔧 Configure Settings** - Customize your workflow
4. **📊 Monitor Performance** - Check system metrics
5. **🚀 Deploy to Production** - Use Docker deployment

## 💡 Pro Tips

- **Start Simple**: Begin with basic projects like "todo app" or "calculator"
- **Monitor Progress**: Use the web dashboard for real-time updates
- **Check Logs**: Watch the logs for detailed execution information
- **Experiment**: Try different project descriptions to see how AI agents respond
- **Save Time**: Use the CLI for batch operations and automation

## 🆘 Getting Help

- **Documentation**: Browse the [full documentation](../README.md)
- **Examples**: Check out [example projects](../user-guide/examples.md)
- **API Reference**: See [API documentation](../api/rest-api.md)
- **Issues**: Report problems on GitHub Issues

---

**🎉 You're ready to start building with AI! 🎉**