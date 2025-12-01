"""
Connexion et récupération des emails depuis Outlook via pywin32
"""

import win32com.client
import pythoncom
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional, Tuple

class OutlookConnector:
    def __init__(self, config):
        self.config = config
        self.folders_config = config.get('outlook_folders', [{'name': 'Support', 'enabled': True}])
        self.logger = logging.getLogger(__name__)

    def test_connection(self) -> Tuple[bool, str]:
        """Teste la connexion à Outlook."""
        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            inbox = namespace.GetDefaultFolder(6)

            for folder_config in self.folders_config:
                if folder_config.get('enabled', True):
                    folder_name = folder_config['name']
                    try:
                        folder = inbox.Folders[folder_name]
                        count = folder.Items.Count
                        return True, f"✓ Connexion réussie. {count} emails dans '{folder_name}'"
                    except:
                        return False, f"✗ Le dossier '{folder_name}' n'existe pas"

            return False, "✗ Aucun dossier configuré"
        except Exception as e:
            return False, f"✗ Impossible de se connecter à Outlook : {str(e)}"
        finally:
            pythoncom.CoUninitialize()

    def list_available_folders(self) -> List[Dict[str, Any]]:
        """Liste tous les dossiers disponibles."""
        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            inbox = namespace.GetDefaultFolder(6)

            folders = []
            for folder in inbox.Folders:
                folders.append({
                    'name': folder.Name,
                    'count': folder.Items.Count,
                    'has_subfolders': folder.Folders.Count > 0
                })
            return folders
        except Exception as e:
            self.logger.error(f"Erreur liste dossiers: {e}")
            return []
        finally:
            pythoncom.CoUninitialize()

    def get_new_emails(self, mark_as_read: bool = False, limit: int = None) -> List[Dict[str, Any]]:
        """Récupère les nouveaux emails de tous les dossiers activés."""
        all_emails = []

        for folder_config in self.folders_config:
            if not folder_config.get('enabled', True):
                continue

            folder_name = folder_config['name']
            priority_boost = folder_config.get('priority_boost', 0)

            try:
                emails = self._get_emails_from_folder(folder_name, mark_as_read, limit)

                for email in emails:
                    email['priority_boost'] = priority_boost
                    email['source_folder'] = folder_name

                all_emails.extend(emails)
            except Exception as e:
                self.logger.error(f"Erreur dossier '{folder_name}': {e}")

        all_emails.sort(key=lambda x: x.get('received_date', ''), reverse=True)
        return all_emails

    def _get_emails_from_folder(self, folder_name: str, mark_as_read: bool, limit: int) -> List[Dict[str, Any]]:
        """Récupère les emails d'un dossier spécifique."""
        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            inbox = namespace.GetDefaultFolder(6)

            folder = inbox
            for part in folder_name.split('/'):
                folder = folder.Folders[part]

            emails = []
            items = folder.Items
            items.Sort("[ReceivedTime]", True)

            count = 0
            for item in items:
                if limit and count >= limit:
                    break

                if hasattr(item, 'UnRead') and item.UnRead:
                    email_data = self._extract_email_data(item)
                    emails.append(email_data)
                    count += 1

                    if mark_as_read:
                        item.UnRead = False
                        item.Save()

            return emails
        except Exception as e:
            self.logger.error(f"Erreur accès dossier {folder_name}: {e}")
            return []
        finally:
            pythoncom.CoUninitialize()

    def _extract_email_data(self, item) -> Dict[str, Any]:
        """Extrait les données d'un email Outlook."""
        return {
            'message_id': item.EntryID,
            'subject': item.Subject or '(Sans sujet)',
            'sender_email': self._get_sender_email(item),
            'sender_name': item.SenderName or '',
            'body': (item.Body or '')[:5000],
            'html_body': (item.HTMLBody or '')[:10000] if hasattr(item, 'HTMLBody') else None,
            'received_date': item.ReceivedTime.isoformat() if item.ReceivedTime else None,
            'has_attachments': item.Attachments.Count > 0,
            'importance': item.Importance
        }

    def _get_sender_email(self, item) -> str:
        """Extrait l'email de l'expéditeur."""
        try:
            if item.SenderEmailType == "EX":
                sender = item.Sender
                if sender:
                    return sender.GetExchangeUser().PrimarySmtpAddress
            return item.SenderEmailAddress or ''
        except:
            return item.SenderEmailAddress or ''
