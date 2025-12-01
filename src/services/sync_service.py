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

    def sync_now(self, initial_import: bool = False, import_limit: int = 50) -> Dict[str, Any]:
        """Synchronise immédiatement.

        Args:
            initial_import: Si True, importe tous les emails récents (pas seulement non lus)
            import_limit: Nombre max d'emails à importer (50 par défaut)
        """
        if self._is_syncing:
            self.logger.warning("Synchronisation déjà en cours")
            return {'status': 'already_syncing'}

        self._is_syncing = True
        self.logger.info(f"Début synchronisation (initial_import={initial_import}, limit={import_limit})")

        try:
            # Récupérer les emails
            # En mode initial, on récupère tous les emails (pas seulement non lus)
            only_unread = not initial_import
            emails = self.connector.get_new_emails(
                mark_as_read=False,
                limit=import_limit,
                only_unread=only_unread
            )

            self.logger.info(f"{len(emails)} emails récupérés depuis Outlook")

            if not emails:
                self.logger.info("Aucun nouvel email à synchroniser")
                return {
                    'status': 'success',
                    'new_tickets': 0,
                    'emails_found': 0,
                    'timestamp': datetime.now().isoformat()
                }

            new_tickets = []
            skipped = 0

            for i, email_data in enumerate(emails, 1):
                self.logger.debug(f"Traitement email {i}/{len(emails)}: {email_data.get('subject', 'Sans sujet')[:50]}")

                try:
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
                        self.logger.info(f"Ticket #{ticket_id} créé: {ticket_data.get('subject', 'Sans sujet')[:50]}")

                        # Notification si urgent
                        if ticket_data['priority'] == 'urgent':
                            notification_service.notify_urgent_ticket(ticket_data['subject'])
                    else:
                        skipped += 1
                        self.logger.debug(f"Ticket skipped (déjà existant): {email_data.get('subject', '')[:50]}")

                except Exception as e:
                    self.logger.error(f"Erreur création ticket: {e}", exc_info=True)
                    skipped += 1

            # Notification groupée
            if new_tickets:
                notification_service.notify_new_tickets(len(new_tickets))

            self.logger.info(f"Synchronisation terminée: {len(new_tickets)} nouveaux tickets, {skipped} ignorés")

            return {
                'status': 'success',
                'new_tickets': len(new_tickets),
                'emails_found': len(emails),
                'skipped': skipped,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Erreur sync: {e}", exc_info=True)
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
