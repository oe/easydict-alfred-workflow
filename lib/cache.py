"""
Easydict Alfred Workflow - Cache Management

Simple file-based cache for translation results.
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Any


class Cache:
    """Simple file-based cache."""
    
    def __init__(self, cache_dir: Optional[str] = None, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            cache_dir: Cache directory path. Defaults to ~/.cache/easydict/
            ttl: Time to live in seconds. Default 1 hour.
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".cache" / "easydict"
        
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_key(self, key: str) -> str:
        """Generate a hash key for the given string."""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_path(self, key: str) -> Path:
        """Get the cache file path for the given key."""
        return self.cache_dir / f"{self._get_key(key)}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        path = self._get_path(key)
        
        if not path.exists():
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check expiration
            if time.time() - data.get("timestamp", 0) > self.ttl:
                path.unlink()
                return None
            
            return data.get("value")
        except (json.JSONDecodeError, IOError):
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
        """
        path = self._get_path(key)
        
        data = {
            "timestamp": time.time(),
            "key": key,
            "value": value,
        }
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except IOError:
            pass
    
    def delete(self, key: str) -> None:
        """Delete a cache entry."""
        path = self._get_path(key)
        if path.exists():
            path.unlink()
    
    def clear(self) -> None:
        """Clear all cache entries."""
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
            except IOError:
                pass


# Global cache instance
cache = Cache()
