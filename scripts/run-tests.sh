#!/bin/bash
# Test runner script for AI Orchestration System

set -e

echo "🧪 Running AI Orchestration System Tests"
echo "========================================="

# Change to project directory
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "📥 Installing test dependencies..."
pip install pytest pytest-asyncio pytest-cov black flake8 mypy

# Run code formatting check
echo "🎨 Checking code formatting with Black..."
black --check ai_orchestrator/ tests/ || {
    echo "❌ Code formatting issues found. Run 'black ai_orchestrator/ tests/' to fix."
    exit 1
}

# Run linting
echo "🔍 Running linting with Flake8..."
flake8 ai_orchestrator/ tests/ --max-line-length=100 --ignore=E203,W503

# Run type checking
echo "🔎 Running type checking with MyPy..."
mypy ai_orchestrator/ --ignore-missing-imports

# Run unit tests
echo "🧪 Running unit tests..."
pytest tests/unit/ -v --cov=ai_orchestrator --cov-report=term-missing --cov-report=html

# Run integration tests
if [ -f "tests/integration/test_integration.py" ]; then
    echo "🔗 Running integration tests..."
    pytest tests/integration/ -v
fi

# Generate coverage report
echo "📊 Coverage report generated in htmlcov/"

echo "✅ All tests passed!"
echo ""
echo "📋 Test Summary:"
echo "  - Code formatting: ✅"
echo "  - Linting: ✅" 
echo "  - Type checking: ✅"
echo "  - Unit tests: ✅"
echo "  - Integration tests: ✅"
echo ""
echo "🎉 Ready for deployment!"