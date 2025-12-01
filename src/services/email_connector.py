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

    def get_new_emails(self, mark_as_read: bool = False, limit: int = None, only_unread: bool = False) -> List[Dict[str, Any]]:
        """Récupère les nouveaux emails de tous les dossiers activés.

        Args:
            mark_as_read: Marquer les emails comme lus après import
            limit: Nombre maximum d'emails à récupérer par dossier
            only_unread: Si True, ne récupère que les emails non lus
        """
        all_emails = []

        for folder_config in self.folders_config:
            if not folder_config.get('enabled', True):
                continue

            folder_name = folder_config['name']
            priority_boost = folder_config.get('priority_boost', 0)

            try:
                emails = self._get_emails_from_folder(folder_name, mark_as_read, limit, only_unread)

                self.logger.info(f"Dossier '{folder_name}': {len(emails)} emails récupérés")

                for email in emails:
                    email['priority_boost'] = priority_boost
                    email['source_folder'] = folder_name

                all_emails.extend(emails)
            except Exception as e:
                self.logger.error(f"Erreur dossier '{folder_name}': {e}", exc_info=True)

        all_emails.sort(key=lambda x: x.get('received_date', ''), reverse=True)
        self.logger.info(f"Total: {len(all_emails)} emails récupérés de tous les dossiers")
        return all_emails

    def _get_emails_from_folder(self, folder_name: str, mark_as_read: bool, limit: int, only_unread: bool) -> List[Dict[str, Any]]:
        """Récupère les emails d'un dossier spécifique."""
        try:
            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            inbox = namespace.GetDefaultFolder(6)

            # Navigation vers le dossier
            folder = inbox
            for part in folder_name.split('/'):
                folder = folder.Folders[part]

            self.logger.info(f"Accès au dossier '{folder_name}', {folder.Items.Count} emails au total")

            emails = []
            items = folder.Items
            items.Sort("[ReceivedTime]", True)  # Tri par date décroissante

            count = 0
            processed = 0

            for item in items:
                processed += 1

                # Limite de traitement
                if limit and count >= limit:
                    break

                # Vérifier si c'est un MailItem
                if not hasattr(item, 'Subject'):
                    continue

                # Filtre : seulement les non lus OU tous les emails
                if only_unread and hasattr(item, 'UnRead') and not item.UnRead:
                    continue

                try:
                    email_data = self._extract_email_data(item)
                    emails.append(email_data)
                    count += 1

                    self.logger.debug(f"Email récupéré: {email_data.get('subject', 'Sans sujet')[:50]}")

                    if mark_as_read and hasattr(item, 'UnRead'):
                        item.UnRead = False
                        item.Save()

                except Exception as e:
                    self.logger.warning(f"Erreur extraction email: {e}")
                    continue

            self.logger.info(f"Dossier '{folder_name}': {count} emails extraits sur {processed} traités")
            return emails

        except Exception as e:
            self.logger.error(f"Erreur accès dossier {folder_name}: {e}", exc_info=True)
            return []
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def _parse_email_thread(self, body: str) -> list:
        """Parse le corps de l'email en messages séparés (comme une conversation)."""
        if not body:
            return []

        import re

        # Patterns de séparation d'emails (lignes "De:", "From:", etc.)
        separator_patterns = [
            r'^(?:De|From)\s*:\s*.+',
            r'^Le .+ a écrit\s*:',
            r'^On .+ wrote\s*:',
            r'^_{5,}',  # Lignes de underscores
            r'^-{5,}',  # Lignes de tirets
        ]

        combined_pattern = '|'.join(f'({p})' for p in separator_patterns)

        # Diviser le texte en messages
        messages = []
        current_message = []

        for line in body.split('\n'):
            # Vérifier si c'est une ligne de séparation
            if re.match(combined_pattern, line.strip(), re.MULTILINE):
                # Sauvegarder le message précédent s'il existe
                if current_message:
                    msg_text = '\n'.join(current_message).strip()
                    if msg_text and len(msg_text) > 5:  # Ignorer les messages trop courts
                        messages.append(msg_text)
                    current_message = []
            else:
                current_message.append(line)

        # Ajouter le dernier message
        if current_message:
            msg_text = '\n'.join(current_message).strip()
            if msg_text and len(msg_text) > 5:
                messages.append(msg_text)

        # Si aucun message parsé, retourner le corps entier
        if not messages:
            messages = [body.strip()]

        return messages

    def _clean_email_body(self, body: str) -> str:
        """Nettoie le corps de l'email en retirant les signatures et éléments indésirables."""
        if not body:
            return body

        import re

        # Supprimer les URLs Letsignit
        body = re.sub(r'<https://cloud\.letsignit\.com/[^>]+>', '', body)
        body = re.sub(r'https://cloud\.letsignit\.com/\S+', '', body)

        # Supprimer les pieds de page courants
        footer_patterns = [
            r'Retrouvez l\'actualité du groupe sur.*?(?:Linkedin|LinkedIn)\.?',
            r'Pensez Environnement\s*!\s*Merci de n\'imprimer cet e?-?mail que si nécessaire\.?',
            r'Merci de n\'imprimer cet e?-?mail que si nécessaire\.?',
            r'Please consider the environment before printing this e?-?mail\.?',
            r'Ce message et toutes les pièces jointes.*?destinataire\.?',
            r'This message and any attachments.*?recipient\.?',
            r'Avertissement\s*:.*?autorisée\.?',
            r'Confidentiality Notice:.*?prohibited\.?',
        ]

        for pattern in footer_patterns:
            body = re.sub(pattern, '', body, flags=re.IGNORECASE | re.DOTALL)

        # Supprimer les lignes vides multiples
        body = re.sub(r'\n\s*\n\s*\n+', '\n\n', body)

        # Supprimer les espaces en fin de lignes
        body = re.sub(r' +\n', '\n', body)

        return body.strip()

    def _extract_email_data(self, item) -> Dict[str, Any]:
        """Extrait les données d'un email Outlook."""
        raw_body = item.Body or ''
        cleaned_body = self._clean_email_body(raw_body)

        return {
            'message_id': item.EntryID,
            'subject': item.Subject or '(Sans sujet)',
            'sender_email': self._get_sender_email(item),
            'sender_name': item.SenderName or '',
            'body': cleaned_body[:5000],
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
