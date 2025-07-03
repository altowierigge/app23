"""
Advanced Branch Manager for Micro-Phase Workflows.
Handles complex branching strategies, merge conflicts, and Git operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

from .enhanced_github_client import EnhancedGitHubClient, MergeMethod


class BranchType(str, Enum):
    """Types of branches in micro-phase workflow."""
    MAIN = "main"
    DEVELOP = "develop"
    FEATURE = "feature"
    HOTFIX = "hotfix"
    RELEASE = "release"
    EXPERIMENTAL = "experimental"


class MergeStrategy(str, Enum):
    """Merge strategies for different scenarios."""
    AUTO_MERGE = "auto_merge"
    REQUIRE_REVIEW = "require_review"
    MANUAL_ONLY = "manual_only"
    FAST_FORWARD = "fast_forward"


@dataclass
class BranchRule:
    """Rules for branch management."""
    branch_pattern: str
    branch_type: BranchType
    merge_strategy: MergeStrategy
    required_checks: List[str]
    required_reviewers: int
    auto_delete_after_merge: bool = True
    allow_force_push: bool = False
    max_age_days: Optional[int] = None


@dataclass
class ConflictResolution:
    """Conflict resolution strategy."""
    strategy: str  # "auto", "manual", "prefer_ours", "prefer_theirs"
    auto_resolve_patterns: List[str]
    manual_review_patterns: List[str]
    escalation_contacts: List[str]


@dataclass
class BranchStatus:
    """Current status of a branch."""
    name: str
    branch_type: BranchType
    commit_sha: str
    ahead_by: int
    behind_by: int
    has_conflicts: bool
    last_activity: str
    pull_request_number: Optional[int]
    ci_status: str
    review_status: str


class BranchManager:
    """
    Advanced branch management for micro-phase workflows.
    
    Handles branching strategies, conflict resolution, automated merging,
    and complex Git operations across the development lifecycle.
    """
    
    def __init__(self, github_client: EnhancedGitHubClient):
        """Initialize branch manager."""
        self.github_client = github_client
        self.logger = logging.getLogger("branch_manager")
        
        # Default branch rules
        self.branch_rules = self._setup_default_branch_rules()
        
        # Track branch relationships
        self.branch_dependencies: Dict[str, List[str]] = {}
        self.merge_queue: List[str] = []
    
    def _setup_default_branch_rules(self) -> List[BranchRule]:
        """Set up default branch management rules."""
        return [
            BranchRule(
                branch_pattern="main",
                branch_type=BranchType.MAIN,
                merge_strategy=MergeStrategy.REQUIRE_REVIEW,
                required_checks=["ci", "security", "quality"],
                required_reviewers=2,
                auto_delete_after_merge=False,
                allow_force_push=False
            ),
            BranchRule(
                branch_pattern="develop",
                branch_type=BranchType.DEVELOP,
                merge_strategy=MergeStrategy.REQUIRE_REVIEW,
                required_checks=["ci", "lint"],
                required_reviewers=1,
                auto_delete_after_merge=False,
                allow_force_push=False
            ),
            BranchRule(
                branch_pattern="feature/*",
                branch_type=BranchType.FEATURE,
                merge_strategy=MergeStrategy.AUTO_MERGE,
                required_checks=["ci"],
                required_reviewers=1,
                auto_delete_after_merge=True,
                max_age_days=30
            ),
            BranchRule(
                branch_pattern="hotfix/*",
                branch_type=BranchType.HOTFIX,
                merge_strategy=MergeStrategy.FAST_FORWARD,
                required_checks=["ci", "security"],
                required_reviewers=1,
                auto_delete_after_merge=True,
                max_age_days=7
            )
        ]
    
    async def create_micro_phase_branch(self, repo_name: str, phase_info: Dict[str, Any], 
                                       base_branch: str = "develop") -> Dict[str, Any]:
        """
        Create optimized branch for micro-phase development.
        
        Handles naming conventions, dependency tracking, and setup.
        """
        # Generate branch name following conventions
        branch_name = self._generate_branch_name(phase_info)
        
        self.logger.info(f"Creating micro-phase branch: {branch_name}")
        
        # Check for conflicts with existing branches
        existing_branches = await self._get_repository_branches(repo_name)
        if branch_name in existing_branches:
            branch_name = f"{branch_name}-{phase_info.get('session_id', 'unknown')[:8]}"
        
        # Create branch
        branch_result = await self.github_client.create_branch(
            repo_name=repo_name,
            branch_name=branch_name,
            base_branch=base_branch
        )
        
        # Track dependencies
        dependencies = phase_info.get("dependencies", [])
        if dependencies:
            self.branch_dependencies[branch_name] = dependencies
        
        # Apply branch rules
        await self._apply_branch_rules(repo_name, branch_name)
        
        return {
            "branch_name": branch_name,
            "base_branch": base_branch,
            "commit_sha": branch_result["object"]["sha"],
            "dependencies": dependencies,
            "url": f"https://github.com/{await self._get_repo_owner(repo_name)}/{repo_name}/tree/{branch_name}"
        }
    
    async def manage_merge_queue(self, repo_name: str, target_branch: str) -> Dict[str, Any]:
        """
        Manage automated merge queue for validated micro-phases.
        
        Handles dependency ordering, conflict resolution, and batch merging.
        """
        self.logger.info(f"Managing merge queue for {repo_name}:{target_branch}")
        
        # Get all ready-to-merge branches
        ready_branches = await self._get_ready_to_merge_branches(repo_name, target_branch)
        
        # Sort by dependencies and priority
        ordered_branches = self._order_branches_by_dependencies(ready_branches)
        
        merge_results = []
        
        for branch_info in ordered_branches:
            branch_name = branch_info["name"]
            
            try:
                # Check for conflicts
                conflicts = await self._check_merge_conflicts(repo_name, branch_name, target_branch)
                
                if conflicts:
                    # Attempt automatic resolution
                    resolution_result = await self._resolve_conflicts_automatically(
                        repo_name, branch_name, target_branch, conflicts
                    )
                    
                    if not resolution_result["resolved"]:
                        # Add to manual review queue
                        merge_results.append({
                            "branch": branch_name,
                            "status": "conflicts_require_manual_review",
                            "conflicts": conflicts
                        })
                        continue
                
                # Attempt merge
                merge_result = await self._execute_merge(repo_name, branch_info, target_branch)
                merge_results.append(merge_result)
                
                # Remove from dependencies for subsequent branches
                self._update_dependencies_after_merge(branch_name)
                
            except Exception as e:
                self.logger.error(f"Failed to merge {branch_name}: {str(e)}")
                merge_results.append({
                    "branch": branch_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "target_branch": target_branch,
            "processed_branches": len(merge_results),
            "successful_merges": len([r for r in merge_results if r.get("status") == "merged"]),
            "conflicts": len([r for r in merge_results if "conflicts" in r]),
            "results": merge_results
        }
    
    async def handle_conflict_resolution(self, repo_name: str, branch_name: str, 
                                        target_branch: str, 
                                        resolution_strategy: ConflictResolution) -> Dict[str, Any]:
        """
        Handle merge conflict resolution with various strategies.
        """
        self.logger.info(f"Resolving conflicts for {branch_name} -> {target_branch}")
        
        # Get conflict details
        conflicts = await self._get_detailed_conflicts(repo_name, branch_name, target_branch)
        
        resolution_results = []
        
        for conflict in conflicts:
            file_path = conflict["file"]
            conflict_type = conflict["type"]
            
            if resolution_strategy.strategy == "auto":
                # Try automatic resolution based on patterns
                auto_result = await self._try_automatic_resolution(conflict, resolution_strategy)
                resolution_results.append(auto_result)
            
            elif resolution_strategy.strategy == "prefer_ours":
                # Use the version from our branch
                result = await self._resolve_prefer_ours(repo_name, branch_name, file_path)
                resolution_results.append(result)
            
            elif resolution_strategy.strategy == "prefer_theirs":
                # Use the version from target branch
                result = await self._resolve_prefer_theirs(repo_name, target_branch, file_path)
                resolution_results.append(result)
            
            else:
                # Manual resolution required
                resolution_results.append({
                    "file": file_path,
                    "status": "manual_review_required",
                    "conflict_type": conflict_type,
                    "escalation_contacts": resolution_strategy.escalation_contacts
                })
        
        # Check if all conflicts resolved
        unresolved = [r for r in resolution_results if r["status"] != "resolved"]
        
        return {
            "branch": branch_name,
            "target_branch": target_branch,
            "total_conflicts": len(conflicts),
            "resolved_conflicts": len(conflicts) - len(unresolved),
            "unresolved_conflicts": len(unresolved),
            "resolution_details": resolution_results,
            "fully_resolved": len(unresolved) == 0
        }
    
    async def cleanup_stale_branches(self, repo_name: str) -> Dict[str, Any]:
        """
        Clean up stale branches based on age and merge status.
        """
        self.logger.info(f"Cleaning up stale branches for {repo_name}")
        
        branches = await self._get_all_branches_with_metadata(repo_name)
        stale_branches = []
        cleanup_results = []
        
        for branch in branches:
            branch_name = branch["name"]
            
            # Skip protected branches
            if branch_name in ["main", "develop"]:
                continue
            
            # Check if branch is stale
            is_stale = await self._is_branch_stale(branch)
            
            if is_stale:
                stale_branches.append(branch_name)
                
                try:
                    # Check if safe to delete
                    safe_to_delete = await self._is_safe_to_delete(repo_name, branch_name)
                    
                    if safe_to_delete:
                        # Delete the branch
                        await self._delete_branch(repo_name, branch_name)
                        cleanup_results.append({
                            "branch": branch_name,
                            "status": "deleted",
                            "reason": "stale_and_merged"
                        })
                    else:
                        cleanup_results.append({
                            "branch": branch_name,
                            "status": "kept",
                            "reason": "not_safe_to_delete"
                        })
                
                except Exception as e:
                    cleanup_results.append({
                        "branch": branch_name,
                        "status": "error",
                        "error": str(e)
                    })
        
        return {
            "repository": repo_name,
            "total_branches_checked": len(branches),
            "stale_branches_found": len(stale_branches),
            "branches_deleted": len([r for r in cleanup_results if r["status"] == "deleted"]),
            "cleanup_results": cleanup_results
        }
    
    async def get_branch_analytics(self, repo_name: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics about branch usage and health.
        """
        branches = await self._get_all_branches_with_metadata(repo_name)
        
        # Calculate analytics
        analytics = {
            "total_branches": len(branches),
            "branch_types": {},
            "merge_readiness": {
                "ready_to_merge": 0,
                "needs_review": 0,
                "has_conflicts": 0,
                "ci_failing": 0
            },
            "age_distribution": {
                "new": 0,      # < 7 days
                "active": 0,   # 7-30 days
                "old": 0,      # 30-90 days
                "stale": 0     # > 90 days
            },
            "activity_summary": {
                "total_commits": 0,
                "active_prs": 0,
                "merged_prs": 0
            }
        }
        
        for branch in branches:
            # Branch type classification
            branch_type = self._classify_branch_type(branch["name"])
            analytics["branch_types"][branch_type] = analytics["branch_types"].get(branch_type, 0) + 1
            
            # Age classification
            age_category = self._classify_branch_age(branch)
            analytics["age_distribution"][age_category] += 1
            
            # Merge readiness
            readiness = await self._assess_merge_readiness(repo_name, branch)
            analytics["merge_readiness"][readiness] += 1
            
            # Activity metrics
            analytics["activity_summary"]["total_commits"] += branch.get("commit_count", 0)
            if branch.get("pull_request"):
                if branch["pull_request"]["state"] == "open":
                    analytics["activity_summary"]["active_prs"] += 1
                elif branch["pull_request"]["state"] == "merged":
                    analytics["activity_summary"]["merged_prs"] += 1
        
        return analytics
    
    def _generate_branch_name(self, phase_info: Dict[str, Any]) -> str:
        """Generate standardized branch name for micro-phase."""
        phase_type = phase_info.get("phase_type", "feature")
        phase_name = phase_info.get("name", "unknown").lower()
        
        # Clean phase name for Git
        clean_name = re.sub(r'[^a-z0-9-]', '-', phase_name)
        clean_name = re.sub(r'-+', '-', clean_name).strip('-')
        
        return f"{phase_type}/{clean_name}"
    
    async def _get_repository_branches(self, repo_name: str) -> List[str]:
        """Get list of all branches in repository."""
        owner = await self._get_repo_owner(repo_name)
        url = f"{self.github_client.base_url}/repos/{owner}/{repo_name}/branches"
        
        response = await self.github_client._make_request("GET", url)
        return [branch["name"] for branch in response]
    
    async def _get_repo_owner(self, repo_name: str) -> str:
        """Get repository owner."""
        if self.github_client.org:
            return self.github_client.org
        else:
            return await self.github_client._get_authenticated_user_login()
    
    async def _apply_branch_rules(self, repo_name: str, branch_name: str):
        """Apply branch rules based on branch pattern matching."""
        for rule in self.branch_rules:
            if self._branch_matches_pattern(branch_name, rule.branch_pattern):
                # Apply protection rules if needed
                if rule.required_checks or rule.required_reviewers > 0:
                    # Branch protection will be applied at repository level
                    pass
                break
    
    def _branch_matches_pattern(self, branch_name: str, pattern: str) -> bool:
        """Check if branch name matches pattern."""
        if "*" in pattern:
            # Convert glob pattern to regex
            regex_pattern = pattern.replace("*", ".*")
            return re.match(f"^{regex_pattern}$", branch_name) is not None
        else:
            return branch_name == pattern
    
    async def _get_ready_to_merge_branches(self, repo_name: str, target_branch: str) -> List[Dict[str, Any]]:
        """Get branches that are ready to merge."""
        # This would implement actual logic to check PR status, CI status, etc.
        # For now, return empty list as placeholder
        return []
    
    def _order_branches_by_dependencies(self, branches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order branches based on their dependencies."""
        # Implement topological sort based on dependencies
        ordered = []
        remaining = branches.copy()
        
        while remaining:
            # Find branches with no unresolved dependencies
            ready = []
            for branch in remaining:
                branch_name = branch["name"]
                dependencies = self.branch_dependencies.get(branch_name, [])
                
                # Check if all dependencies are already merged
                unresolved_deps = [dep for dep in dependencies 
                                 if not self._is_dependency_resolved(dep, ordered)]
                
                if not unresolved_deps:
                    ready.append(branch)
            
            if not ready:
                # Circular dependency or unresolvable dependencies
                # Add remaining branches anyway to avoid infinite loop
                ordered.extend(remaining)
                break
            
            # Add ready branches to ordered list
            ordered.extend(ready)
            
            # Remove from remaining
            for branch in ready:
                remaining.remove(branch)
        
        return ordered
    
    def _is_dependency_resolved(self, dependency: str, merged_branches: List[Dict[str, Any]]) -> bool:
        """Check if a dependency has been resolved (merged)."""
        for branch in merged_branches:
            if dependency in branch.get("name", ""):
                return True
        return False
    
    async def _check_merge_conflicts(self, repo_name: str, source_branch: str, target_branch: str) -> List[Dict[str, Any]]:
        """Check for merge conflicts between branches."""
        # This would implement actual conflict detection
        # For now, return empty list as placeholder
        return []
    
    async def _resolve_conflicts_automatically(self, repo_name: str, source_branch: str, 
                                             target_branch: str, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Attempt automatic conflict resolution."""
        # This would implement automatic conflict resolution strategies
        return {"resolved": False, "details": "Auto-resolution not implemented"}
    
    async def _execute_merge(self, repo_name: str, branch_info: Dict[str, Any], target_branch: str) -> Dict[str, Any]:
        """Execute merge operation."""
        # This would implement the actual merge logic
        return {
            "branch": branch_info["name"],
            "status": "merged",
            "target_branch": target_branch
        }
    
    def _update_dependencies_after_merge(self, merged_branch: str):
        """Update dependency tracking after successful merge."""
        # Remove the merged branch from dependency lists
        for branch_name, deps in self.branch_dependencies.items():
            if merged_branch in deps:
                deps.remove(merged_branch)
    
    async def _get_detailed_conflicts(self, repo_name: str, source_branch: str, target_branch: str) -> List[Dict[str, Any]]:
        """Get detailed conflict information."""
        # Placeholder implementation
        return []
    
    async def _try_automatic_resolution(self, conflict: Dict[str, Any], 
                                       strategy: ConflictResolution) -> Dict[str, Any]:
        """Try automatic conflict resolution."""
        # Placeholder implementation
        return {"file": conflict["file"], "status": "manual_review_required"}
    
    async def _resolve_prefer_ours(self, repo_name: str, branch_name: str, file_path: str) -> Dict[str, Any]:
        """Resolve conflict by preferring our version."""
        # Placeholder implementation
        return {"file": file_path, "status": "resolved", "method": "prefer_ours"}
    
    async def _resolve_prefer_theirs(self, repo_name: str, target_branch: str, file_path: str) -> Dict[str, Any]:
        """Resolve conflict by preferring their version."""
        # Placeholder implementation
        return {"file": file_path, "status": "resolved", "method": "prefer_theirs"}
    
    async def _get_all_branches_with_metadata(self, repo_name: str) -> List[Dict[str, Any]]:
        """Get all branches with metadata."""
        # Placeholder implementation
        return []
    
    async def _is_branch_stale(self, branch: Dict[str, Any]) -> bool:
        """Check if branch is stale based on age and activity."""
        # Placeholder implementation
        return False
    
    async def _is_safe_to_delete(self, repo_name: str, branch_name: str) -> bool:
        """Check if branch is safe to delete."""
        # Placeholder implementation
        return False
    
    async def _delete_branch(self, repo_name: str, branch_name: str):
        """Delete a branch."""
        owner = await self._get_repo_owner(repo_name)
        url = f"{self.github_client.base_url}/repos/{owner}/{repo_name}/git/refs/heads/{branch_name}"
        await self.github_client._make_request("DELETE", url)
    
    def _classify_branch_type(self, branch_name: str) -> str:
        """Classify branch type based on name."""
        if branch_name.startswith("feature/"):
            return "feature"
        elif branch_name.startswith("hotfix/"):
            return "hotfix"
        elif branch_name.startswith("release/"):
            return "release"
        elif branch_name in ["main", "master"]:
            return "main"
        elif branch_name == "develop":
            return "develop"
        else:
            return "other"
    
    def _classify_branch_age(self, branch: Dict[str, Any]) -> str:
        """Classify branch age."""
        # Placeholder implementation
        return "active"
    
    async def _assess_merge_readiness(self, repo_name: str, branch: Dict[str, Any]) -> str:
        """Assess if branch is ready to merge."""
        # Placeholder implementation
        return "needs_review"