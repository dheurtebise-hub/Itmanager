"""
Backup automatique de la base de données
"""

import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import logging
import threading
import time

class BackupService:
    def __init__(self, db_path: str = None, backup_dir: str = None):
        self.logger = logging.getLogger(__name__)

        from config import config

        if db_path is None:
            db_path = str(config.config_dir / 'database' / 'tickets.db')
        if backup_dir is None:
            backup_dir = str(config.config_dir / 'backups')

        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self._scheduler_thread = None
        self._stop_scheduler = threading.Event()
        self.max_backups = 7
        self.backup_hour = 3

    def create_backup(self, compress: bool = True) -> Optional[Path]:
        if not self.db_path.exists():
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if compress:
            backup_path = self.backup_dir / f"backup_{timestamp}.db.gz"
            try:
                with open(self.db_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            except Exception as e:
                self.logger.error(f"Erreur backup: {e}")
                return None
        else:
            backup_path = self.backup_dir / f"backup_{timestamp}.db"
            shutil.copy2(self.db_path, backup_path)

        self._cleanup_old_backups()
        self.logger.info(f"Backup créé: {backup_path}")
        return backup_path

    def restore_backup(self, backup_path: Path) -> bool:
        if not backup_path.exists():
            return False

        try:
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(self.db_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            self.logger.error(f"Erreur restauration: {e}")
            return False

    def list_backups(self) -> List[dict]:
        backups = []
        for file in sorted(self.backup_dir.glob('backup_*'), reverse=True):
            stat = file.stat()
            backups.append({
                'path': str(file),
                'name': file.name,
                'size_mb': round(stat.st_size / 1024 / 1024, 2),
                'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        return backups

    def _cleanup_old_backups(self):
        cutoff = datetime.now() - timedelta(days=self.max_backups)
        for file in self.backup_dir.glob('backup_*'):
            try:
                date_str = file.stem.split('_')[1]
                file_date = datetime.strptime(date_str, '%Y%m%d')
                if file_date < cutoff:
                    file.unlink()
            except Exception:
                pass

    def start_scheduler(self):
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return

        self._stop_scheduler.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def _scheduler_loop(self):
        """Boucle du planificateur pour backups et archivage."""
        while not self._stop_scheduler.is_set():
            now = datetime.now()
            if now.hour == self.backup_hour and now.minute == 0:
                # Créer un backup
                self.create_backup()

                # Lancer l'archivage automatique des tickets résolus depuis 7 jours
                try:
                    from services.archive_service import archive_service
                    self.logger.info("Lancement de l'archivage automatique des tickets")
                    result = archive_service.archive_old_resolved_tickets()
                    self.logger.info(f"Archivage: {result['archived']} tickets archivés, "
                                   f"{result['moved_emails']} emails déplacés")
                except Exception as e:
                    self.logger.error(f"Erreur archivage automatique: {e}")

                time.sleep(3600)  # Attendre 1h pour éviter les doublons
            else:
                time.sleep(60)  # Vérifier chaque minute


backup_service = BackupService()
