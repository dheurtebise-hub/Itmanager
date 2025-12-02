"""
Gestion automatique des dossiers Outlook pour le cycle de vie des tickets
"""

import win32com.client
import pythoncom
import logging
from typing import List, Dict, Tuple, Optional

class OutlookFolderManager:
    """Gestionnaire pour créer et déplacer des emails dans les dossiers Outlook."""

    # Noms des dossiers de l'application
    FOLDERS = {
        'import': 'App-Import',
        'in_progress': 'App-EnCours',
        'resolved': 'App-Cloturé',
        'archive': 'App-Archives'
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def ensure_folders_exist(self) -> Tuple[bool, str]:
        """Crée les dossiers de l'application s'ils n'existent pas."""
        outlook = None
        namespace = None
        inbox = None

        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            inbox = namespace.GetDefaultFolder(6)  # olFolderInbox

            created = []
            existing = []

            for folder_type, folder_name in self.FOLDERS.items():
                try:
                    # Tenter d'accéder au dossier
                    folder = inbox.Folders[folder_name]
                    existing.append(folder_name)
                    self.logger.info(f"Dossier '{folder_name}' existe déjà")
                except Exception:
                    # Le dossier n'existe pas, le créer
                    try:
                        new_folder = inbox.Folders.Add(folder_name)
                        created.append(folder_name)
                        self.logger.info(f"Dossier '{folder_name}' créé avec succès")
                    except Exception as e:
                        self.logger.error(f"Erreur création dossier '{folder_name}': {e}")
                        return False, f"Erreur création dossier '{folder_name}': {str(e)}"

            msg = f"✓ Dossiers vérifiés: {len(existing)} existants, {len(created)} créés"
            return True, msg

        except Exception as e:
            self.logger.error(f"Erreur configuration dossiers: {e}")
            return False, f"Erreur: {str(e)}"
        finally:
            if inbox:
                try:
                    del inbox
                except:
                    pass
            if namespace:
                try:
                    del namespace
                except:
                    pass
            if outlook:
                try:
                    del outlook
                except:
                    pass
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def move_email_to_folder(self, message_id: str, target_folder_key: str) -> Tuple[bool, str]:
        """
        Déplace un email vers un dossier spécifique.

        Args:
            message_id: L'EntryID de l'email à déplacer
            target_folder_key: Clé du dossier cible ('import', 'in_progress', 'resolved', 'archive')

        Returns:
            Tuple (success, message)
        """
        if target_folder_key not in self.FOLDERS:
            return False, f"Dossier cible invalide: {target_folder_key}"

        target_folder_name = self.FOLDERS[target_folder_key]
        outlook = None
        namespace = None
        inbox = None
        target_folder = None
        item = None

        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")

            # Récupérer l'email par son EntryID
            try:
                item = namespace.GetItemFromID(message_id)
            except Exception as e:
                self.logger.warning(f"Email {message_id[:20]}... non trouvé (peut-être déjà déplacé): {e}")
                return True, "Email introuvable (déjà déplacé?)"

            # Récupérer le dossier cible
            inbox = namespace.GetDefaultFolder(6)
            target_folder = inbox.Folders[target_folder_name]

            # Déplacer l'email
            item.Move(target_folder)

            self.logger.info(f"Email déplacé vers '{target_folder_name}'")
            return True, f"Email déplacé vers '{target_folder_name}'"

        except Exception as e:
            self.logger.error(f"Erreur déplacement email: {e}")
            return False, f"Erreur: {str(e)}"
        finally:
            if item:
                try:
                    del item
                except:
                    pass
            if target_folder:
                try:
                    del target_folder
                except:
                    pass
            if inbox:
                try:
                    del inbox
                except:
                    pass
            if namespace:
                try:
                    del namespace
                except:
                    pass
            if outlook:
                try:
                    del outlook
                except:
                    pass
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def move_ticket_email(self, message_id: str, new_status: str) -> Tuple[bool, str]:
        """
        Déplace l'email d'un ticket selon son nouveau statut.

        Args:
            message_id: L'EntryID de l'email
            new_status: Le nouveau statut du ticket ('new', 'in_progress', 'resolved')

        Returns:
            Tuple (success, message)
        """
        # Mapping statut → dossier
        status_to_folder = {
            'new': 'import',
            'in_progress': 'in_progress',
            'resolved': 'resolved'
        }

        if new_status not in status_to_folder:
            return False, f"Statut invalide: {new_status}"

        folder_key = status_to_folder[new_status]
        return self.move_email_to_folder(message_id, folder_key)


folder_manager = OutlookFolderManager()
