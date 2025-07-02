"""
GitHub integration for AI Orchestrator.
Provides repository management, commit handling, and PR creation for AI-generated projects.
"""

import os
import json
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime

class GitHubIntegration:
    """GitHub integration for AI project management."""
    
    def __init__(self, token: Optional[str] = None, org: Optional[str] = None):
        """Initialize GitHub integration."""
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.org = org or os.getenv('GITHUB_ORG')  # Optional organization
        self.base_url = "https://api.github.com"
        
        if not self.token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get GitHub API headers."""
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def create_repository(self, name: str, description: str = "", private: bool = True) -> Dict[str, Any]:
        """Create a new GitHub repository."""
        url = f"{self.base_url}/user/repos" if not self.org else f"{self.base_url}/orgs/{self.org}/repos"
        
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True,
            "gitignore_template": "Python"
        }
        
        response = requests.post(url, json=data, headers=self._get_headers())
        response.raise_for_status()
        
        return response.json()
    
    def create_branch(self, repo_name: str, branch_name: str, base_branch: str = "main") -> Dict[str, Any]:
        """Create a new branch from base branch."""
        # Get base branch SHA
        owner = self.org or self._get_authenticated_user()["login"]
        base_url = f"{self.base_url}/repos/{owner}/{repo_name}"
        
        # Get base branch reference
        ref_response = requests.get(f"{base_url}/git/refs/heads/{base_branch}", headers=self._get_headers())
        ref_response.raise_for_status()
        base_sha = ref_response.json()["object"]["sha"]
        
        # Create new branch
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        response = requests.post(f"{base_url}/git/refs", json=data, headers=self._get_headers())
        response.raise_for_status()
        
        return response.json()
    
    def commit_files(self, repo_name: str, branch: str, files: Dict[str, str], 
                    commit_message: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Commit multiple files to repository."""
        owner = self.org or self._get_authenticated_user()["login"]
        base_url = f"{self.base_url}/repos/{owner}/{repo_name}"
        
        # Get current branch reference
        ref_response = requests.get(f"{base_url}/git/refs/heads/{branch}", headers=self._get_headers())
        ref_response.raise_for_status()
        current_sha = ref_response.json()["object"]["sha"]
        
        # Create tree with all files
        tree_items = []
        for file_path, content in files.items():
            # Create blob for file content
            blob_data = {"content": content, "encoding": "utf-8"}
            blob_response = requests.post(f"{base_url}/git/blobs", json=blob_data, headers=self._get_headers())
            blob_response.raise_for_status()
            blob_sha = blob_response.json()["sha"]
            
            tree_items.append({
                "path": file_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha
            })
        
        # Create tree
        tree_data = {"tree": tree_items}
        tree_response = requests.post(f"{base_url}/git/trees", json=tree_data, headers=self._get_headers())
        tree_response.raise_for_status()
        tree_sha = tree_response.json()["sha"]
        
        # Create commit with metadata
        full_message = commit_message
        if metadata:
            full_message += f"\n\nAI Metadata:\n{json.dumps(metadata, indent=2)}"
        
        commit_data = {
            "message": full_message,
            "tree": tree_sha,
            "parents": [current_sha]
        }
        
        commit_response = requests.post(f"{base_url}/git/commits", json=commit_data, headers=self._get_headers())
        commit_response.raise_for_status()
        commit_sha = commit_response.json()["sha"]
        
        # Update branch reference
        update_data = {"sha": commit_sha}
        update_response = requests.patch(f"{base_url}/git/refs/heads/{branch}", 
                                       json=update_data, headers=self._get_headers())
        update_response.raise_for_status()
        
        return commit_response.json()
    
    def create_pull_request(self, repo_name: str, title: str, head_branch: str, 
                          base_branch: str = "main", body: str = "") -> Dict[str, Any]:
        """Create a pull request."""
        owner = self.org or self._get_authenticated_user()["login"]
        url = f"{self.base_url}/repos/{owner}/{repo_name}/pulls"
        
        data = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body
        }
        
        response = requests.post(url, json=data, headers=self._get_headers())
        response.raise_for_status()
        
        return response.json()
    
    def add_pr_comment(self, repo_name: str, pr_number: int, comment: str) -> Dict[str, Any]:
        """Add comment to pull request."""
        owner = self.org or self._get_authenticated_user()["login"]
        url = f"{self.base_url}/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
        
        data = {"body": comment}
        
        response = requests.post(url, json=data, headers=self._get_headers())
        response.raise_for_status()
        
        return response.json()
    
    def _get_authenticated_user(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        response = requests.get(f"{self.base_url}/user", headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    def create_ai_project_workflow(self, project_name: str, session_id: str, 
                                 initial_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Create complete AI project workflow:
        1. Create repository
        2. Create initial commit with project structure
        3. Return repository info for further development
        """
        # Create repository
        repo_info = self.create_repository(
            name=f"ai-project-{project_name}-{session_id[:8]}",
            description=f"AI-generated project: {project_name}",
            private=True
        )
        
        # Commit initial project structure
        commit_info = self.commit_files(
            repo_name=repo_info["name"],
            branch="main",
            files=initial_files,
            commit_message="🤖 Initial AI-generated project structure",
            metadata={
                "ai_session_id": session_id,
                "project_name": project_name,
                "generated_at": datetime.utcnow().isoformat(),
                "ai_orchestrator_version": "3.0.0"
            }
        )
        
        return {
            "repository": repo_info,
            "initial_commit": commit_info,
            "clone_url": repo_info["clone_url"],
            "html_url": repo_info["html_url"]
        }


class AICodeReviewer:
    """AI-powered code reviewer for GitHub integration."""
    
    def __init__(self, github_integration: GitHubIntegration):
        self.github = github_integration
    
    def review_files(self, files: Dict[str, str], context: str = "") -> Dict[str, List[str]]:
        """
        Review files and return feedback.
        Returns dict with filename -> list of review comments
        """
        reviews = {}
        
        for filename, content in files.items():
            reviews[filename] = self._review_single_file(filename, content, context)
        
        return reviews
    
    def _review_single_file(self, filename: str, content: str, context: str) -> List[str]:
        """Review single file and return list of comments."""
        comments = []
        
        # Basic code quality checks
        if filename.endswith('.py'):
            comments.extend(self._review_python_file(content))
        elif filename.endswith('.js') or filename.endswith('.jsx'):
            comments.extend(self._review_javascript_file(content))
        elif filename.endswith('.html'):
            comments.extend(self._review_html_file(content))
        
        return comments
    
    def _review_python_file(self, content: str) -> List[str]:
        """Review Python file."""
        comments = []
        
        if 'import *' in content:
            comments.append("❌ Avoid wildcard imports - use specific imports")
        
        if 'print(' in content and 'main.py' not in content:
            comments.append("⚠️ Consider using logging instead of print statements")
        
        if len(content.split('\n')) > 500:
            comments.append("📏 File is quite large - consider breaking into smaller modules")
        
        if 'password' in content.lower() and 'hash' not in content.lower():
            comments.append("🔒 Ensure passwords are properly hashed")
        
        return comments
    
    def _review_javascript_file(self, content: str) -> List[str]:
        """Review JavaScript/React file."""
        comments = []
        
        if 'var ' in content:
            comments.append("💡 Consider using 'const' or 'let' instead of 'var'")
        
        if 'document.getElementById' in content:
            comments.append("⚛️ For React apps, use refs instead of direct DOM manipulation")
        
        if 'console.log' in content:
            comments.append("🔍 Remove console.log statements before production")
        
        return comments
    
    def _review_html_file(self, content: str) -> List[str]:
        """Review HTML file."""
        comments = []
        
        if '<script>' in content:
            comments.append("📦 Consider moving inline scripts to separate files")
        
        if 'http://' in content:
            comments.append("🔒 Use HTTPS instead of HTTP for external resources")
        
        return comments 