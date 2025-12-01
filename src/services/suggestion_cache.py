"""
Cache LRU pour les suggestions IA
"""

from hashlib import md5
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import threading

class SuggestionCache:
    def __init__(self, max_size: int = 500, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _generate_key(self, category: str, summary: str, priority: str) -> str:
        words = sorted(summary.lower().split())[:20]
        normalized = ' '.join(words)
        content = f"{category}|{priority}|{normalized}"
        return md5(content.encode()).hexdigest()

    def get(self, category: str, summary: str, priority: str) -> Optional[str]:
        key = self._generate_key(category, summary, priority)

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if datetime.now() - entry['timestamp'] < self.ttl:
                    entry['hits'] += 1
                    return entry['suggestion']
                else:
                    del self._cache[key]
        return None

    def set(self, category: str, summary: str, priority: str, suggestion: str) -> None:
        key = self._generate_key(category, summary, priority)

        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            self._cache[key] = {
                'suggestion': suggestion,
                'timestamp': datetime.now(),
                'hits': 0
            }

    def _evict_oldest(self) -> None:
        if not self._cache:
            return
        sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k]['timestamp'])
        for key in sorted_keys[:max(1, len(sorted_keys) // 10)]:
            del self._cache[key]

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'total_hits': sum(e['hits'] for e in self._cache.values())
            }


suggestion_cache = SuggestionCache()
