"""
GPT Git Agent - Repository Management for micro-phase workflow.
Handles GitHub operations, branch management, and CI/CD integration.
"""

import json
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentRole, AgentTask, TaskType
from ..core.config import OpenAIConfig
from ..utils.enhanced_github_client import EnhancedGitHubClient
from ..utils.repository_manager import RepositoryManager
from ..utils.branch_manager import BranchManager
from ..utils.ci_cd_automation import CICDAutomation


class GPTGitAgent(BaseAgent):
    """
    GPT Git Agent (#3) - Repository Management
    
    Responsibilities:
    - Feature branch creation
    - Pull request management
    - CI/CD monitoring
    - Merge conflict resolution
    - Repository setup and configuration
    """
    
    def __init__(self, config: OpenAIConfig):
        super().__init__(config, AgentRole.GPT_GIT_AGENT)
        self.system_prompts = {
            TaskType.GIT_OPERATION: self._get_git_operation_prompt(),
            TaskType.BRANCH_MANAGEMENT: self._get_branch_management_prompt(),
            TaskType.PULL_REQUEST_CREATION: self._get_pull_request_prompt()
        }
        
        # Initialize GitHub integration components
        self.github_client = EnhancedGitHubClient()
        self.repository_manager = RepositoryManager()
        self.branch_manager = BranchManager(self.github_client)
        self.cicd_automation = CICDAutomation(self.github_client)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get OpenAI API headers."""
        headers = super()._get_headers()
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    async def _make_api_request(self, prompt: str, **kwargs) -> str:
        """Make request to OpenAI API."""
        task_type = kwargs.get('task_type')
        
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": self._get_system_prompt(task_type)},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": 0.1  # Very low temperature for consistent Git operations
        }
        
        response = await self.client.post(
            f"{self.config.base_url}/chat/completions",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def _get_system_prompt(self, task_type: TaskType = None) -> str:
        """Get system prompt based on task type."""
        if task_type and task_type in self.system_prompts:
            return self.system_prompts[task_type]
        
        return """You are the GPT Git Agent, specialized in repository management and GitHub operations. 
        Your role is to handle all Git-related operations for micro-phase development including branch 
        creation, pull requests, and CI/CD integration. You ensure clean Git workflows and proper 
        version control practices. Always provide clear, executable Git commands and strategies."""
    
    def _format_prompt(self, task: AgentTask) -> str:
        """Format prompt based on task type."""
        if task.task_type == TaskType.GIT_OPERATION:
            return self._format_git_operation_prompt(task)
        elif task.task_type == TaskType.BRANCH_MANAGEMENT:
            return self._format_branch_management_prompt(task)
        elif task.task_type == TaskType.PULL_REQUEST_CREATION:
            return self._format_pull_request_prompt(task)
        else:
            return task.prompt
    
    def _format_git_operation_prompt(self, task: AgentTask) -> str:
        """Format Git operation prompt."""
        operation_type = task.context.get('operation_type', 'generic')
        repository_info = task.context.get('repository_info', {})
        micro_phase = task.context.get('micro_phase', {})
        files_to_commit = task.context.get('files_to_commit', [])
        
        return f"""
        Execute Git operations for this micro-phase:
        
        OPERATION TYPE: {operation_type}
        
        REPOSITORY INFO: {json.dumps(repository_info, indent=2)}
        
        MICRO-PHASE: {json.dumps(micro_phase, indent=2)}
        
        FILES TO COMMIT: {json.dumps(files_to_commit, indent=2)}
        
        Provide Git operation strategy covering:
        
        ## BRANCH_STRATEGY
        - What branch should be created or used?
        - How should the branch be named (following conventions)?
        - What is the base branch for this feature?
        - Are there any branch dependencies to consider?
        
        ## COMMIT_STRATEGY
        - How should files be staged and committed?
        - What commit message structure should be used?
        - Should commits be atomic or grouped?
        - Are there any files that should be excluded?
        
        ## GIT_COMMANDS
        Provide the exact Git commands to execute:
        ```bash
        # Example:
        git checkout -b feature/micro-phase-name
        git add file1.py file2.js
        git commit -m "Implement micro-phase: description"
        git push -u origin feature/micro-phase-name
        ```
        
        ## SAFETY_CHECKS
        - What validation should be done before committing?
        - Are there any conflicts to check for?
        - Should any tests be run before pushing?
        - Are there any security considerations?
        
        ## ERROR_HANDLING
        - What could go wrong with these operations?
        - How should conflicts be handled?
        - What fallback strategies are available?
        - How should errors be reported and resolved?
        
        ## REPOSITORY_SETUP
        If this is initial setup:
        - Repository initialization steps
        - Branch protection rules to set
        - CI/CD pipeline configuration
        - Webhook and integration setup
        
        Provide clear, executable instructions that follow Git best practices.
        """
    
    def _format_branch_management_prompt(self, task: AgentTask) -> str:
        """Format branch management prompt."""
        current_branches = task.context.get('current_branches', [])
        target_branch = task.context.get('target_branch', 'develop')
        merge_strategy = task.context.get('merge_strategy', 'pull_request')
        conflict_resolution = task.context.get('conflict_resolution', None)
        
        return f"""
        Manage branch operations and merging strategy:
        
        CURRENT BRANCHES: {json.dumps(current_branches, indent=2)}
        
        TARGET BRANCH: {target_branch}
        
        MERGE STRATEGY: {merge_strategy}
        
        CONFLICT RESOLUTION: {json.dumps(conflict_resolution, indent=2)}
        
        Provide branch management strategy covering:
        
        ## BRANCH_ANALYSIS
        - What is the current state of branches?
        - Are there any conflicting changes?
        - Which branches are ready for merging?
        - Are there any stale or abandoned branches?
        
        ## MERGE_READINESS
        - Are all CI/CD checks passing?
        - Have code reviews been completed?
        - Are there any merge conflicts to resolve?
        - Is the target branch up to date?
        
        ## CONFLICT_RESOLUTION
        If conflicts exist:
        - What types of conflicts are present?
        - How should conflicts be resolved?
        - Which changes should take precedence?
        - Are manual interventions needed?
        
        ## MERGE_EXECUTION
        Provide specific commands for merging:
        ```bash
        # Example merge workflow
        git checkout develop
        git pull origin develop
        git merge feature/branch-name
        git push origin develop
        ```
        
        ## CLEANUP_OPERATIONS
        - Which branches can be safely deleted?
        - How should feature branches be cleaned up?
        - Are there any tags that should be created?
        - What documentation needs updating?
        
        ## INTEGRATION_VALIDATION
        - What tests should run after merging?
        - How can we verify the integration is successful?
        - Are there any rollback procedures needed?
        - What monitoring should be in place?
        
        ## BRANCH_PROTECTION
        - What branch protection rules should be enforced?
        - Who should have merge permissions?
        - What approval requirements are needed?
        - Should there be any automated checks?
        
        Ensure clean, safe branch operations that maintain code quality.
        """
    
    def _format_pull_request_prompt(self, task: AgentTask) -> str:
        """Format pull request creation and management prompt."""
        micro_phase = task.context.get('micro_phase', {})
        changes_summary = task.context.get('changes_summary', '')
        source_branch = task.context.get('source_branch', '')
        target_branch = task.context.get('target_branch', 'develop')
        validation_results = task.context.get('validation_results', {})
        
        return f"""
        Create and manage pull request for this micro-phase:
        
        MICRO-PHASE: {json.dumps(micro_phase, indent=2)}
        
        SOURCE BRANCH: {source_branch}
        TARGET BRANCH: {target_branch}
        
        CHANGES SUMMARY: {changes_summary}
        
        VALIDATION RESULTS: {json.dumps(validation_results, indent=2)}
        
        Create comprehensive pull request covering:
        
        ## PR_TITLE
        Create a clear, descriptive title:
        - Include micro-phase name and purpose
        - Follow project naming conventions
        - Be specific about what was implemented
        
        ## PR_DESCRIPTION
        Write detailed description including:
        
        ### Summary
        - What does this micro-phase implement?
        - Why was this approach chosen?
        - What are the key changes?
        
        ### Changes Made
        - List of files modified/added/deleted
        - Key functionality implemented
        - Configuration changes
        - Database migrations (if any)
        
        ### Testing
        - What testing was performed?
        - Are automated tests included?
        - Manual testing procedures
        - Edge cases considered
        
        ### Integration Notes
        - How does this integrate with other phases?
        - Any breaking changes?
        - Dependencies added or updated
        - API changes or new endpoints
        
        ### Deployment Notes
        - Any special deployment considerations?
        - Environment variable changes
        - Database updates required
        - Migration procedures
        
        ## REVIEWERS_AND_LABELS
        - Who should review this PR?
        - What labels should be applied?
        - What milestone should this be associated with?
        - Are there any special review requirements?
        
        ## CI_CD_INTEGRATION
        - What automated checks should run?
        - Are there any specific test requirements?
        - Should this trigger any deployments?
        - What quality gates must pass?
        
        ## MERGE_STRATEGY
        - When is this ready to merge?
        - What approval process is required?
        - Should this be squash merged or regular merge?
        - Are there any dependencies on other PRs?
        
        ## DOCUMENTATION_UPDATES
        - What documentation needs updating?
        - Are there any README changes needed?
        - Should API documentation be updated?
        - Are there any architectural diagrams to update?
        
        ## GITHUB_CLI_COMMANDS
        Provide the exact GitHub CLI commands:
        ```bash
        gh pr create \\
          --title "Title here" \\
          --body "Description here" \\
          --base develop \\
          --head feature/branch-name \\
          --label "enhancement" \\
          --reviewer @username
        ```
        
        Create professional, comprehensive pull requests that facilitate smooth code review and integration.
        """
    
    def _get_git_operation_prompt(self) -> str:
        """System prompt for Git operations."""
        return """You are the GPT Git Agent specialized in Git operations and version control. You have deep 
        expertise in Git workflows, branching strategies, and best practices. Your role is to execute Git 
        operations safely and efficiently while maintaining clean repository history. Always provide specific, 
        executable commands with proper error handling."""
    
    def _get_branch_management_prompt(self) -> str:
        """System prompt for branch management."""
        return """You are the GPT Git Agent specialized in branch management and merging strategies. You 
        understand complex branching workflows, conflict resolution, and integration procedures. Your role is 
        to ensure smooth branch operations while maintaining code quality and repository integrity. Focus on 
        safe, reversible operations."""
    
    def _get_pull_request_prompt(self) -> str:
        """System prompt for pull request management."""
        return """You are the GPT Git Agent specialized in pull request creation and management. You understand 
        code review processes, CI/CD integration, and collaborative development workflows. Your role is to create 
        comprehensive, reviewable pull requests that facilitate smooth integration and maintain project quality. 
        Always include thorough documentation and context."""
    
    def get_capabilities(self) -> List[TaskType]:
        """GPT Git Agent capabilities."""
        return [
            TaskType.GIT_OPERATION,
            TaskType.BRANCH_MANAGEMENT,
            TaskType.PULL_REQUEST_CREATION
        ]
    
    async def create_branch_strategy(self, micro_phase: Dict[str, Any], repository_state: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to create branching strategy for a micro-phase."""
        phase_name = micro_phase.get('name', 'unknown-phase')
        phase_type = micro_phase.get('phase_type', 'feature')
        
        # Generate branch name following conventions
        branch_name = f"feature/{phase_type}-{phase_name.lower().replace(' ', '-')}"
        
        return {
            "branch_name": branch_name,
            "base_branch": "develop",
            "merge_strategy": "pull_request",
            "protection_rules": {
                "require_reviews": True,
                "require_ci_checks": True,
                "restrict_pushes": True
            }
        }
    
    async def execute_real_git_operations(self, task: AgentTask) -> Dict[str, Any]:
        """Execute real GitHub operations using integrated services."""
        operation_type = task.context.get('operation_type', 'generic')
        
        if operation_type == "create_repository":
            return await self._handle_repository_creation(task)
        elif operation_type == "micro_phase_commit":
            return await self._handle_micro_phase_commit(task)
        elif operation_type == "create_pull_request":
            return await self._handle_pull_request_creation(task)
        elif operation_type == "merge_management":
            return await self._handle_merge_management(task)
        else:
            # Fall back to AI-generated instructions
            return await self._generate_git_instructions(task)
    
    async def _handle_repository_creation(self, task: AgentTask) -> Dict[str, Any]:
        """Handle repository creation with full setup."""
        project_config = task.context.get('project_config', {})
        
        # Use repository manager to create and set up repository
        setup_result = await self.repository_manager.setup_micro_phase_project(project_config)
        
        return {
            "operation": "repository_created",
            "repository_url": setup_result.repository_url,
            "repository_name": setup_result.repository_name,
            "branches_created": setup_result.created_branches,
            "ci_cd_enabled": setup_result.ci_cd_status == "active",
            "protection_enabled": setup_result.protection_enabled
        }
    
    async def _handle_micro_phase_commit(self, task: AgentTask) -> Dict[str, Any]:
        """Handle micro-phase commit and PR creation."""
        session_id = task.session_id
        micro_phase = task.context.get('micro_phase', {})
        generated_files = task.context.get('generated_files', {})
        
        # Execute micro-phase workflow
        workflow_result = await self.repository_manager.execute_micro_phase_workflow(
            session_id=session_id,
            micro_phase=micro_phase,
            generated_files=generated_files
        )
        
        return {
            "operation": "micro_phase_committed",
            "branch_name": workflow_result["branch_name"],
            "commit_sha": workflow_result["commit_sha"],
            "pull_request": workflow_result["pull_request"],
            "files_committed": workflow_result["files_committed"],
            "repository_url": workflow_result["repository_url"]
        }
    
    async def _handle_pull_request_creation(self, task: AgentTask) -> Dict[str, Any]:
        """Handle pull request creation with automation."""
        repo_name = task.context.get('repository_name', '')
        phase_info = task.context.get('phase_info', {})
        
        # Create pull request using GitHub client
        pr_result = await self.github_client.create_micro_phase_pull_request(
            repo_name=repo_name,
            phase_info=phase_info,
            head_branch=phase_info.get('branch_name', ''),
            base_branch="develop"
        )
        
        return {
            "operation": "pull_request_created",
            "pr_number": pr_result["number"],
            "pr_url": pr_result["html_url"],
            "title": pr_result["title"]
        }
    
    async def _handle_merge_management(self, task: AgentTask) -> Dict[str, Any]:
        """Handle merge queue management."""
        repo_name = task.context.get('repository_name', '')
        target_branch = task.context.get('target_branch', 'develop')
        
        # Use branch manager for merge queue
        merge_result = await self.branch_manager.manage_merge_queue(repo_name, target_branch)
        
        return {
            "operation": "merge_management",
            "target_branch": merge_result["target_branch"],
            "processed_branches": merge_result["processed_branches"],
            "successful_merges": merge_result["successful_merges"],
            "conflicts": merge_result["conflicts"],
            "results": merge_result["results"]
        }
    
    async def _generate_git_instructions(self, task: AgentTask) -> Dict[str, Any]:
        """Generate AI-powered Git instructions as fallback."""
        # Call the original AI agent for instruction generation
        response = await super().execute_task(task)
        
        return {
            "operation": "ai_instructions_generated",
            "instructions": response.content,
            "task_type": task.task_type.value
        }
    
    async def validate_git_state(self, repository_path: str) -> Dict[str, Any]:
        """Helper method to validate current Git repository state."""
        # This would be implemented with actual Git operations
        return {
            "is_clean": True,
            "current_branch": "develop",
            "uncommitted_changes": [],
            "unpushed_commits": 0,
            "remote_status": "up_to_date"
        }
    
    async def cleanup(self):
        """Cleanup GitHub integration resources."""
        await super().cleanup()
        await self.github_client.cleanup()
        await self.repository_manager.cleanup()
        await self.branch_manager.cleanup() if hasattr(self.branch_manager, 'cleanup') else None