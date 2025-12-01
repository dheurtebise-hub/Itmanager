"""
Configuration de l'application
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from services.secure_storage import secure_storage

class Config:
    DEFAULT_CONFIG = {
        "app_name": "IT Ticket Manager",
        "version": "1.0.0",
        "outlook_folders": [
            {"name": "Support", "enabled": True, "priority_boost": 0}
        ],
        "sync_interval_minutes": 15,
        "auto_sync": True,
        "ai_model_categorize": "claude-haiku-4-5-20251001",
        "ai_model_suggest": "claude-sonnet-4-5-20250929",
        "monthly_budget_euros": 5.0,
        "categories": [],
        "theme": "light",
        "notifications_enabled": True,
        "sla_enabled": True,
        "first_run_completed": False
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            app_data = os.getenv('APPDATA', os.path.expanduser('~'))
            self.config_dir = Path(app_data) / "ITTicketManager"
            self.config_path = self.config_dir / "config.json"
        else:
            self.config_path = Path(config_path)
            self.config_dir = self.config_path.parent

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    return {**self.DEFAULT_CONFIG, **loaded}
            except Exception:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save(self) -> bool:
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    @property
    def claude_api_key(self) -> Optional[str]:
        return secure_storage.get_claude_api_key()

    @claude_api_key.setter
    def claude_api_key(self, value: str) -> None:
        secure_storage.store_claude_api_key(value)

    def has_api_key(self) -> bool:
        return secure_storage.has_claude_api_key()


config = Config()
