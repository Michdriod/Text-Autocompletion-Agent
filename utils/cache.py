# Simple in-memory cache for text generation results
# Helps reduce API calls for identical requests

import hashlib
import time
from typing import Optional, Dict, Any
import json

class SimpleCache:
    """
    Simple in-memory cache with TTL (Time To Live) support.
    Stores generation results to avoid duplicate API calls.
    """
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, system_prompt: str, user_message: str, **kwargs) -> str:
        """Generate a unique cache key from request parameters."""
        # Create a deterministic hash from all parameters
        data = {
            "system_prompt": system_prompt,
            "user_message": user_message,
            **kwargs
        }
        # Sort keys for consistent hashing
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def get(self, system_prompt: str, user_message: str, **kwargs) -> Optional[str]:
        """Get cached result if available and not expired."""
        key = self._generate_key(system_prompt, user_message, **kwargs)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if entry has expired
        if time.time() > entry["expires_at"]:
            del self.cache[key]
            return None
        
        return entry["result"]
    
    def set(self, system_prompt: str, user_message: str, result: str, ttl: Optional[int] = None, **kwargs) -> None:
        """Store result in cache with TTL."""
        key = self._generate_key(system_prompt, user_message, **kwargs)
        expires_at = time.time() + (ttl or self.default_ttl)
        
        self.cache[key] = {
            "result": result,
            "expires_at": expires_at,
            "created_at": time.time()
        }
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        active_entries = sum(
            1 for entry in self.cache.values()
            if current_time <= entry["expires_at"]
        )
        
        return {
            "total_entries": len(self.cache),
            "active_entries": active_entries,
            "expired_entries": len(self.cache) - active_entries
        }

# Global cache instance
_cache_instance = None

def get_cache() -> SimpleCache:
    """Get or create singleton cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SimpleCache()
    return _cache_instance

def clear_cache() -> None:
    """Clear the global cache."""
    cache = get_cache()
    cache.clear()
