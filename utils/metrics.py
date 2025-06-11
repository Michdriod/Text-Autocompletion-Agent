# Performance metrics and monitoring utilities
# Tracks API usage, response times, and system performance

import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
from datetime import datetime, timedelta

@dataclass
class RequestMetric:
    """Individual request metric data."""
    timestamp: float
    endpoint: str
    method: str
    status_code: int
    response_time: float
    mode: Optional[str] = None
    input_length: Optional[int] = None
    output_length: Optional[int] = None
    cached: bool = False
    error: Optional[str] = None

class MetricsCollector:
    """Collects and aggregates performance metrics."""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics: deque = deque(maxlen=max_history)
        self.lock = threading.Lock()
        
        # Aggregated counters
        self.total_requests = 0
        self.total_errors = 0
        self.total_cache_hits = 0
        self.mode_counts = defaultdict(int)
        self.endpoint_counts = defaultdict(int)
        
        # Response time tracking
        self.response_times = deque(maxlen=1000)  # Keep last 1000 response times
        
    def record_request(self, metric: RequestMetric) -> None:
        """Record a new request metric."""
        with self.lock:
            self.metrics.append(metric)
            self.total_requests += 1
            
            if metric.status_code >= 400:
                self.total_errors += 1
            
            if metric.cached:
                self.total_cache_hits += 1
            
            if metric.mode:
                self.mode_counts[metric.mode] += 1
            
            self.endpoint_counts[metric.endpoint] += 1
            self.response_times.append(metric.response_time)
    
    def get_summary_stats(self, time_window: Optional[int] = None) -> Dict[str, Any]:
        """Get summary statistics for the specified time window (in seconds)."""
        with self.lock:
            if time_window:
                cutoff_time = time.time() - time_window
                recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            else:
                recent_metrics = list(self.metrics)
            
            if not recent_metrics:
                return {"message": "No metrics available"}
            
            # Calculate statistics
            total_requests = len(recent_metrics)
            error_count = sum(1 for m in recent_metrics if m.status_code >= 400)
            cache_hits = sum(1 for m in recent_metrics if m.cached)
            
            response_times = [m.response_time for m in recent_metrics]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Mode distribution
            mode_dist = defaultdict(int)
            for metric in recent_metrics:
                if metric.mode:
                    mode_dist[metric.mode] += 1
            
            # Endpoint distribution
            endpoint_dist = defaultdict(int)
            for metric in recent_metrics:
                endpoint_dist[metric.endpoint] += 1
            
            return {
                "time_window_seconds": time_window,
                "total_requests": total_requests,
                "error_rate": error_count / total_requests if total_requests > 0 else 0,
                "cache_hit_rate": cache_hits / total_requests if total_requests > 0 else 0,
                "average_response_time": avg_response_time,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "mode_distribution": dict(mode_dist),
                "endpoint_distribution": dict(endpoint_dist),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error metrics."""
        with self.lock:
            errors = [
                {
                    "timestamp": datetime.fromtimestamp(m.timestamp).isoformat(),
                    "endpoint": m.endpoint,
                    "method": m.method,
                    "status_code": m.status_code,
                    "error": m.error,
                    "response_time": m.response_time
                }
                for m in reversed(self.metrics)
                if m.status_code >= 400
            ][:limit]
            
            return errors
    
    def get_performance_trends(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get performance trends over time."""
        with self.lock:
            cutoff_time = time.time() - time_window
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return {"message": "No metrics available"}
            
            # Group by time buckets (5-minute intervals)
            bucket_size = 300  # 5 minutes
            buckets = defaultdict(list)
            
            for metric in recent_metrics:
                bucket = int(metric.timestamp // bucket_size) * bucket_size
                buckets[bucket].append(metric)
            
            trends = []
            for bucket_time in sorted(buckets.keys()):
                bucket_metrics = buckets[bucket_time]
                response_times = [m.response_time for m in bucket_metrics]
                
                trends.append({
                    "timestamp": datetime.fromtimestamp(bucket_time).isoformat(),
                    "request_count": len(bucket_metrics),
                    "avg_response_time": sum(response_times) / len(response_times),
                    "error_count": sum(1 for m in bucket_metrics if m.status_code >= 400),
                    "cache_hits": sum(1 for m in bucket_metrics if m.cached)
                })
            
            return {
                "time_window_seconds": time_window,
                "bucket_size_seconds": bucket_size,
                "trends": trends
            }
    
    def cleanup_old_metrics(self, max_age_seconds: int = 86400) -> int:
        """Remove metrics older than max_age_seconds. Returns count of removed metrics."""
        cutoff_time = time.time() - max_age_seconds
        
        with self.lock:
            original_count = len(self.metrics)
            # Convert to list, filter, then back to deque
            filtered_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            self.metrics.clear()
            self.metrics.extend(filtered_metrics)
            
            removed_count = original_count - len(self.metrics)
            return removed_count

# Global metrics collector instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get or create singleton metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

# Decorator for automatic metrics collection
def track_performance(endpoint: str, mode: Optional[str] = None):
    """Decorator to automatically track performance metrics."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            collector = get_metrics_collector()
            
            try:
                result = await func(*args, **kwargs)
                response_time = time.time() - start_time
                
                # Extract additional info from result if available
                input_length = getattr(result, 'input_length', None)
                output_length = getattr(result, 'output_length', None)
                cached = getattr(result, 'cached', False)
                
                metric = RequestMetric(
                    timestamp=start_time,
                    endpoint=endpoint,
                    method="POST",  # Most API calls are POST
                    status_code=200,
                    response_time=response_time,
                    mode=mode,
                    input_length=input_length,
                    output_length=output_length,
                    cached=cached
                )
                
                collector.record_request(metric)
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                
                metric = RequestMetric(
                    timestamp=start_time,
                    endpoint=endpoint,
                    method="POST",
                    status_code=500,
                    response_time=response_time,
                    mode=mode,
                    error=str(e)
                )
                
                collector.record_request(metric)
                raise
        
        return async_wrapper
    return decorator
