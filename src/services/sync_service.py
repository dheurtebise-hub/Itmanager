"""
Service de synchronisation des emails Outlook
"""

import logging
import threading
import time
from typing import List, Dict, Any
from datetime import datetime
from services.email_connector import OutlookConnector
from services.ai_service import ai_service
from services.notifications import notification_service
from models.ticket import Ticket
from config import config

class SyncService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connector = OutlookConnector(config._config)
        self._sync_thread = None
        self._stop_sync = threading.Event()
        self._is_syncing = False
        self.sync_interval = config.get('sync_interval_minutes', 15) * 60

    def sync_now(self) -> Dict[str, Any]:
        """Synchronise immédiatement."""
        if self._is_syncing:
            return {'status': 'already_syncing'}

        self._is_syncing = True
        try:
            emails = self.connector.get_new_emails(mark_as_read=False)
            new_tickets = []

            for email_data in emails:
                # Catégoriser avec l'IA
                categorization = ai_service.categorize_ticket(email_data)

                # Créer le ticket
                ticket_data = {
                    **email_data,
                    'category': categorization.get('category', 'autre'),
                    'priority': categorization.get('priority', 'medium'),
                    'summary': categorization.get('summary', email_data.get('subject', '')),
                    'ai_categorized': True,
                    'ai_confidence': categorization.get('confidence', 0),
                    'status': 'new'
                }

                ticket_id = Ticket.create(ticket_data)
                if ticket_id:
                    new_tickets.append(ticket_id)

                    # Notification si urgent
                    if ticket_data['priority'] == 'urgent':
                        notification_service.notify_urgent_ticket(ticket_data['subject'])

            # Notification groupée
            if new_tickets:
                notification_service.notify_new_tickets(len(new_tickets))

            self.logger.info(f"Synchronisation terminée: {len(new_tickets)} nouveaux tickets")

            return {
                'status': 'success',
                'new_tickets': len(new_tickets),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Erreur sync: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            self._is_syncing = False

    def start_auto_sync(self):
        """Démarre la synchronisation automatique."""
        if self._sync_thread and self._sync_thread.is_alive():
            return

        self._stop_sync.clear()
        self._sync_thread = threading.Thread(target=self._auto_sync_loop, daemon=True)
        self._sync_thread.start()
        self.logger.info("Auto-sync démarré")

    def stop_auto_sync(self):
        """Arrête la synchronisation automatique."""
        self._stop_sync.set()
        if self._sync_thread:
            self._sync_thread.join(timeout=5)
        self.logger.info("Auto-sync arrêté")

    def _auto_sync_loop(self):
        """Boucle de synchronisation automatique."""
        while not self._stop_sync.is_set():
            try:
                self.sync_now()
            except Exception as e:
                self.logger.error(f"Erreur dans auto-sync: {e}")

            # Attendre l'intervalle
            self._stop_sync.wait(self.sync_interval)

    def is_running(self) -> bool:
        """Vérifie si l'auto-sync est actif."""
        return self._sync_thread is not None and self._sync_thread.is_alive()


sync_service = SyncService()
