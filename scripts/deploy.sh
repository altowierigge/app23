#!/bin/bash
# Deployment script for AI Orchestration System

set -e

echo "🚀 Deploying AI Orchestration System"
echo "====================================="

# Configuration
ENV=${1:-production}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENV" = "development" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
fi

echo "📋 Environment: $ENV"
echo "📄 Using: $COMPOSE_FILE"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and configuration"
    echo "   Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY"
    exit 1
fi

# Check for required environment variables
echo "🔍 Checking environment variables..."
if [ -z "$OPENAI_API_KEY" ] && [ -z "$(grep OPENAI_API_KEY .env)" ]; then
    echo "❌ OPENAI_API_KEY not found in environment or .env file"
    exit 1
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose -f $COMPOSE_FILE build

echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Running health check..."
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ AI Orchestration System is healthy!"
else
    echo "❌ Health check failed. Checking logs..."
    docker-compose -f $COMPOSE_FILE logs ai-orchestrator
    exit 1
fi

# Show status
echo ""
echo "📊 Service Status:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "🌐 Access Points:"
echo "  - Web Dashboard: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/api/docs"
echo "  - Health Check: http://localhost:8000/api/health"
echo ""
echo "📋 Management Commands:"
echo "  - View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  - Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  - Restart: docker-compose -f $COMPOSE_FILE restart"
echo ""
echo "🔧 Next Steps:"
echo "  1. Configure your API keys in the web dashboard"
echo "  2. Run system diagnostics at /api/health"
echo "  3. Create your first AI-generated project!"