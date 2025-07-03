"""
Advanced Caching System for Micro-Phase Workflows.
Provides intelligent caching, versioning, dependency tracking, and cost optimization.
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles

from ..agents.base_agent import MicroPhase


class CacheStatus(str, Enum):
    """Cache entry status."""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"
    MISSING_DEPENDENCIES = "missing_dependencies"


class CacheLevel(str, Enum):
    """Cache levels for different data types."""
    SESSION = "session"          # Entire session data
    WORKFLOW = "workflow"        # Workflow phase results
    AGENT = "agent"             # Individual agent responses
    MICRO_PHASE = "micro_phase" # Individual micro-phase outputs
    FILE = "file"               # Generated files


@dataclass
class CacheMetadata:
    """Metadata for cached entries."""
    cache_key: str
    created_at: str
    updated_at: str
    agent_type: str
    agent_version: str
    prompt_hash: str
    dependencies: List[str]
    session_id: str
    validation_status: str
    expiry_time: Optional[str] = None
    file_count: int = 0
    size_bytes: int = 0
    access_count: int = 0
    last_accessed: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class CacheStats:
    """Cache performance statistics."""
    total_entries: int
    hit_rate: float
    miss_rate: float
    total_size_mb: float
    avg_access_time_ms: float
    cost_savings_usd: float
    api_calls_saved: int


class CacheManager:
    """
    Advanced cache manager for micro-phase workflows.
    
    Provides intelligent caching with dependency tracking, versioning,
    health checks, and cost optimization analytics.
    """
    
    def __init__(self, cache_root: str = "/tmp/ai_orchestrator_cache"):
        """Initialize cache manager."""
        self.cache_root = Path(cache_root)
        self.logger = logging.getLogger("cache_manager")
        
        # Cache structure
        self.cache_dirs = {
            "metadata": self.cache_root / "metadata",
            "brainstorming": self.cache_root / "brainstorming", 
            "architecture": self.cache_root / "architecture",
            "phases": self.cache_root / "phases",
            "integration": self.cache_root / "integration",
            "files": self.cache_root / "files",
            "analytics": self.cache_root / "analytics"
        }
        
        # Cache index and dependency tracking
        self.cache_index: Dict[str, CacheMetadata] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Performance tracking
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "cost_savings": 0.0,
            "api_calls_saved": 0
        }
        
        # Configuration
        self.config = {
            "max_cache_size_gb": 10.0,
            "default_expiry_hours": 72,
            "cleanup_interval_hours": 24,
            "compression_enabled": True,
            "analytics_enabled": True
        }
        
        # Initialize cache
        asyncio.create_task(self._initialize_cache())
    
    async def _initialize_cache(self):
        """Initialize cache directories and load existing index."""
        try:
            # Create cache directories
            for cache_dir in self.cache_dirs.values():
                cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing cache index
            await self._load_cache_index()
            
            # Validate cache integrity
            await self._validate_cache_integrity()
            
            # Schedule cleanup task
            asyncio.create_task(self._periodic_cleanup())
            
            self.logger.info(f"Cache manager initialized: {len(self.cache_index)} entries")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cache: {str(e)}")
    
    async def get(self, cache_key: str, validate_dependencies: bool = True) -> Optional[Any]:
        """
        Get cached data with dependency validation.
        
        Args:
            cache_key: Unique identifier for cached data
            validate_dependencies: Whether to check dependency validity
            
        Returns:
            Cached data if valid, None otherwise
        """
        start_time = datetime.utcnow()
        
        try:
            # Check if entry exists
            if cache_key not in self.cache_index:
                self.stats["misses"] += 1
                self.logger.debug(f"Cache miss: {cache_key}")
                return None
            
            metadata = self.cache_index[cache_key]
            
            # Validate cache entry
            cache_status = await self._validate_cache_entry(metadata, validate_dependencies)
            
            if cache_status != CacheStatus.VALID:
                self.logger.warning(f"Invalid cache entry {cache_key}: {cache_status}")
                await self._invalidate_entry(cache_key)
                self.stats["misses"] += 1
                return None
            
            # Load cached data
            data = await self._load_cache_data(metadata)
            
            if data is None:
                self.stats["misses"] += 1
                return None
            
            # Update access statistics
            await self._update_access_stats(metadata)
            
            self.stats["hits"] += 1
            access_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self.logger.info(f"Cache hit: {cache_key} ({access_time:.2f}ms)")
            return data
            
        except Exception as e:
            self.logger.error(f"Cache get error for {cache_key}: {str(e)}")
            self.stats["misses"] += 1
            return None
    
    async def set(self, cache_key: str, data: Any, metadata_override: Dict[str, Any] = None,
                  dependencies: List[str] = None, expiry_hours: Optional[int] = None) -> bool:
        """
        Store data in cache with metadata and dependency tracking.
        
        Args:
            cache_key: Unique identifier for cached data
            data: Data to cache
            metadata_override: Override default metadata values
            dependencies: List of cache keys this entry depends on
            expiry_hours: Custom expiry time in hours
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            # Generate metadata
            metadata = await self._generate_metadata(
                cache_key, data, metadata_override, dependencies, expiry_hours
            )
            
            # Store data
            success = await self._store_cache_data(metadata, data)
            
            if success:
                # Update cache index
                self.cache_index[cache_key] = metadata
                
                # Update dependency graph
                if dependencies:
                    self.dependency_graph[cache_key] = set(dependencies)
                
                # Save cache index
                await self._save_cache_index()
                
                self.logger.info(f"Cached: {cache_key} ({metadata.size_bytes} bytes)")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Cache set error for {cache_key}: {str(e)}")
            return False
    
    async def invalidate(self, cache_key: str, cascade: bool = True) -> List[str]:
        """
        Invalidate cache entry and optionally cascade to dependents.
        
        Args:
            cache_key: Key to invalidate
            cascade: Whether to invalidate dependent entries
            
        Returns:
            List of invalidated cache keys
        """
        invalidated_keys = []
        
        try:
            # Find all entries that depend on this key
            if cascade:
                dependent_keys = await self._find_dependent_keys(cache_key)
                for dep_key in dependent_keys:
                    await self._invalidate_entry(dep_key)
                    invalidated_keys.append(dep_key)
            
            # Invalidate the main entry
            await self._invalidate_entry(cache_key)
            invalidated_keys.append(cache_key)
            
            self.stats["invalidations"] += len(invalidated_keys)
            self.logger.info(f"Invalidated {len(invalidated_keys)} cache entries")
            
            return invalidated_keys
            
        except Exception as e:
            self.logger.error(f"Cache invalidation error: {str(e)}")
            return []
    
    async def get_phase_files(self, phase_id: str) -> Dict[str, str]:
        """Get all generated files for a specific micro-phase."""
        cache_key = f"phase-{phase_id}-generated_code"
        files_data = await self.get(cache_key)
        
        if files_data and isinstance(files_data, dict):
            return files_data
        
        return {}
    
    async def cache_phase_files(self, phase_id: str, files: Dict[str, str], 
                               session_id: str, dependencies: List[str] = None) -> bool:
        """Cache generated files for a micro-phase."""
        cache_key = f"phase-{phase_id}-generated_code"
        
        metadata_override = {
            "session_id": session_id,
            "agent_type": "claude",
            "file_count": len(files),
            "tags": ["generated_code", "micro_phase", phase_id]
        }
        
        return await self.set(cache_key, files, metadata_override, dependencies)
    
    async def cache_brainstorming(self, features: str, session_id: str) -> bool:
        """Cache brainstorming results."""
        return await self.set(
            "brainstorming_features",
            features,
            {"session_id": session_id, "agent_type": "gpt_manager"},
            expiry_hours=168  # 1 week
        )
    
    async def cache_architecture(self, architecture: str, session_id: str, 
                                dependencies: List[str] = None) -> bool:
        """Cache architecture plan."""
        return await self.set(
            "system_architecture_plan",
            architecture,
            {"session_id": session_id, "agent_type": "claude"},
            dependencies or ["brainstorming_features"]
        )
    
    async def cache_micro_phases(self, phases: List[MicroPhase], session_id: str,
                                dependencies: List[str] = None) -> bool:
        """Cache micro-phase breakdown."""
        phases_data = [asdict(phase) for phase in phases]
        return await self.set(
            "project_micro_phases",
            phases_data,
            {"session_id": session_id, "agent_type": "claude"},
            dependencies or ["system_architecture_plan"]
        )
    
    async def cache_validation_report(self, phase_id: str, report: Dict[str, Any],
                                     session_id: str) -> bool:
        """Cache validation results for a micro-phase."""
        cache_key = f"phase-{phase_id}-validation_report"
        
        metadata_override = {
            "session_id": session_id,
            "agent_type": "gpt_validator",
            "validation_status": "passed" if report.get("success") else "failed",
            "tags": ["validation", "micro_phase", phase_id]
        }
        
        return await self.set(cache_key, report, metadata_override, [f"phase-{phase_id}-generated_code"])
    
    async def cache_integration_summary(self, summary: Dict[str, Any], session_id: str,
                                       phase_dependencies: List[str] = None) -> bool:
        """Cache final integration summary."""
        return await self.set(
            "final_integration_summary",
            summary,
            {"session_id": session_id, "agent_type": "gpt_integration_agent"},
            phase_dependencies
        )
    
    async def cache_phase_documentation(self, session_id: str, phase_name: str, 
                                       documentation: Dict[str, Any]) -> bool:
        """Cache phase documentation."""
        cache_key = f"phase_documentation_{phase_name.lower().replace(' ', '_')}"
        
        metadata_override = {
            "session_id": session_id,
            "agent_type": "phase_documenter",
            "tags": ["documentation", "phase", phase_name.lower()]
        }
        
        return await self.set(cache_key, documentation, metadata_override)
    
    async def cache_architecture_plan_file(self, session_id: str, plan_file: Dict[str, Any]) -> bool:
        """Cache architecture plan file."""
        return await self.set(
            "architecture_plan_file",
            plan_file,
            {
                "session_id": session_id,
                "agent_type": "phase_documenter",
                "tags": ["architecture", "plan_file", "guidance"]
            },
            ["system_architecture_plan"]
        )
    
    async def get_cache_analytics(self) -> CacheStats:
        """Get comprehensive cache performance analytics."""
        total_hits = self.stats["hits"]
        total_misses = self.stats["misses"]
        total_requests = total_hits + total_misses
        
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0
        miss_rate = 100.0 - hit_rate
        
        total_size = sum(metadata.size_bytes for metadata in self.cache_index.values())
        total_size_mb = total_size / (1024 * 1024)
        
        # Estimate cost savings (assuming $0.002 per 1K tokens for GPT-4)
        estimated_tokens_saved = self.stats["api_calls_saved"] * 2000  # Average 2K tokens per call
        cost_savings = (estimated_tokens_saved / 1000) * 0.002
        
        return CacheStats(
            total_entries=len(self.cache_index),
            hit_rate=hit_rate,
            miss_rate=miss_rate,
            total_size_mb=total_size_mb,
            avg_access_time_ms=5.0,  # Placeholder
            cost_savings_usd=cost_savings,
            api_calls_saved=self.stats["api_calls_saved"]
        )
    
    async def cleanup_expired_entries(self) -> Dict[str, Any]:
        """Clean up expired and stale cache entries."""
        cleanup_stats = {
            "expired_entries": 0,
            "corrupted_entries": 0,
            "bytes_freed": 0,
            "entries_kept": 0
        }
        
        current_time = datetime.utcnow()
        entries_to_remove = []
        
        for cache_key, metadata in self.cache_index.items():
            # Check expiry
            if metadata.expiry_time:
                expiry_time = datetime.fromisoformat(metadata.expiry_time.replace("Z", "+00:00"))
                if current_time > expiry_time:
                    entries_to_remove.append(cache_key)
                    cleanup_stats["expired_entries"] += 1
                    cleanup_stats["bytes_freed"] += metadata.size_bytes
                    continue
            
            # Check corruption
            if await self._is_entry_corrupted(metadata):
                entries_to_remove.append(cache_key)
                cleanup_stats["corrupted_entries"] += 1
                cleanup_stats["bytes_freed"] += metadata.size_bytes
                continue
            
            cleanup_stats["entries_kept"] += 1
        
        # Remove expired/corrupted entries
        for cache_key in entries_to_remove:
            await self._invalidate_entry(cache_key)
        
        # Save updated index
        await self._save_cache_index()
        
        self.logger.info(f"Cleanup completed: {len(entries_to_remove)} entries removed")
        return cleanup_stats
    
    async def _generate_metadata(self, cache_key: str, data: Any, 
                                metadata_override: Dict[str, Any] = None,
                                dependencies: List[str] = None,
                                expiry_hours: Optional[int] = None) -> CacheMetadata:
        """Generate metadata for cache entry."""
        current_time = datetime.utcnow().isoformat() + "Z"
        
        # Calculate prompt hash for versioning
        prompt_hash = hashlib.md5(str(data).encode()).hexdigest()
        
        # Calculate data size
        data_str = json.dumps(data) if not isinstance(data, str) else data
        size_bytes = len(data_str.encode('utf-8'))
        
        # Calculate expiry time
        expiry_time = None
        if expiry_hours:
            expiry_time = (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat() + "Z"
        elif self.config["default_expiry_hours"]:
            expiry_time = (datetime.utcnow() + timedelta(hours=self.config["default_expiry_hours"])).isoformat() + "Z"
        
        metadata = CacheMetadata(
            cache_key=cache_key,
            created_at=current_time,
            updated_at=current_time,
            agent_type=metadata_override.get("agent_type", "unknown") if metadata_override else "unknown",
            agent_version="v1.0",  # Could be dynamic
            prompt_hash=prompt_hash,
            dependencies=dependencies or [],
            session_id=metadata_override.get("session_id", "unknown") if metadata_override else "unknown",
            validation_status=metadata_override.get("validation_status", "unknown") if metadata_override else "unknown",
            expiry_time=expiry_time,
            file_count=metadata_override.get("file_count", 0) if metadata_override else 0,
            size_bytes=size_bytes,
            access_count=0,
            last_accessed=None,
            tags=metadata_override.get("tags", []) if metadata_override else []
        )
        
        return metadata
    
    async def _validate_cache_entry(self, metadata: CacheMetadata, 
                                   validate_dependencies: bool = True) -> CacheStatus:
        """Validate cache entry status."""
        # Check expiry
        if metadata.expiry_time:
            expiry_time = datetime.fromisoformat(metadata.expiry_time.replace("Z", "+00:00"))
            if datetime.utcnow() > expiry_time:
                return CacheStatus.EXPIRED
        
        # Check file existence
        cache_file = self._get_cache_file_path(metadata.cache_key)
        if not cache_file.exists():
            return CacheStatus.CORRUPTED
        
        # Check dependencies if requested
        if validate_dependencies and metadata.dependencies:
            for dep_key in metadata.dependencies:
                if dep_key not in self.cache_index:
                    return CacheStatus.MISSING_DEPENDENCIES
                
                dep_status = await self._validate_cache_entry(
                    self.cache_index[dep_key], validate_dependencies=False
                )
                if dep_status != CacheStatus.VALID:
                    return CacheStatus.MISSING_DEPENDENCIES
        
        return CacheStatus.VALID
    
    async def _load_cache_data(self, metadata: CacheMetadata) -> Optional[Any]:
        """Load cached data from disk."""
        cache_file = self._get_cache_file_path(metadata.cache_key)
        
        try:
            async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            self.logger.error(f"Failed to load cache data for {metadata.cache_key}: {str(e)}")
            return None
    
    async def _store_cache_data(self, metadata: CacheMetadata, data: Any) -> bool:
        """Store data to cache file."""
        cache_file = self._get_cache_file_path(metadata.cache_key)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Convert data to JSON string
            if isinstance(data, str):
                json_data = json.dumps({"content": data})
            else:
                json_data = json.dumps(data, indent=2)
            
            async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
                await f.write(json_data)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to store cache data for {metadata.cache_key}: {str(e)}")
            return False
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        # Determine cache directory based on key pattern
        if cache_key == "brainstorming_features":
            return self.cache_dirs["brainstorming"] / "features.json"
        elif cache_key == "system_architecture_plan":
            return self.cache_dirs["architecture"] / "plan.json"
        elif cache_key == "project_micro_phases":
            return self.cache_dirs["metadata"] / "micro_phases.json"
        elif cache_key.startswith("phase-") and "generated_code" in cache_key:
            phase_id = cache_key.split("-")[1]
            return self.cache_dirs["phases"] / f"phase_{phase_id}" / "generated_code.json"
        elif cache_key.startswith("phase-") and "validation_report" in cache_key:
            phase_id = cache_key.split("-")[1]
            return self.cache_dirs["phases"] / f"phase_{phase_id}" / "validation_report.json"
        elif cache_key == "final_integration_summary":
            return self.cache_dirs["integration"] / "summary.json"
        else:
            # Default location
            safe_key = cache_key.replace("/", "_").replace(":", "_")
            return self.cache_dirs["files"] / f"{safe_key}.json"
    
    async def _update_access_stats(self, metadata: CacheMetadata):
        """Update access statistics for cache entry."""
        metadata.access_count += 1
        metadata.last_accessed = datetime.utcnow().isoformat() + "Z"
        
        # Increment API calls saved (estimate)
        self.stats["api_calls_saved"] += 1
    
    async def _invalidate_entry(self, cache_key: str):
        """Remove cache entry and its files."""
        if cache_key in self.cache_index:
            metadata = self.cache_index[cache_key]
            cache_file = self._get_cache_file_path(cache_key)
            
            # Remove file if exists
            if cache_file.exists():
                cache_file.unlink()
            
            # Remove directory if empty
            if cache_file.parent.exists() and not any(cache_file.parent.iterdir()):
                cache_file.parent.rmdir()
            
            # Remove from index
            del self.cache_index[cache_key]
            
            # Remove from dependency graph
            if cache_key in self.dependency_graph:
                del self.dependency_graph[cache_key]
    
    async def _find_dependent_keys(self, cache_key: str) -> List[str]:
        """Find all cache keys that depend on the given key."""
        dependent_keys = []
        
        for key, deps in self.dependency_graph.items():
            if cache_key in deps:
                dependent_keys.append(key)
        
        return dependent_keys
    
    async def _load_cache_index(self):
        """Load cache index from disk."""
        index_file = self.cache_dirs["metadata"] / "cache_index.json"
        
        if index_file.exists():
            try:
                async with aiofiles.open(index_file, 'r') as f:
                    content = await f.read()
                    index_data = json.loads(content)
                    
                    for key, metadata_dict in index_data.items():
                        self.cache_index[key] = CacheMetadata(**metadata_dict)
                
                self.logger.info(f"Loaded cache index: {len(self.cache_index)} entries")
            except Exception as e:
                self.logger.error(f"Failed to load cache index: {str(e)}")
    
    async def _save_cache_index(self):
        """Save cache index to disk."""
        index_file = self.cache_dirs["metadata"] / "cache_index.json"
        
        try:
            index_data = {key: asdict(metadata) for key, metadata in self.cache_index.items()}
            
            async with aiofiles.open(index_file, 'w') as f:
                await f.write(json.dumps(index_data, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save cache index: {str(e)}")
    
    async def _validate_cache_integrity(self):
        """Validate integrity of cached entries."""
        corrupted_keys = []
        
        for cache_key, metadata in self.cache_index.items():
            if await self._is_entry_corrupted(metadata):
                corrupted_keys.append(cache_key)
        
        # Remove corrupted entries
        for key in corrupted_keys:
            await self._invalidate_entry(key)
        
        if corrupted_keys:
            self.logger.warning(f"Removed {len(corrupted_keys)} corrupted cache entries")
    
    async def _is_entry_corrupted(self, metadata: CacheMetadata) -> bool:
        """Check if cache entry is corrupted."""
        cache_file = self._get_cache_file_path(metadata.cache_key)
        
        if not cache_file.exists():
            return True
        
        try:
            # Try to load and parse the file
            async with aiofiles.open(cache_file, 'r') as f:
                content = await f.read()
                json.loads(content)
            return False
        except:
            return True
    
    async def _periodic_cleanup(self):
        """Run periodic cleanup of cache."""
        while True:
            try:
                await asyncio.sleep(self.config["cleanup_interval_hours"] * 3600)
                await self.cleanup_expired_entries()
            except Exception as e:
                self.logger.error(f"Periodic cleanup error: {str(e)}")
    
    async def cleanup(self):
        """Cleanup cache manager resources."""
        try:
            await self._save_cache_index()
            self.logger.info("Cache manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Cache cleanup error: {str(e)}")