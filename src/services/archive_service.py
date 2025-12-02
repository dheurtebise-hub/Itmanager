"""
Service d'archivage automatique des tickets résolus depuis 7 jours
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from models.database import db
from services.outlook_folder_manager import folder_manager

class ArchiveService:
    """Service pour archiver automatiquement les tickets résolus."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.archive_delay_days = 7

    def archive_old_resolved_tickets(self) -> Dict:
        """Archive les tickets résolus depuis plus de 7 jours."""
        try:
            # Date limite: 7 jours avant aujourd'hui
            cutoff_date = (datetime.now() - timedelta(days=self.archive_delay_days)).isoformat()

            # Trouver les tickets résolus depuis plus de 7 jours
            tickets_to_archive = db.fetchall("""
                SELECT id, message_id, subject, resolved_at
                FROM tickets
                WHERE status = 'resolved'
                AND resolved_at IS NOT NULL
                AND resolved_at < ?
            """, (cutoff_date,))

            if not tickets_to_archive:
                self.logger.info("Aucun ticket à archiver")
                return {
                    'archived': 0,
                    'moved_emails': 0,
                    'errors': 0
                }

            archived_count = 0
            moved_emails_count = 0
            errors = []

            for ticket in tickets_to_archive:
                ticket_id = ticket['id']
                message_id = ticket['message_id']

                try:
                    # Déplacer l'email vers App-Archives
                    if message_id:
                        success, msg = folder_manager.move_email_to_folder(message_id, 'archive')
                        if success:
                            moved_emails_count += 1
                            self.logger.info(f"Ticket #{ticket_id}: email archivé")
                        else:
                            self.logger.warning(f"Ticket #{ticket_id}: échec déplacement email: {msg}")
                            errors.append(f"Ticket #{ticket_id}: {msg}")

                    # Supprimer le ticket de la base de données
                    db.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
                    archived_count += 1
                    self.logger.info(f"Ticket #{ticket_id} archivé et supprimé")

                except Exception as e:
                    self.logger.error(f"Erreur archivage ticket #{ticket_id}: {e}")
                    errors.append(f"Ticket #{ticket_id}: {str(e)}")

            result = {
                'archived': archived_count,
                'moved_emails': moved_emails_count,
                'errors': len(errors),
                'error_details': errors if errors else None
            }

            self.logger.info(f"Archivage terminé: {archived_count} tickets archivés, {moved_emails_count} emails déplacés")
            return result

        except Exception as e:
            self.logger.error(f"Erreur processus d'archivage: {e}", exc_info=True)
            return {
                'archived': 0,
                'moved_emails': 0,
                'errors': 1,
                'error_details': [str(e)]
            }

    def get_tickets_to_archive_count(self) -> int:
        """Retourne le nombre de tickets qui seront archivés."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=self.archive_delay_days)).isoformat()
            result = db.fetchone("""
                SELECT COUNT(*) as count
                FROM tickets
                WHERE status = 'resolved'
                AND resolved_at IS NOT NULL
                AND resolved_at < ?
            """, (cutoff_date,))
            return result['count'] if result else 0
        except Exception as e:
            self.logger.error(f"Erreur comptage tickets à archiver: {e}")
            return 0


archive_service = ArchiveService()
