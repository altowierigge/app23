"""
Cost Optimization Engine for AI Orchestrator Caching.
Provides intelligent cost analysis, optimization strategies, and savings tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

from .cache_manager import CacheManager, CacheMetadata


class OptimizationStrategy(str, Enum):
    """Cost optimization strategies."""
    AGGRESSIVE_CACHING = "aggressive_caching"
    SELECTIVE_CACHING = "selective_caching" 
    SMART_INVALIDATION = "smart_invalidation"
    PREDICTIVE_CACHING = "predictive_caching"


@dataclass
class CostAnalysis:
    """Cost analysis for API usage."""
    total_api_calls: int
    cached_calls: int
    api_calls_saved: int
    estimated_cost_usd: float
    estimated_savings_usd: float
    savings_percentage: float
    most_cached_operations: List[str]
    cost_by_agent_type: Dict[str, float]


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation."""
    strategy: OptimizationStrategy
    description: str
    potential_savings_usd: float
    implementation_effort: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"
    confidence: float  # 0.0 to 1.0


class CostOptimizer:
    """
    Advanced cost optimization engine for AI API usage.
    
    Analyzes caching patterns, predicts costs, and provides
    intelligent recommendations for reducing API expenses.
    """
    
    def __init__(self, cache_manager: CacheManager):
        """Initialize cost optimizer."""
        self.cache_manager = cache_manager
        self.logger = logging.getLogger("cost_optimizer")
        
        # Cost models (USD per 1K tokens)
        self.cost_models = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
        }
        
        # Average token estimates by operation type
        self.token_estimates = {
            "brainstorming": {"input": 1500, "output": 2000},
            "architecture": {"input": 2500, "output": 3500},
            "micro_phase_planning": {"input": 2000, "output": 2500},
            "code_generation": {"input": 1800, "output": 4000},
            "validation": {"input": 2200, "output": 1500},
            "integration": {"input": 3000, "output": 2000}
        }
        
        # Optimization thresholds
        self.optimization_config = {
            "high_cost_threshold_usd": 10.0,
            "cache_hit_target": 0.8,  # 80% hit rate target
            "max_cache_age_hours": 168,  # 1 week
            "aggressive_caching_savings_threshold": 0.5  # 50% savings
        }
    
    async def analyze_costs(self, time_period_days: int = 30) -> CostAnalysis:
        """
        Perform comprehensive cost analysis for specified time period.
        
        Args:
            time_period_days: Number of days to analyze
            
        Returns:
            Detailed cost analysis with savings information
        """
        self.logger.info(f"Analyzing costs for {time_period_days} days")
        
        # Get cache analytics
        cache_stats = await self.cache_manager.get_cache_analytics()
        
        # Calculate API call estimates
        total_requests = cache_stats.api_calls_saved + self._estimate_actual_api_calls()
        cached_calls = cache_stats.api_calls_saved
        actual_api_calls = total_requests - cached_calls
        
        # Estimate costs by operation type
        cost_by_operation = await self._calculate_costs_by_operation()
        total_estimated_cost = sum(cost_by_operation.values())
        
        # Calculate savings
        estimated_cost_without_cache = await self._estimate_cost_without_cache(total_requests)
        estimated_savings = estimated_cost_without_cache - total_estimated_cost
        savings_percentage = (estimated_savings / estimated_cost_without_cache * 100) if estimated_cost_without_cache > 0 else 0
        
        # Find most cached operations
        most_cached = await self._get_most_cached_operations()
        
        # Cost breakdown by agent type
        cost_by_agent = await self._calculate_cost_by_agent_type()
        
        return CostAnalysis(
            total_api_calls=total_requests,
            cached_calls=cached_calls,
            api_calls_saved=cached_calls,
            estimated_cost_usd=total_estimated_cost,
            estimated_savings_usd=estimated_savings,
            savings_percentage=savings_percentage,
            most_cached_operations=most_cached,
            cost_by_agent_type=cost_by_agent
        )
    
    async def get_optimization_recommendations(self, cost_analysis: CostAnalysis) -> List[OptimizationRecommendation]:
        """
        Generate intelligent optimization recommendations based on cost analysis.
        
        Args:
            cost_analysis: Current cost analysis
            
        Returns:
            List of prioritized optimization recommendations
        """
        recommendations = []
        
        # Analyze cache hit rate
        total_requests = cost_analysis.total_api_calls
        hit_rate = cost_analysis.cached_calls / total_requests if total_requests > 0 else 0
        
        if hit_rate < self.optimization_config["cache_hit_target"]:
            recommendations.append(OptimizationRecommendation(
                strategy=OptimizationStrategy.AGGRESSIVE_CACHING,
                description=f"Increase cache hit rate from {hit_rate:.1%} to {self.optimization_config['cache_hit_target']:.1%}",
                potential_savings_usd=cost_analysis.estimated_cost_usd * 0.3,
                implementation_effort="medium",
                risk_level="low",
                confidence=0.85
            ))
        
        # Check for high-cost operations
        if cost_analysis.estimated_cost_usd > self.optimization_config["high_cost_threshold_usd"]:
            expensive_agents = [agent for agent, cost in cost_analysis.cost_by_agent_type.items() 
                              if cost > cost_analysis.estimated_cost_usd * 0.3]
            
            if expensive_agents:
                recommendations.append(OptimizationRecommendation(
                    strategy=OptimizationStrategy.SELECTIVE_CACHING,
                    description=f"Focus caching on high-cost agents: {', '.join(expensive_agents)}",
                    potential_savings_usd=cost_analysis.estimated_cost_usd * 0.4,
                    implementation_effort="low",
                    risk_level="low",
                    confidence=0.9
                ))
        
        # Smart invalidation recommendation
        stale_cache_savings = await self._estimate_stale_cache_savings()
        if stale_cache_savings > 1.0:  # $1+ potential savings
            recommendations.append(OptimizationRecommendation(
                strategy=OptimizationStrategy.SMART_INVALIDATION,
                description="Implement smarter cache invalidation to reduce unnecessary re-computation",
                potential_savings_usd=stale_cache_savings,
                implementation_effort="medium",
                risk_level="medium",
                confidence=0.7
            ))
        
        # Predictive caching for common patterns
        if len(cost_analysis.most_cached_operations) >= 3:
            recommendations.append(OptimizationRecommendation(
                strategy=OptimizationStrategy.PREDICTIVE_CACHING,
                description="Pre-cache common operation sequences to reduce latency and costs",
                potential_savings_usd=cost_analysis.estimated_cost_usd * 0.15,
                implementation_effort="high",
                risk_level="medium",
                confidence=0.6
            ))
        
        # Sort by potential savings (descending)
        recommendations.sort(key=lambda x: x.potential_savings_usd, reverse=True)
        
        return recommendations
    
    async def estimate_monthly_costs(self, current_usage_days: int = 7) -> Dict[str, float]:
        """
        Estimate monthly costs based on current usage patterns.
        
        Args:
            current_usage_days: Days of current usage to extrapolate from
            
        Returns:
            Monthly cost estimates with and without caching
        """
        # Get current cost analysis
        cost_analysis = await self.analyze_costs(current_usage_days)
        
        # Extrapolate to monthly
        daily_cost = cost_analysis.estimated_cost_usd / current_usage_days
        monthly_cost_with_cache = daily_cost * 30
        
        # Estimate without cache
        daily_cost_without_cache = (cost_analysis.estimated_cost_usd + cost_analysis.estimated_savings_usd) / current_usage_days
        monthly_cost_without_cache = daily_cost_without_cache * 30
        
        return {
            "monthly_with_cache": monthly_cost_with_cache,
            "monthly_without_cache": monthly_cost_without_cache,
            "monthly_savings": monthly_cost_without_cache - monthly_cost_with_cache,
            "yearly_savings": (monthly_cost_without_cache - monthly_cost_with_cache) * 12
        }
    
    async def track_cost_trends(self, days: int = 30) -> Dict[str, List[float]]:
        """
        Track cost trends over time for analysis and forecasting.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Cost trends by day and operation type
        """
        # This would require historical data storage
        # For now, return simulated trend data
        
        trends = {
            "daily_costs": [],
            "cache_hit_rates": [],
            "api_calls_saved": [],
            "cost_by_agent": {
                "gpt_manager": [],
                "gpt_validator": [],
                "gpt_git_agent": [],
                "gpt_integration_agent": [],
                "claude": []
            }
        }
        
        # Simulate trends (in real implementation, this would use historical data)
        base_cost = 2.5
        for day in range(days):
            # Simulate improving cache hit rate over time
            hit_rate = min(0.95, 0.3 + (day / days) * 0.5)
            daily_cost = base_cost * (1 - hit_rate * 0.6)
            
            trends["daily_costs"].append(daily_cost)
            trends["cache_hit_rates"].append(hit_rate)
            trends["api_calls_saved"].append(int(50 * hit_rate))
            
            # Distribute costs among agents
            for agent in trends["cost_by_agent"]:
                agent_cost = daily_cost * (0.15 + hash(agent) % 25 / 100)
                trends["cost_by_agent"][agent].append(agent_cost)
        
        return trends
    
    def _estimate_actual_api_calls(self) -> int:
        """Estimate actual API calls made (not cached)."""
        # This would be tracked in real implementation
        return max(0, 100 - self.cache_manager.stats["api_calls_saved"])
    
    async def _calculate_costs_by_operation(self) -> Dict[str, float]:
        """Calculate estimated costs by operation type."""
        costs = {}
        
        for operation, tokens in self.token_estimates.items():
            # Use GPT-4 as default model for estimates
            cost_per_call = (
                (tokens["input"] / 1000) * self.cost_models["gpt-4"]["input"] +
                (tokens["output"] / 1000) * self.cost_models["gpt-4"]["output"]
            )
            
            # Estimate calls per operation type (simplified)
            estimated_calls = 10  # Would be tracked in real implementation
            costs[operation] = cost_per_call * estimated_calls
        
        return costs
    
    async def _estimate_cost_without_cache(self, total_requests: int) -> float:
        """Estimate cost if no caching was used."""
        # Average cost per request across all operation types
        avg_cost_per_request = 0.15  # $0.15 average per API call
        return total_requests * avg_cost_per_request
    
    async def _get_most_cached_operations(self) -> List[str]:
        """Get most frequently cached operation types."""
        # Analyze cache entries by type/tags
        operation_counts = {}
        
        for metadata in self.cache_manager.cache_index.values():
            for tag in metadata.tags:
                if tag in self.token_estimates:
                    operation_counts[tag] = operation_counts.get(tag, 0) + 1
        
        # Return top 3 most cached operations
        sorted_ops = sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)
        return [op[0] for op in sorted_ops[:3]]
    
    async def _calculate_cost_by_agent_type(self) -> Dict[str, float]:
        """Calculate estimated costs by agent type."""
        costs = {
            "gpt_manager": 2.5,
            "gpt_validator": 1.8,
            "gpt_git_agent": 1.2,
            "gpt_integration_agent": 2.0,
            "claude": 3.5
        }
        
        # In real implementation, this would be calculated from actual usage
        return costs
    
    async def _estimate_stale_cache_savings(self) -> float:
        """Estimate potential savings from better cache invalidation."""
        # Count potentially stale entries
        stale_count = 0
        current_time = datetime.utcnow()
        
        for metadata in self.cache_manager.cache_index.values():
            created_time = datetime.fromisoformat(metadata.created_at.replace("Z", "+00:00"))
            age_hours = (current_time - created_time).total_seconds() / 3600
            
            if age_hours > self.optimization_config["max_cache_age_hours"]:
                stale_count += 1
        
        # Estimate savings from better invalidation
        return stale_count * 0.10  # $0.10 per stale entry avoided
    
    async def generate_cost_report(self, time_period_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive cost optimization report."""
        cost_analysis = await self.analyze_costs(time_period_days)
        recommendations = await self.get_optimization_recommendations(cost_analysis)
        monthly_estimates = await self.estimate_monthly_costs(time_period_days)
        trends = await self.track_cost_trends(time_period_days)
        
        return {
            "report_generated": datetime.utcnow().isoformat(),
            "analysis_period_days": time_period_days,
            "cost_analysis": asdict(cost_analysis),
            "optimization_recommendations": [asdict(rec) for rec in recommendations],
            "monthly_estimates": monthly_estimates,
            "cost_trends": trends,
            "summary": {
                "current_monthly_cost": monthly_estimates["monthly_with_cache"],
                "potential_monthly_savings": sum(rec.potential_savings_usd for rec in recommendations),
                "cache_effectiveness": f"{cost_analysis.savings_percentage:.1f}%",
                "top_recommendation": recommendations[0].description if recommendations else "No recommendations"
            }
        }