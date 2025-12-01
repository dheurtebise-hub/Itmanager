"""
Notifications Desktop Windows
"""

import threading
import logging
from typing import Callable

try:
    from win10toast_click import ToastNotifier
    HAS_TOAST = True
except ImportError:
    HAS_TOAST = False

class NotificationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.toaster = ToastNotifier() if HAS_TOAST else None
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled and HAS_TOAST

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    def notify(self, title: str, message: str, duration: int = 5,
               on_click: Callable = None, threaded: bool = True):
        if not self.enabled:
            return

        def show():
            try:
                self.toaster.show_toast(
                    title=title,
                    msg=message,
                    duration=duration,
                    threaded=False,
                    callback_on_click=on_click
                )
            except Exception as e:
                self.logger.error(f"Erreur notification: {e}")

        if threaded:
            threading.Thread(target=show, daemon=True).start()
        else:
            show()

    def notify_new_tickets(self, count: int):
        if count == 1:
            self.notify("🎫 Nouveau ticket", "Un nouveau ticket est arrivé")
        else:
            self.notify(f"🎫 {count} nouveaux tickets", f"{count} nouveaux tickets sont arrivés")

    def notify_urgent_ticket(self, subject: str):
        self.notify("🔴 Ticket URGENT", subject[:100], duration=10)

    def notify_sla_breach(self, ticket_id: int, subject: str):
        self.notify("⚠️ Alerte SLA", f"Ticket #{ticket_id} a dépassé son SLA", duration=10)


notification_service = NotificationService()
