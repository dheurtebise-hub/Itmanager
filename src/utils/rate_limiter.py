"""
Rate limiter pour l'API
"""

from functools import wraps
from flask import request, jsonify
from collections import defaultdict
from datetime import datetime, timedelta
import threading

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        now = datetime.now()

        with self.lock:
            self.requests[client_id] = [
                t for t in self.requests[client_id] if now - t < self.window
            ]

            if len(self.requests[client_id]) >= self.max_requests:
                return False

            self.requests[client_id].append(now)
            return True


api_limiter = RateLimiter(100, 60)
ai_limiter = RateLimiter(20, 60)


def rate_limit(limiter: RateLimiter = api_limiter):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not limiter.is_allowed(request.remote_addr):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            return f(*args, **kwargs)
        return wrapped
    return decorator
