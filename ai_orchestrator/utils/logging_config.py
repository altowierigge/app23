"""
Comprehensive logging and monitoring configuration for the AI orchestration system.
"""

import logging
import logging.handlers
import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import os

from ..core.config import get_config, LogLevel


@dataclass
class MetricData:
    """Data structure for tracking metrics."""
    name: str
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = "count"


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        if hasattr(record, 'agent_role'):
            log_data['agent_role'] = record.agent_role
        if hasattr(record, 'task_type'):
            log_data['task_type'] = record.task_type
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class MetricsCollector:
    """Collects and aggregates metrics from the AI orchestration system."""
    
    def __init__(self):
        self.metrics: List[MetricData] = []
        self.aggregated_metrics: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()
        self.logger = logging.getLogger("metrics")
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None, unit: str = "count"):
        """Record a metric value."""
        metric = MetricData(
            name=name,
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            unit=unit
        )
        self.metrics.append(metric)
        self.logger.debug(f"Metric recorded: {name}={value} {unit}")
    
    def record_execution_time(self, operation: str, duration: float, labels: Optional[Dict[str, str]] = None):
        """Record execution time for an operation."""
        self.record_metric(
            name=f"{operation}_execution_time",
            value=duration,
            labels=labels,
            unit="seconds"
        )
    
    def record_api_call(self, agent: str, model: str, tokens_used: int, success: bool):
        """Record API call metrics."""
        labels = {"agent": agent, "model": model, "success": str(success)}
        
        self.record_metric("api_calls_total", 1, labels)
        self.record_metric("tokens_used_total", tokens_used, labels)
        
        if not success:
            self.record_metric("api_errors_total", 1, labels)
    
    def record_workflow_phase(self, phase_name: str, duration: float, success: bool):
        """Record workflow phase metrics."""
        labels = {"phase": phase_name, "success": str(success)}
        
        self.record_metric("workflow_phase_duration", duration, labels, "seconds")
        self.record_metric("workflow_phase_total", 1, labels)
        
        if not success:
            self.record_metric("workflow_phase_errors", 1, labels)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        total_runtime = time.time() - self.start_time
        
        # Aggregate metrics by name
        aggregated = {}
        for metric in self.metrics:
            if metric.name not in aggregated:
                aggregated[metric.name] = {
                    "count": 0,
                    "total": 0.0,
                    "min": float('inf'),
                    "max": float('-inf'),
                    "unit": metric.unit
                }
            
            agg = aggregated[metric.name]
            agg["count"] += 1
            agg["total"] += metric.value
            agg["min"] = min(agg["min"], metric.value)
            agg["max"] = max(agg["max"], metric.value)
            agg["average"] = agg["total"] / agg["count"]
        
        return {
            "total_runtime": total_runtime,
            "total_metrics": len(self.metrics),
            "aggregated_metrics": aggregated,
            "timestamp": datetime.now().isoformat()
        }


class PerformanceMonitor:
    """Monitor performance and health of the AI orchestration system."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.logger = logging.getLogger("performance_monitor")
        self.alerts: List[Dict[str, Any]] = []
        
        # Performance thresholds
        self.thresholds = {
            "api_response_time": 30.0,  # seconds
            "phase_execution_time": 600.0,  # 10 minutes
            "error_rate": 0.1,  # 10%
            "memory_usage": 0.8  # 80%
        }
    
    def check_api_performance(self, agent: str, response_time: float):
        """Check API performance and generate alerts if needed."""
        if response_time > self.thresholds["api_response_time"]:
            self._generate_alert(
                severity="warning",
                message=f"Slow API response from {agent}: {response_time:.2f}s",
                data={"agent": agent, "response_time": response_time}
            )
    
    def check_phase_performance(self, phase_name: str, execution_time: float):
        """Check workflow phase performance."""
        if execution_time > self.thresholds["phase_execution_time"]:
            self._generate_alert(
                severity="warning",
                message=f"Slow phase execution: {phase_name} took {execution_time:.2f}s",
                data={"phase": phase_name, "execution_time": execution_time}
            )
    
    def check_error_rate(self, agent: str, total_calls: int, errors: int):
        """Check error rate for an agent."""
        if total_calls > 0:
            error_rate = errors / total_calls
            if error_rate > self.thresholds["error_rate"]:
                self._generate_alert(
                    severity="critical",
                    message=f"High error rate for {agent}: {error_rate:.2%}",
                    data={"agent": agent, "error_rate": error_rate, "total_calls": total_calls, "errors": errors}
                )
    
    def _generate_alert(self, severity: str, message: str, data: Dict[str, Any]):
        """Generate a performance alert."""
        alert = {
            "timestamp": time.time(),
            "severity": severity,
            "message": message,
            "data": data
        }
        self.alerts.append(alert)
        
        # Log alert
        if severity == "critical":
            self.logger.critical(message, extra=data)
        elif severity == "warning":
            self.logger.warning(message, extra=data)
        else:
            self.logger.info(message, extra=data)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        recent_alerts = [a for a in self.alerts if time.time() - a["timestamp"] < 300]  # Last 5 minutes
        
        critical_alerts = [a for a in recent_alerts if a["severity"] == "critical"]
        warning_alerts = [a for a in recent_alerts if a["severity"] == "warning"]
        
        if critical_alerts:
            status = "critical"
        elif warning_alerts:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "recent_alerts": len(recent_alerts),
            "critical_alerts": len(critical_alerts),
            "warning_alerts": len(warning_alerts),
            "last_alert": self.alerts[-1] if self.alerts else None
        }


class WorkflowLogger:
    """Specialized logger for workflow events with context awareness."""
    
    def __init__(self, session_id: str, metrics_collector: MetricsCollector):
        self.session_id = session_id
        self.metrics = metrics_collector
        self.logger = logging.getLogger(f"workflow.{session_id[:8]}")
        self.phase_start_times: Dict[str, float] = {}
        self.workflow_start_time = time.time()
    
    def log_workflow_start(self, user_request: str):
        """Log workflow start."""
        self.logger.info(
            "Workflow started",
            extra={
                "session_id": self.session_id,
                "user_request_length": len(user_request)
            }
        )
        self.metrics.record_metric("workflow_started", 1, {"session_id": self.session_id})
    
    def log_phase_start(self, phase_name: str, agent_role: str):
        """Log phase start."""
        self.phase_start_times[phase_name] = time.time()
        self.logger.info(
            f"Phase started: {phase_name}",
            extra={
                "session_id": self.session_id,
                "phase": phase_name,
                "agent_role": agent_role
            }
        )
    
    def log_phase_complete(self, phase_name: str, agent_role: str, success: bool = True):
        """Log phase completion."""
        start_time = self.phase_start_times.get(phase_name, time.time())
        duration = time.time() - start_time
        
        self.logger.info(
            f"Phase completed: {phase_name}",
            extra={
                "session_id": self.session_id,
                "phase": phase_name,
                "agent_role": agent_role,
                "execution_time": duration,
                "success": success
            }
        )
        
        self.metrics.record_workflow_phase(phase_name, duration, success)
    
    def log_agent_interaction(self, agent_role: str, task_type: str, response_time: float, success: bool):
        """Log agent interaction."""
        self.logger.info(
            f"Agent interaction: {agent_role} - {task_type}",
            extra={
                "session_id": self.session_id,
                "agent_role": agent_role,
                "task_type": task_type,
                "execution_time": response_time,
                "success": success
            }
        )
        
        self.metrics.record_execution_time(
            f"agent_{agent_role}_{task_type}",
            response_time,
            {"agent": agent_role, "task": task_type}
        )
    
    def log_workflow_complete(self, success: bool = True):
        """Log workflow completion."""
        total_duration = time.time() - self.workflow_start_time
        
        self.logger.info(
            "Workflow completed",
            extra={
                "session_id": self.session_id,
                "execution_time": total_duration,
                "success": success
            }
        )
        
        self.metrics.record_metric(
            "workflow_completed",
            1,
            {"session_id": self.session_id, "success": str(success)}
        )
        self.metrics.record_execution_time("workflow_total", total_duration)


# Global instances
_metrics_collector = None
_performance_monitor = None


def setup_logging() -> None:
    """Setup logging configuration for the entire application."""
    config = get_config()
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level.value))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    if config.debug:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        console_formatter = StructuredFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "ai_orchestrator.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    
    # Metrics file handler
    metrics_handler = logging.handlers.RotatingFileHandler(
        log_dir / "metrics.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    metrics_formatter = StructuredFormatter()
    metrics_handler.setFormatter(metrics_formatter)
    
    # Add metrics handler to metrics logger
    metrics_logger = logging.getLogger("metrics")
    metrics_logger.addHandler(metrics_handler)
    metrics_logger.setLevel(logging.INFO)
    
    logging.info("Logging system initialized")


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(get_metrics_collector())
    return _performance_monitor


def get_workflow_logger(session_id: str) -> WorkflowLogger:
    """Get a workflow logger for a specific session."""
    return WorkflowLogger(session_id, get_metrics_collector())


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


# Context manager for timed operations
class TimedOperation:
    """Context manager for timing operations and recording metrics."""
    
    def __init__(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        self.operation_name = operation_name
        self.labels = labels or {}
        self.start_time = None
        self.metrics = get_metrics_collector()
        self.logger = get_logger("timed_operation")
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None
        
        self.metrics.record_execution_time(
            self.operation_name,
            duration,
            {**self.labels, "success": str(success)}
        )
        
        if success:
            self.logger.debug(f"Operation completed: {self.operation_name} ({duration:.3f}s)")
        else:
            self.logger.error(f"Operation failed: {self.operation_name} ({duration:.3f}s) - {exc_type.__name__}: {exc_val}")
        
        return False  # Don't suppress exceptions