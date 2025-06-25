import time
import threading
from typing import Any, Dict, Optional

class CacheManager:
    """Cache manager for reducing API calls and improving performance"""
    
    def __init__(self):
        self._cache: Dict[str, tuple] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str, ttl: int = 30) -> Optional[Any]:
        """
        Get value from cache if not expired
        :param key: Cache key
        :param ttl: Time to live in seconds
        :return: Cached value or None if expired/not found
        """
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < ttl:
                    return value
                else:
                    # Remove expired entry
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int = 30) -> None:
        """
        Set value in cache with TTL
        :param key: Cache key
        :param value: Value to cache
        :param ttl: Time to live in seconds
        """
        with self._lock:
            self._cache[key] = (value, time.time())
    
    def invalidate(self, key: str) -> None:
        """Remove specific key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> None:
        """Remove all expired entries from cache"""
        current_time = time.time()
        with self._lock:
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items()
                if current_time - timestamp > 300  # 5 minutes default TTL
            ]
            for key in expired_keys:
                del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                'total_entries': len(self._cache),
                'cache_size': sum(len(str(v)) for v, _ in self._cache.values())
            } 