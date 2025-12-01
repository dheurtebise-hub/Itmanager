"""
Stockage sécurisé des clés API via Windows Credential Manager
"""

import keyring
import logging
from typing import Optional

class SecureStorage:
    SERVICE_NAME = "ITTicketManager"
    CLAUDE_API_KEY = "claude_api_key"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def store_secret(self, key_name: str, value: str) -> bool:
        try:
            keyring.set_password(self.SERVICE_NAME, key_name, value)
            self.logger.info(f"Secret '{key_name}' stocké")
            return True
        except Exception as e:
            self.logger.error(f"Erreur stockage: {e}")
            return False

    def get_secret(self, key_name: str) -> Optional[str]:
        try:
            return keyring.get_password(self.SERVICE_NAME, key_name)
        except Exception as e:
            self.logger.error(f"Erreur récupération: {e}")
            return None

    def delete_secret(self, key_name: str) -> bool:
        try:
            keyring.delete_password(self.SERVICE_NAME, key_name)
            return True
        except Exception:
            return True

    def has_secret(self, key_name: str) -> bool:
        return self.get_secret(key_name) is not None

    def store_claude_api_key(self, api_key: str) -> bool:
        return self.store_secret(self.CLAUDE_API_KEY, api_key)

    def get_claude_api_key(self) -> Optional[str]:
        return self.get_secret(self.CLAUDE_API_KEY)

    def has_claude_api_key(self) -> bool:
        return self.has_secret(self.CLAUDE_API_KEY)


secure_storage = SecureStorage()
