# 🔑 API Key Setup Guide

## Required API Keys

Your AI Orchestrator needs API keys from three services to function:

### 1. 🤖 OpenAI (GPT-4) - Project Manager Agent
**Role**: Requirements refinement, plan comparison, conflict resolution
- **Get Key**: https://platform.openai.com/api-keys
- **Cost**: ~$0.03 per 1K tokens
- **Required**: Yes

### 2. 🧠 Anthropic (Claude) - Backend Expert Agent  
**Role**: Backend architecture, API development, database design
- **Get Key**: https://console.anthropic.com/
- **Cost**: ~$0.015 per 1K tokens
- **Required**: Yes

### 3. ✨ Google (Gemini) - Frontend Expert Agent
**Role**: Frontend design, user interface, user experience
- **Get Key**: https://makersuite.google.com/app/apikey
- **Cost**: Free tier available
- **Required**: Yes

## 🚀 Quick Setup

1. **Create environment file**:
```bash
cp .env.example .env
```

2. **Edit `.env` file** with your keys:
```env
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-api-key-here
```

3. **Test the setup**:
```bash
python -m ai_orchestrator.cli doctor --check-apis
```

## 💡 Pro Tips

- **Start with one API key** if you want to test gradually
- **Use environment variables** for security in production
- **Monitor usage** - each service has different pricing
- **Free tiers available** - Google Gemini has generous free limits

## 🔧 Troubleshooting

**"API key not configured"**
- Check your `.env` file exists in the project root
- Verify no extra spaces around the `=` sign
- Restart the application after adding keys

**"HTTP Status Error"** 
- Verify the API key is valid and active
- Check your account has sufficient credits/quota
- Ensure the key has the right permissions

## 🎯 What's Next?

Once your API keys are configured:
1. Run a test workflow: `python main.py`
2. Access web dashboard: http://localhost:8000
3. Generate your first project! 