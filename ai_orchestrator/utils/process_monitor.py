"""
Real-time process monitoring and AI agent communication tracking.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from threading import Lock
import weakref

from .logging_config import get_logger


class MessageType(Enum):
    """Types of messages in the monitoring system."""
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STATUS_UPDATE = "status_update"
    WORKFLOW_EVENT = "workflow_event"


@dataclass
class ProcessMessage:
    """A single message in the process monitoring system."""
    id: str
    session_id: str
    timestamp: float
    message_type: MessageType
    source: str  # agent name or system component
    content: Any
    metadata: Dict[str, Any]
    level: str = "info"  # debug, info, warning, error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "message_type": self.message_type.value,
            "source": self.source,
            "content": self.content,
            "metadata": self.metadata,
            "level": self.level
        }


class ProcessMonitor:
    """Real-time process monitoring system for AI agent communications."""
    
    def __init__(self):
        self.logger = get_logger("process_monitor")
        self._messages: Dict[str, List[ProcessMessage]] = {}  # session_id -> messages
        self._subscribers: Dict[str, Set[weakref.ref]] = {}  # session_id -> websocket refs
        self._lock = Lock()
        self._message_counter = 0
        self._max_messages_per_session = 1000
        
    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        self._message_counter += 1
        return f"msg_{int(time.time() * 1000)}_{self._message_counter}"
    
    def subscribe(self, session_id: str, callback):
        """Subscribe to messages for a specific session."""
        with self._lock:
            if session_id not in self._subscribers:
                self._subscribers[session_id] = set()
            self._subscribers[session_id].add(weakref.ref(callback))
    
    def unsubscribe(self, session_id: str, callback):
        """Unsubscribe from messages for a specific session."""
        with self._lock:
            if session_id in self._subscribers:
                callback_ref = weakref.ref(callback)
                self._subscribers[session_id].discard(callback_ref)
                if not self._subscribers[session_id]:
                    del self._subscribers[session_id]
    
    def add_message(
        self,
        session_id: str,
        message_type: MessageType,
        source: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ) -> str:
        """Add a message to the monitoring system."""
        message = ProcessMessage(
            id=self._generate_message_id(),
            session_id=session_id,
            timestamp=time.time(),
            message_type=message_type,
            source=source,
            content=content,
            metadata=metadata or {},
            level=level
        )
        
        with self._lock:
            if session_id not in self._messages:
                self._messages[session_id] = []
            
            # Add message
            self._messages[session_id].append(message)
            
            # Limit messages per session
            if len(self._messages[session_id]) > self._max_messages_per_session:
                self._messages[session_id] = self._messages[session_id][-self._max_messages_per_session:]
            
            # Notify subscribers
            self._notify_subscribers(session_id, message)
        
        return message.id
    
    def _notify_subscribers(self, session_id: str, message: ProcessMessage):
        """Notify all subscribers of a new message."""
        if session_id not in self._subscribers:
            return
        
        # Clean up dead references and notify live ones
        live_refs = set()
        for callback_ref in self._subscribers[session_id]:
            callback = callback_ref()
            if callback is not None:
                live_refs.add(callback_ref)
                try:
                    # Use asyncio.create_task if callback is a coroutine
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(message.to_dict()))
                    else:
                        callback(message.to_dict())
                except Exception as e:
                    self.logger.error(f"Error notifying subscriber: {e}")
        
        self._subscribers[session_id] = live_refs
    
    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        message_type: Optional[MessageType] = None,
        source: Optional[str] = None,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages for a session with optional filtering."""
        with self._lock:
            if session_id not in self._messages:
                return []
            
            messages = self._messages[session_id]
            
            # Apply filters
            if message_type:
                messages = [m for m in messages if m.message_type == message_type]
            if source:
                messages = [m for m in messages if m.source == source]
            if level:
                messages = [m for m in messages if m.level == level]
            
            # Apply limit
            if limit:
                messages = messages[-limit:]
            
            return [m.to_dict() for m in messages]
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        with self._lock:
            if session_id not in self._messages:
                return {
                    "total_messages": 0,
                    "by_type": {},
                    "by_source": {},
                    "by_level": {},
                    "start_time": None,
                    "duration": 0
                }
            
            messages = self._messages[session_id]
            
            # Count by type
            by_type = {}
            for msg in messages:
                msg_type = msg.message_type.value
                by_type[msg_type] = by_type.get(msg_type, 0) + 1
            
            # Count by source
            by_source = {}
            for msg in messages:
                by_source[msg.source] = by_source.get(msg.source, 0) + 1
            
            # Count by level
            by_level = {}
            for msg in messages:
                by_level[msg.level] = by_level.get(msg.level, 0) + 1
            
            # Calculate duration
            start_time = messages[0].timestamp if messages else None
            end_time = messages[-1].timestamp if messages else None
            duration = (end_time - start_time) if (start_time and end_time) else 0
            
            return {
                "total_messages": len(messages),
                "by_type": by_type,
                "by_source": by_source,
                "by_level": by_level,
                "start_time": start_time,
                "duration": duration
            }
    
    def clear_session(self, session_id: str):
        """Clear all messages for a session."""
        with self._lock:
            if session_id in self._messages:
                del self._messages[session_id]
            if session_id in self._subscribers:
                del self._subscribers[session_id]
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active sessions being monitored."""
        with self._lock:
            return list(self._messages.keys())
    
    # Convenience methods for common message types
    def log_agent_request(self, session_id: str, agent_name: str, prompt: str, metadata: Optional[Dict] = None):
        """Log an agent API request."""
        return self.add_message(
            session_id=session_id,
            message_type=MessageType.AGENT_REQUEST,
            source=agent_name,
            content={"prompt": prompt},
            metadata=metadata or {},
            level="debug"
        )
    
    def log_agent_response(self, session_id: str, agent_name: str, response: str, metadata: Optional[Dict] = None):
        """Log an agent API response."""
        return self.add_message(
            session_id=session_id,
            message_type=MessageType.AGENT_RESPONSE,
            source=agent_name,
            content={"response": response},
            metadata=metadata or {},
            level="debug"
        )
    
    def log_phase_start(self, session_id: str, phase_name: str, metadata: Optional[Dict] = None):
        """Log the start of a workflow phase."""
        return self.add_message(
            session_id=session_id,
            message_type=MessageType.PHASE_START,
            source="workflow_engine",
            content={"phase": phase_name},
            metadata=metadata or {},
            level="info"
        )
    
    def log_phase_end(self, session_id: str, phase_name: str, success: bool, metadata: Optional[Dict] = None):
        """Log the end of a workflow phase."""
        return self.add_message(
            session_id=session_id,
            message_type=MessageType.PHASE_END,
            source="workflow_engine",
            content={"phase": phase_name, "success": success},
            metadata=metadata or {},
            level="info" if success else "warning"
        )
    
    def log_error(self, session_id: str, source: str, error: str, metadata: Optional[Dict] = None):
        """Log an error."""
        return self.add_message(
            session_id=session_id,
            message_type=MessageType.ERROR,
            source=source,
            content={"error": error},
            metadata=metadata or {},
            level="error"
        )
    
    def log_workflow_event(self, session_id: str, event: str, details: Any, metadata: Optional[Dict] = None):
        """Log a general workflow event."""
        return self.add_message(
            session_id=session_id,
            message_type=MessageType.WORKFLOW_EVENT,
            source="workflow_engine",
            content={"event": event, "details": details},
            metadata=metadata or {},
            level="info"
        )


# Global process monitor instance
_process_monitor: Optional[ProcessMonitor] = None


def get_process_monitor() -> ProcessMonitor:
    """Get the global process monitor instance."""
    global _process_monitor
    if _process_monitor is None:
        _process_monitor = ProcessMonitor()
    return _process_monitor


# Decorator for monitoring agent calls
def monitor_agent_call(agent_name: str):
    """Decorator to automatically monitor agent API calls."""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            session_id = getattr(self, 'current_session_id', None)
            if not session_id:
                return await func(self, *args, **kwargs)
            
            monitor = get_process_monitor()
            
            # Log request
            prompt = args[0] if args else kwargs.get('prompt', 'Unknown')
            monitor.log_agent_request(
                session_id=session_id,
                agent_name=agent_name,
                prompt=str(prompt)[:500],  # Truncate long prompts
                metadata={"function": func.__name__}
            )
            
            try:
                # Execute the function
                result = await func(self, *args, **kwargs)
                
                # Log response
                monitor.log_agent_response(
                    session_id=session_id,
                    agent_name=agent_name,
                    response=str(result)[:500],  # Truncate long responses
                    metadata={"function": func.__name__, "success": True}
                )
                
                return result
                
            except Exception as e:
                # Log error
                monitor.log_error(
                    session_id=session_id,
                    source=agent_name,
                    error=str(e),
                    metadata={"function": func.__name__}
                )
                raise
        
        return wrapper
    return decorator