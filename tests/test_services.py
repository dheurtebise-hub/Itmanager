"""
Tests unitaires pour les services
"""

import pytest
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from services.suggestion_cache import SuggestionCache
from utils.helpers import time_ago, sanitize_email, truncate_text
from datetime import datetime, timedelta

class TestSuggestionCache:
    def test_cache_set_and_get(self):
        cache = SuggestionCache(max_size=10, ttl_hours=1)
        cache.set('category', 'test summary', 'medium', 'test suggestion')
        result = cache.get('category', 'test summary', 'medium')
        assert result == 'test suggestion'

    def test_cache_miss(self):
        cache = SuggestionCache(max_size=10, ttl_hours=1)
        result = cache.get('category', 'nonexistent', 'medium')
        assert result is None

    def test_cache_clear(self):
        cache = SuggestionCache(max_size=10, ttl_hours=1)
        cache.set('category', 'test', 'medium', 'suggestion')
        cache.clear()
        result = cache.get('category', 'test', 'medium')
        assert result is None

class TestHelpers:
    def test_time_ago_recent(self):
        now = datetime.now()
        result = time_ago(now)
        assert result == "à l'instant"

    def test_time_ago_minutes(self):
        dt = datetime.now() - timedelta(minutes=5)
        result = time_ago(dt)
        assert 'min' in result

    def test_time_ago_hours(self):
        dt = datetime.now() - timedelta(hours=2)
        result = time_ago(dt)
        assert 'h' in result

    def test_sanitize_email_valid(self):
        email = sanitize_email('Test@Example.COM')
        assert email == 'test@example.com'

    def test_sanitize_email_invalid(self):
        email = sanitize_email('invalid-email')
        assert email == ''

    def test_truncate_text(self):
        text = 'A' * 200
        result = truncate_text(text, max_length=50)
        assert len(result) == 50
        assert result.endswith('...')

    def test_truncate_text_short(self):
        text = 'Short text'
        result = truncate_text(text, max_length=100)
        assert result == text

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
