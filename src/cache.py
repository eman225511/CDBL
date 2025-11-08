"""
CDBL Caching Module
Provides caching functionality for API calls to reduce flooding and improve performance
"""

import time
import json
import os
from typing import Optional, Dict, Any, Tuple

class APICache:
    """Simple in-memory cache with TTL support for API responses"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        """
        Initialize the cache
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._max_size = 100  # Prevent memory bloat
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get a cached value if it exists and hasn't expired
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
            
        value, timestamp = self._cache[key]
        
        # Check if expired
        if time.time() - timestamp > self._default_ttl:
            del self._cache[key]
            return None
            
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a cached value
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        # Clean up expired entries if cache is getting large
        if len(self._cache) >= self._max_size:
            self._cleanup_expired()
            
        # If still too large, remove oldest entries
        if len(self._cache) >= self._max_size:
            oldest_keys = sorted(self._cache.keys(), 
                               key=lambda k: self._cache[k][1])[:10]
            for old_key in oldest_keys:
                del self._cache[old_key]
        
        cache_ttl = ttl if ttl is not None else self._default_ttl
        self._cache[key] = (value, time.time())
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self._default_ttl
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cached entries"""
        self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)

class RateLimiter:
    """Simple rate limiter to prevent API flooding"""
    
    def __init__(self, min_interval: float = 1.0):
        """
        Initialize rate limiter
        
        Args:
            min_interval: Minimum time between requests in seconds
        """
        self._min_interval = min_interval
        self._last_request = 0.0
        
    def wait_if_needed(self) -> None:
        """Wait if we're making requests too quickly"""
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            wait_time = self._min_interval - elapsed
            time.sleep(wait_time)
        self._last_request = time.time()

# Global instances
skybox_cache = APICache(default_ttl=300)  # 5 minutes for skybox listings
popular_cache = APICache(default_ttl=1800)  # 30 minutes for popular lists
preview_cache = APICache(default_ttl=86400)  # 24 hours for preview images
health_cache = APICache(default_ttl=60)  # 1 minute for health checks

# Rate limiter for API calls
api_rate_limiter = RateLimiter(min_interval=1.0)  # 1 second between requests

def get_cache_stats() -> Dict[str, int]:
    """Get statistics about cache usage"""
    return {
        "skybox_cache_size": skybox_cache.size(),
        "popular_cache_size": popular_cache.size(),
        "preview_cache_size": preview_cache.size(),
        "health_cache_size": health_cache.size()
    }

def clear_all_caches() -> None:
    """Clear all caches"""
    skybox_cache.clear()
    popular_cache.clear()
    preview_cache.clear()
    health_cache.clear()