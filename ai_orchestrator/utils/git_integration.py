"""
Git integration for automated repository management and GitHub integration.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    import git
    from git import Repo
    GIT_AVAILABLE = True
except ImportError:
    git = None
    Repo = None
    GIT_AVAILABLE = False

try:
    import github
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    github = None
    Github = None
    GITHUB_AVAILABLE = False

from ..core.config import get_config
from .logging_config import get_logger, TimedOperation
from .file_manager import ProjectStructure


@dataclass
class GitRepository:
    """Represents a Git repository with metadata."""
    local_path: str
    remote_url: Optional[str] = None
    branch: str = "main"
    commit_hash: Optional[str] = None
    github_repo: Optional[str] = None  # format: "owner/repo"


@dataclass
class CommitInfo:
    """Information about a Git commit."""
    hash: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]


class GitManager:
    """Manages Git operations for AI-generated projects."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("git_manager")
        
        if not GIT_AVAILABLE:
            self.logger.warning("GitPython not available. Git operations will be disabled.")
        
        # Configure Git user if not set
        self._configure_git_user()
    
    def _configure_git_user(self):
        """Configure Git user for commits."""
        try:
            # Check if Git user is configured
            result = subprocess.run(['git', 'config', 'user.name'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                # Set default user
                subprocess.run(['git', 'config', '--global', 'user.name', 'AI Orchestrator'], 
                             check=True)
                subprocess.run(['git', 'config', '--global', 'user.email', 'ai-orchestrator@example.com'], 
                             check=True)
                self.logger.info("Configured default Git user")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to configure Git user: {str(e)}")
    
    def initialize_repository(self, project_path: str, project: ProjectStructure) -> GitRepository:
        """Initialize a Git repository for the project."""
        if not GIT_AVAILABLE:
            raise RuntimeError("GitPython not available")
        
        with TimedOperation("initialize_git_repo", {"project": project.name}):
            try:
                # Initialize repository
                repo = Repo.init(project_path)
                
                # Create .gitignore if not exists
                gitignore_path = Path(project_path) / '.gitignore'
                if not gitignore_path.exists():
                    self._create_default_gitignore(gitignore_path)
                
                # Add all files
                repo.git.add(A=True)
                
                # Initial commit
                commit_message = self._generate_commit_message(project)
                commit = repo.index.commit(commit_message)
                
                git_repo = GitRepository(
                    local_path=project_path,
                    branch="main",
                    commit_hash=commit.hexsha
                )
                
                self.logger.info(f"Initialized Git repository: {project_path}")
                return git_repo
                
            except Exception as e:
                self.logger.error(f"Failed to initialize Git repository: {str(e)}")
                raise
    
    def commit_changes(self, repo_path: str, message: Optional[str] = None) -> CommitInfo:
        """Commit changes in the repository."""
        if not GIT_AVAILABLE:
            raise RuntimeError("GitPython not available")
        
        try:
            repo = Repo(repo_path)
            
            # Check for changes
            if not repo.is_dirty() and not repo.untracked_files:
                self.logger.info("No changes to commit")
                return None
            
            # Add all changes
            repo.git.add(A=True)
            
            # Generate commit message if not provided
            if not message:
                message = f"Auto-commit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Commit
            commit = repo.index.commit(message)
            
            commit_info = CommitInfo(
                hash=commit.hexsha,
                message=commit.message.strip(),
                author=str(commit.author),
                timestamp=datetime.fromtimestamp(commit.committed_date),
                files_changed=list(repo.git.diff('HEAD~1', '--name-only').split('\n'))
            )
            
            self.logger.info(f"Committed changes: {commit.hexsha[:8]} - {message}")
            return commit_info
            
        except Exception as e:
            self.logger.error(f"Failed to commit changes: {str(e)}")
            raise
    
    def create_branch(self, repo_path: str, branch_name: str) -> str:
        """Create and checkout a new branch."""
        if not GIT_AVAILABLE:
            raise RuntimeError("GitPython not available")
        
        try:
            repo = Repo(repo_path)
            
            # Create new branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            self.logger.info(f"Created and checked out branch: {branch_name}")
            return branch_name
            
        except Exception as e:
            self.logger.error(f"Failed to create branch: {str(e)}")
            raise
    
    def _create_default_gitignore(self, gitignore_path: Path):
        """Create a default .gitignore file."""
        gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.pyc
.Python
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Environment
.env
.env.local

# Build
build/
dist/
*.egg-info/

# Database
*.db
*.sqlite

# Temporary
tmp/
*.tmp
"""
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
    
    def _generate_commit_message(self, project: ProjectStructure) -> str:
        """Generate a descriptive commit message."""
        template = self.config.git.repository_template
        
        message = f"""Initial commit: AI-generated project

Project: {project.name}
Session: {project.session_id}
Generated: {project.created_at.isoformat()}

Features:
- Backend API implementation
- Frontend user interface  
- Comprehensive test suite
- Docker configuration
- Documentation

AI Agents:
- GPT-4: Project management and testing
- Claude: Backend development
- Gemini: Frontend development

Files: {len(project.files)} files generated
"""
        return message


class GitHubIntegration:
    """Handles GitHub-specific operations and repository management."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("github_integration")
        
        if not GITHUB_AVAILABLE:
            self.logger.warning("PyGithub not available. GitHub operations will be disabled.")
            self.github_client = None
        elif self.config.git.github_token:
            try:
                self.github_client = Github(self.config.git.github_token)
                # Test authentication
                user = self.github_client.get_user()
                self.logger.info(f"GitHub integration initialized for user: {user.login}")
            except Exception as e:
                self.logger.error(f"Failed to initialize GitHub client: {str(e)}")
                self.github_client = None
        else:
            self.logger.info("No GitHub token provided. GitHub operations will be disabled.")
            self.github_client = None
    
    def create_repository(self, project: ProjectStructure, 
                         repo_name: Optional[str] = None,
                         private: bool = True,
                         description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new GitHub repository."""
        if not self.github_client:
            raise RuntimeError("GitHub client not available")
        
        if not repo_name:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            repo_name = f"ai-generated-{timestamp}"
        
        if not description:
            description = f"AI-generated project from session {project.session_id}"
        
        with TimedOperation("create_github_repo", {"repo_name": repo_name}):
            try:
                user = self.github_client.get_user()
                
                # Create repository
                repo = user.create_repo(
                    name=repo_name,
                    description=description,
                    private=private,
                    auto_init=False,  # We'll push our own initial commit
                    has_issues=True,
                    has_wiki=True,
                    has_downloads=True
                )
                
                repo_info = {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "html_url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "ssh_url": repo.ssh_url,
                    "description": repo.description,
                    "private": repo.private
                }
                
                self.logger.info(f"Created GitHub repository: {repo.full_name}")
                return repo_info
                
            except Exception as e:
                self.logger.error(f"Failed to create GitHub repository: {str(e)}")
                raise
    
    def push_to_github(self, local_repo_path: str, github_repo_url: str, 
                      branch: str = "main") -> bool:
        """Push local repository to GitHub."""
        if not GIT_AVAILABLE:
            raise RuntimeError("GitPython not available")
        
        with TimedOperation("push_to_github", {"repo_url": github_repo_url}):
            try:
                repo = Repo(local_repo_path)
                
                # Add remote if not exists
                try:
                    origin = repo.remote('origin')
                except:
                    origin = repo.create_remote('origin', github_repo_url)
                
                # Push to GitHub
                origin.push(f"refs/heads/{branch}:refs/heads/{branch}")
                
                self.logger.info(f"Pushed to GitHub: {github_repo_url}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to push to GitHub: {str(e)}")
                return False
    
    def create_release(self, repo_full_name: str, tag_name: str, 
                      release_name: str, description: str) -> Dict[str, Any]:
        """Create a GitHub release."""
        if not self.github_client:
            raise RuntimeError("GitHub client not available")
        
        try:
            repo = self.github_client.get_repo(repo_full_name)
            
            release = repo.create_git_release(
                tag=tag_name,
                name=release_name,
                message=description,
                draft=False,
                prerelease=False
            )
            
            release_info = {
                "id": release.id,
                "tag_name": release.tag_name,
                "name": release.title,
                "html_url": release.html_url,
                "upload_url": release.upload_url
            }
            
            self.logger.info(f"Created GitHub release: {tag_name}")
            return release_info
            
        except Exception as e:
            self.logger.error(f"Failed to create GitHub release: {str(e)}")
            raise
    
    def add_repository_topics(self, repo_full_name: str, topics: List[str]):
        """Add topics to a GitHub repository."""
        if not self.github_client:
            raise RuntimeError("GitHub client not available")
        
        try:
            repo = self.github_client.get_repo(repo_full_name)
            
            # Add AI-related topics
            default_topics = ["ai-generated", "automated", "ai-orchestration"]
            all_topics = list(set(default_topics + topics))
            
            repo.replace_topics(all_topics)
            
            self.logger.info(f"Added topics to repository: {', '.join(all_topics)}")
            
        except Exception as e:
            self.logger.error(f"Failed to add repository topics: {str(e)}")


class ProjectPublisher:
    """High-level interface for publishing AI-generated projects."""
    
    def __init__(self):
        self.config = get_config()
        self.git_manager = GitManager()
        self.github_integration = GitHubIntegration()
        self.logger = get_logger("project_publisher")
    
    def publish_project(self, project: ProjectStructure, project_path: str, 
                       push_to_github: bool = None) -> Dict[str, Any]:
        """Complete project publishing workflow."""
        if push_to_github is None:
            push_to_github = self.config.git.auto_push
        
        publish_result = {
            "local_repo": None,
            "github_repo": None,
            "success": False,
            "errors": []
        }
        
        try:
            # Initialize Git repository
            if GIT_AVAILABLE:
                git_repo = self.git_manager.initialize_repository(project_path, project)
                publish_result["local_repo"] = {
                    "path": git_repo.local_path,
                    "commit_hash": git_repo.commit_hash
                }
                self.logger.info("Git repository initialized")
            
            # Push to GitHub if enabled
            if push_to_github and self.github_integration.github_client:
                # Create GitHub repository
                github_repo = self.github_integration.create_repository(project)
                
                # Push local repository to GitHub
                if GIT_AVAILABLE:
                    success = self.github_integration.push_to_github(
                        project_path, 
                        github_repo["clone_url"]
                    )
                    
                    if success:
                        publish_result["github_repo"] = github_repo
                        
                        # Add relevant topics
                        topics = self._extract_topics_from_project(project)
                        self.github_integration.add_repository_topics(
                            github_repo["full_name"], 
                            topics
                        )
                        
                        self.logger.info(f"Project published to GitHub: {github_repo['html_url']}")
            
            publish_result["success"] = True
            
        except Exception as e:
            error_msg = f"Failed to publish project: {str(e)}"
            self.logger.error(error_msg)
            publish_result["errors"].append(error_msg)
        
        return publish_result
    
    def _extract_topics_from_project(self, project: ProjectStructure) -> List[str]:
        """Extract relevant topics from project structure."""
        topics = []
        
        # Check for technologies used
        file_extensions = set()
        for file in project.files:
            if '.' in file.path:
                ext = file.path.split('.')[-1].lower()
                file_extensions.add(ext)
        
        # Map extensions to topics
        tech_mapping = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'react',
            'tsx': 'react',
            'css': 'css',
            'scss': 'sass',
            'html': 'html',
            'yml': 'docker',
            'yaml': 'docker',
            'json': 'json'
        }
        
        for ext in file_extensions:
            if ext in tech_mapping:
                topics.append(tech_mapping[ext])
        
        # Check for frameworks
        if any('react' in f.path.lower() or 'jsx' in f.path for f in project.files):
            topics.append('react')
        
        if any('fastapi' in f.content.lower() or 'uvicorn' in f.content.lower() for f in project.files):
            topics.append('fastapi')
        
        if any('docker' in f.path.lower() for f in project.files):
            topics.append('docker')
        
        return list(set(topics))  # Remove duplicates