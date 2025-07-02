"""
Setup configuration for the AI Orchestration System.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.1",
        "httpx>=0.25.2",
        "tenacity>=8.2.3",
        "click>=8.1.7"
    ]

setup(
    name="ai-orchestrator",
    version="1.0.0",
    description="Advanced AI orchestration system for multi-agent software development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AI Orchestration Team",
    author_email="ai-orchestrator@example.com",
    url="https://github.com/ai-orchestrator/ai-orchestrator",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "git": ["GitPython>=3.1.40", "PyGithub>=1.59.1"],
        "web": ["fastapi>=0.104.1", "uvicorn[standard]>=0.24.0"],
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1", 
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0"
        ],
        "docs": ["mkdocs>=1.5.3", "mkdocs-material>=9.4.8"]
    },
    entry_points={
        "console_scripts": [
            "ai-orchestrator=ai_orchestrator.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai, orchestration, multi-agent, code-generation, gpt, claude, gemini",
    project_urls={
        "Bug Reports": "https://github.com/ai-orchestrator/ai-orchestrator/issues",
        "Source": "https://github.com/ai-orchestrator/ai-orchestrator",
        "Documentation": "https://ai-orchestrator.readthedocs.io/",
    },
    include_package_data=True,
    package_data={
        "ai_orchestrator": ["workflows/*.yaml", "templates/*"],
    },
)