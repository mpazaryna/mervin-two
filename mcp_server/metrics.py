"""
Performance Metrics System

This module provides performance metrics collection and reporting for the
MCP Learning Server, including request tracking, response times, and
resource usage monitoring.
"""

import time
import threading
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

from .logging_config import get_logger


class PerformanceMetrics:
    """
    Performance metrics collection and reporting system.
    
    Tracks various server performance metrics including request counts,
    response times, error rates, and resource usage.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize performance metrics.
        
        Args:
            max_history: Maximum number of historical entries to keep
        """
        self.logger = get_logger("mcp_metrics")
        self.max_history = max_history
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Basic counters
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
        
        # Request tracking
        self.requests_by_type: Dict[str, int] = defaultdict(int)
        self.errors_by_type: Dict[str, int] = defaultdict(int)
        
        # Tool usage tracking
        self.tool_calls: Dict[str, int] = defaultdict(int)
        self.tool_errors: Dict[str, int] = defaultdict(int)
        self.tool_response_times: Dict[str, List[float]] = defaultdict(list)
        
        # Resource usage tracking
        self.resource_requests: Dict[str, int] = defaultdict(int)
        self.resource_cache_hits = 0
        self.resource_cache_misses = 0
        
        # Prompt usage tracking
        self.prompt_requests: Dict[str, int] = defaultdict(int)
        self.prompt_render_times: List[float] = []
        
        # Response time tracking
        self.response_times: deque = deque(maxlen=max_history)
        self.active_requests: Dict[str, float] = {}
        
        # Periodic metrics
        self.metrics_snapshots: List[Dict[str, Any]] = []
        self.last_snapshot_time = datetime.now()
        
        self.logger.info("Performance metrics initialized")
    
    def start_request(self, request_id: str, request_type: str) -> None:
        """
        Start tracking a request.
        
        Args:
            request_id: Unique identifier for the request
            request_type: Type of request (e.g., 'call_tool', 'list_resources')
        """
        with self._lock:
            self.request_count += 1
            self.requests_by_type[request_type] += 1
            self.active_requests[request_id] = time.time()
            
            self.logger.debug(f"Started tracking request {request_id} ({request_type})")
    
    def end_request(self, request_id: str, success: bool = True) -> Optional[float]:
        """
        End tracking a request and record response time.
        
        Args:
            request_id: Unique identifier for the request
            success: Whether the request was successful
            
        Returns:
            Response time in seconds, or None if request not found
        """
        with self._lock:
            if request_id not in self.active_requests:
                self.logger.warning(f"Request {request_id} not found in active requests")
                return None
            
            start_time = self.active_requests.pop(request_id)
            response_time = time.time() - start_time
            
            self.response_times.append(response_time)
            
            if not success:
                self.error_count += 1
            
            self.logger.debug(f"Completed request {request_id} in {response_time:.3f}s (success={success})")
            return response_time
    
    def record_error(self, error_type: str, request_type: str = None) -> None:
        """
        Record an error occurrence.
        
        Args:
            error_type: Type of error
            request_type: Type of request that caused the error
        """
        with self._lock:
            self.error_count += 1
            self.errors_by_type[error_type] += 1
            
            if request_type:
                self.errors_by_type[f"{request_type}_{error_type}"] += 1
            
            self.logger.debug(f"Recorded error: {error_type} (request_type={request_type})")
    
    def record_tool_call(self, tool_name: str, response_time: float = None, success: bool = True) -> None:
        """
        Record a tool call.
        
        Args:
            tool_name: Name of the tool called
            response_time: Time taken to execute the tool
            success: Whether the tool call was successful
        """
        with self._lock:
            self.tool_calls[tool_name] += 1
            
            if response_time is not None:
                self.tool_response_times[tool_name].append(response_time)
                # Keep only recent response times
                if len(self.tool_response_times[tool_name]) > self.max_history:
                    self.tool_response_times[tool_name] = self.tool_response_times[tool_name][-self.max_history:]
            
            if not success:
                self.tool_errors[tool_name] += 1
            
            self.logger.debug(f"Recorded tool call: {tool_name} (time={response_time}, success={success})")
    
    def record_resource_request(self, resource_id: str, cache_hit: bool = False) -> None:
        """
        Record a resource request.
        
        Args:
            resource_id: ID of the requested resource
            cache_hit: Whether the request was served from cache
        """
        with self._lock:
            self.resource_requests[resource_id] += 1
            
            if cache_hit:
                self.resource_cache_hits += 1
            else:
                self.resource_cache_misses += 1
            
            self.logger.debug(f"Recorded resource request: {resource_id} (cache_hit={cache_hit})")
    
    def record_prompt_request(self, prompt_id: str, render_time: float = None) -> None:
        """
        Record a prompt request.
        
        Args:
            prompt_id: ID of the requested prompt
            render_time: Time taken to render the prompt
        """
        with self._lock:
            self.prompt_requests[prompt_id] += 1
            
            if render_time is not None:
                self.prompt_render_times.append(render_time)
                # Keep only recent render times
                if len(self.prompt_render_times) > self.max_history:
                    self.prompt_render_times = self.prompt_render_times[-self.max_history:]
            
            self.logger.debug(f"Recorded prompt request: {prompt_id} (render_time={render_time})")
    
    def get_basic_metrics(self) -> Dict[str, Any]:
        """
        Get basic performance metrics.
        
        Returns:
            Dictionary of basic metrics
        """
        with self._lock:
            uptime = datetime.now() - self.start_time
            
            return {
                "uptime_seconds": uptime.total_seconds(),
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": self.error_count / max(self.request_count, 1),
                "active_requests": len(self.active_requests),
                "average_response_time": self._calculate_average_response_time(),
                "requests_per_second": self.request_count / max(uptime.total_seconds(), 1)
            }
    
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics.
        
        Returns:
            Dictionary of detailed metrics
        """
        with self._lock:
            basic_metrics = self.get_basic_metrics()
            
            detailed_metrics = {
                **basic_metrics,
                "requests_by_type": dict(self.requests_by_type),
                "errors_by_type": dict(self.errors_by_type),
                "tool_metrics": self._get_tool_metrics(),
                "resource_metrics": self._get_resource_metrics(),
                "prompt_metrics": self._get_prompt_metrics(),
                "response_time_percentiles": self._calculate_response_time_percentiles()
            }
            
            return detailed_metrics
    
    def _get_tool_metrics(self) -> Dict[str, Any]:
        """Get tool-specific metrics."""
        tool_metrics = {}
        
        for tool_name in set(list(self.tool_calls.keys()) + list(self.tool_errors.keys())):
            calls = self.tool_calls[tool_name]
            errors = self.tool_errors[tool_name]
            response_times = self.tool_response_times[tool_name]
            
            tool_metrics[tool_name] = {
                "calls": calls,
                "errors": errors,
                "error_rate": errors / max(calls, 1),
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "total_response_time": sum(response_times)
            }
        
        return tool_metrics
    
    def _get_resource_metrics(self) -> Dict[str, Any]:
        """Get resource-specific metrics."""
        total_requests = self.resource_cache_hits + self.resource_cache_misses
        
        return {
            "total_requests": total_requests,
            "cache_hits": self.resource_cache_hits,
            "cache_misses": self.resource_cache_misses,
            "cache_hit_rate": self.resource_cache_hits / max(total_requests, 1),
            "requests_by_resource": dict(self.resource_requests)
        }
    
    def _get_prompt_metrics(self) -> Dict[str, Any]:
        """Get prompt-specific metrics."""
        return {
            "total_requests": sum(self.prompt_requests.values()),
            "requests_by_prompt": dict(self.prompt_requests),
            "average_render_time": sum(self.prompt_render_times) / len(self.prompt_render_times) if self.prompt_render_times else 0,
            "total_render_time": sum(self.prompt_render_times)
        }
    
    def _calculate_average_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def _calculate_response_time_percentiles(self) -> Dict[str, float]:
        """Calculate response time percentiles."""
        if not self.response_times:
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}
        
        sorted_times = sorted(self.response_times)
        length = len(sorted_times)
        
        return {
            "p50": sorted_times[int(length * 0.5)],
            "p90": sorted_times[int(length * 0.9)],
            "p95": sorted_times[int(length * 0.95)],
            "p99": sorted_times[int(length * 0.99)]
        }
    
    def take_snapshot(self) -> Dict[str, Any]:
        """
        Take a snapshot of current metrics.
        
        Returns:
            Snapshot of current metrics
        """
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.get_detailed_metrics()
        }
        
        with self._lock:
            self.metrics_snapshots.append(snapshot)
            # Keep only recent snapshots
            if len(self.metrics_snapshots) > 100:
                self.metrics_snapshots = self.metrics_snapshots[-100:]
            
            self.last_snapshot_time = datetime.now()
        
        return snapshot
    
    def get_snapshots(self, since: datetime = None) -> List[Dict[str, Any]]:
        """
        Get metrics snapshots.
        
        Args:
            since: Only return snapshots after this time
            
        Returns:
            List of metrics snapshots
        """
        with self._lock:
            if since is None:
                return self.metrics_snapshots.copy()
            
            return [
                snapshot for snapshot in self.metrics_snapshots
                if datetime.fromisoformat(snapshot["timestamp"]) > since
            ]
    
    def reset_metrics(self) -> None:
        """Reset all metrics to initial state."""
        with self._lock:
            self.request_count = 0
            self.error_count = 0
            self.start_time = datetime.now()
            
            self.requests_by_type.clear()
            self.errors_by_type.clear()
            self.tool_calls.clear()
            self.tool_errors.clear()
            self.tool_response_times.clear()
            self.resource_requests.clear()
            self.resource_cache_hits = 0
            self.resource_cache_misses = 0
            self.prompt_requests.clear()
            self.prompt_render_times.clear()
            self.response_times.clear()
            self.active_requests.clear()
            self.metrics_snapshots.clear()
            
            self.logger.info("Performance metrics reset")


class MetricsContext:
    """Context manager for tracking request metrics."""
    
    def __init__(self, metrics: PerformanceMetrics, request_id: str, request_type: str):
        """
        Initialize metrics context.
        
        Args:
            metrics: Metrics instance
            request_id: Unique request identifier
            request_type: Type of request
        """
        self.metrics = metrics
        self.request_id = request_id
        self.request_type = request_type
        self.success = True
    
    def __enter__(self):
        """Start tracking the request."""
        self.metrics.start_request(self.request_id, self.request_type)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End tracking the request."""
        if exc_type is not None:
            self.success = False
            self.metrics.record_error(exc_type.__name__, self.request_type)
        
        self.metrics.end_request(self.request_id, self.success)
    
    def mark_error(self, error_type: str = None):
        """Mark the request as failed."""
        self.success = False
        if error_type:
            self.metrics.record_error(error_type, self.request_type)
