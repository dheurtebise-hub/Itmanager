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
        outlook = None
        namespace = None
        inbox = None
        folder = None
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
                    finally:
                        if folder is not None:
                            try:
                                del folder
                            except:
                                pass
                            folder = None

            return False, "✗ Aucun dossier configuré"
        except Exception as e:
            return False, f"✗ Impossible de se connecter à Outlook : {str(e)}"
        finally:
            # Libérer les objets COM dans le bon ordre
            if folder is not None:
                try:
                    del folder
                except:
                    pass
            if inbox is not None:
                try:
                    del inbox
                except:
                    pass
            if namespace is not None:
                try:
                    del namespace
                except:
                    pass
            if outlook is not None:
                try:
                    del outlook
                except:
                    pass
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def list_available_folders(self) -> List[Dict[str, Any]]:
        """Liste tous les dossiers disponibles."""
        outlook = None
        namespace = None
        inbox = None

        # Retry logic
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                pythoncom.CoInitialize()
                outlook = win32com.client.Dispatch("Outlook.Application")
                namespace = outlook.GetNamespace("MAPI")

                # Tenter d'accéder à l'inbox
                try:
                    inbox = namespace.GetDefaultFolder(6)
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée pour lister dossiers: {e}, retry dans {retry_delay}s...")
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
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise

                folders = []
                folder_count = inbox.Folders.Count

                for i in range(folder_count):
                    folder = None
                    try:
                        # Accès par index (1-based en COM) avec .Item()
                        try:
                            folder = inbox.Folders.Item(i + 1)
                        except Exception as idx_err:
                            self.logger.warning(f"Impossible d'accéder au dossier index {i+1}: {idx_err}")
                            continue

                        folders.append({
                            'name': folder.Name,
                            'count': folder.Items.Count,
                            'has_subfolders': folder.Folders.Count > 0
                        })
                    except Exception as e:
                        self.logger.warning(f"Erreur traitement dossier index {i+1}: {e}")
                        continue
                    finally:
                        if folder is not None:
                            try:
                                del folder
                            except:
                                pass

                self.logger.info(f"{len(folders)} dossiers Outlook trouvés")
                return folders

            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Erreur liste dossiers, tentative {attempt + 1}/{max_retries}: {e}")
                    continue
                else:
                    self.logger.error(f"Erreur liste dossiers après {max_retries} tentatives: {e}")
                    return []
            finally:
                # Libérer les objets COM
                if inbox is not None:
                    try:
                        del inbox
                    except:
                        pass
                if namespace is not None:
                    try:
                        del namespace
                    except:
                        pass
                if outlook is not None:
                    try:
                        del outlook
                    except:
                        pass
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass

        return []

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
        outlook = None
        namespace = None
        inbox = None
        folder = None
        items = None

        # Retry logic pour gérer les problèmes temporaires COM
        max_retries = 3
        retry_delay = 2  # secondes

        for attempt in range(max_retries):
            try:
                pythoncom.CoInitialize()
                outlook = win32com.client.Dispatch("Outlook.Application")
                namespace = outlook.GetNamespace("MAPI")

                # Tenter d'accéder à l'inbox
                try:
                    inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée pour accès inbox: {e}, nouvelle tentative dans {retry_delay}s...")
                        # Nettoyer avant retry
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
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception(f"Impossible d'accéder à la boîte de réception après {max_retries} tentatives. Vérifiez qu'Outlook est en mode connecté et que votre profil est correctement configuré.")

                # Navigation vers le dossier
                folder = inbox
                for part in folder_name.split('/'):
                    self.logger.debug(f"Navigation vers sous-dossier: {part}")
                    folder = folder.Folders[part]

                total_items = folder.Items.Count
                self.logger.info(f"Accès au dossier '{folder_name}', {total_items} emails au total")

                if total_items == 0:
                    self.logger.info(f"Dossier '{folder_name}' vide, aucun email à traiter")
                    return []

                emails = []
                items = folder.Items

                # Tri avec gestion d'erreur
                try:
                    items.Sort("[ReceivedTime]", True)
                    self.logger.debug(f"Tri des emails par date effectué")
                except Exception as e:
                    self.logger.warning(f"Impossible de trier les emails: {e}, utilisation de l'ordre par défaut")

                count = 0
                processed = 0
                items_count = items.Count

                self.logger.debug(f"Début traitement de {items_count} emails (limit={limit}, only_unread={only_unread})")

                for i in range(items_count):
                    # Limite de traitement
                    if limit and count >= limit:
                        self.logger.debug(f"Limite de {limit} emails atteinte, arrêt")
                        break

                    # Récupérer l'item par index (1-based en COM)
                    item = None
                    try:
                        processed += 1
                        # COM collections sont 1-indexées, mais vérifier d'abord si l'index est valide
                        try:
                            item = items.Item(i + 1)  # Utiliser .Item() au lieu de []
                        except Exception as idx_err:
                            self.logger.warning(f"Impossible d'accéder à l'item {i+1}: {idx_err}")
                            continue

                        # Vérifier si c'est un MailItem
                        if not hasattr(item, 'Subject'):
                            self.logger.debug(f"Item {i+1} ignoré (pas un MailItem)")
                            continue

                        # Filtre : seulement les non lus OU tous les emails
                        if only_unread and hasattr(item, 'UnRead') and not item.UnRead:
                            self.logger.debug(f"Item {i+1} ignoré (déjà lu)")
                            continue

                        email_data = self._extract_email_data(item)
                        emails.append(email_data)
                        count += 1

                        if count % 10 == 0:
                            self.logger.info(f"Progression: {count} emails extraits sur {processed} traités")

                        if mark_as_read and hasattr(item, 'UnRead'):
                            item.UnRead = False
                            item.Save()

                    except Exception as e:
                        self.logger.warning(f"Erreur extraction email index {i+1}/{items_count}: {e}")
                        continue
                    finally:
                        # CRITIQUE: Libérer explicitement chaque objet COM item après usage
                        if item is not None:
                            try:
                                del item
                            except:
                                pass

                self.logger.info(f"Dossier '{folder_name}': {count} emails extraits sur {processed} traités")
                return emails

            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Erreur dossier {folder_name}, tentative {attempt + 1}/{max_retries}: {e}")
                    continue
                else:
                    self.logger.error(f"Erreur accès dossier {folder_name} après {max_retries} tentatives: {e}", exc_info=True)
                    return []
            finally:
                # Libérer explicitement tous les objets COM dans le bon ordre
                if items is not None:
                    try:
                        del items
                    except:
                        pass
                if folder is not None:
                    try:
                        del folder
                    except:
                        pass
                if inbox is not None:
                    try:
                        del inbox
                    except:
                        pass
                if namespace is not None:
                    try:
                        del namespace
                    except:
                        pass
                if outlook is not None:
                    try:
                        del outlook
                    except:
                        pass
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass

        return []

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
        sender = None
        exchange_user = None
        try:
            if item.SenderEmailType == "EX":
                sender = item.Sender
                if sender:
                    exchange_user = sender.GetExchangeUser()
                    if exchange_user:
                        email = exchange_user.PrimarySmtpAddress
                        return email
            return item.SenderEmailAddress or ''
        except:
            return item.SenderEmailAddress or ''
        finally:
            # Libérer les objets COM créés
            if exchange_user is not None:
                try:
                    del exchange_user
                except:
                    pass
            if sender is not None:
                try:
                    del sender
                except:
                    pass
