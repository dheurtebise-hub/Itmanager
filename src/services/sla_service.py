"""
Service de gestion des SLA
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
from models.database import db

class SLAService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._sla_config: Dict[str, Dict[str, int]] = {}
        self._load_config()

    def _load_config(self):
        try:
            rows = db.fetchall("SELECT * FROM sla_config WHERE is_active = TRUE")
            self._sla_config = {
                row['priority']: {
                    'response_time': row['response_time_minutes'],
                    'resolution_time': row['resolution_time_minutes']
                }
                for row in rows
            }
        except:
            self._sla_config = {
                'urgent': {'response_time': 30, 'resolution_time': 240},
                'high': {'response_time': 60, 'resolution_time': 480},
                'medium': {'response_time': 240, 'resolution_time': 1440},
                'low': {'response_time': 480, 'resolution_time': 2880}
            }

    def get_sla_deadlines(self, ticket: Dict[str, Any]) -> Dict[str, datetime]:
        priority = ticket.get('priority', 'medium')
        sla = self._sla_config.get(priority, self._sla_config.get('medium'))

        received = ticket.get('received_date')

        # Si pas de date, utiliser maintenant
        if not received:
            received = datetime.now()
        elif isinstance(received, str):
            received = datetime.fromisoformat(received)

        # Ensure timezone-naive datetime for SLA calculations
        if hasattr(received, 'tzinfo') and received.tzinfo is not None:
            received = received.replace(tzinfo=None)

        return {
            'response_deadline': received + timedelta(minutes=sla['response_time']),
            'resolution_deadline': received + timedelta(minutes=sla['resolution_time'])
        }

    def check_sla_status(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now()
        deadlines = self.get_sla_deadlines(ticket)
        status = ticket.get('status', 'new')

        result = {'status': 'ok', 'response': {'status': 'ok'}, 'resolution': {'status': 'ok'}}

        if status == 'new':
            remaining = (deadlines['response_deadline'] - now).total_seconds()
            if remaining < 0:
                result['response'] = {'status': 'breach', 'overdue_minutes': abs(remaining) // 60}
                result['status'] = 'breach'
            elif remaining < 600:
                result['response'] = {'status': 'warning', 'remaining_minutes': remaining // 60}
                result['status'] = 'warning'

        if status not in ['resolved', 'closed']:
            remaining = (deadlines['resolution_deadline'] - now).total_seconds()
            if remaining < 0:
                result['resolution'] = {'status': 'breach', 'overdue_minutes': abs(remaining) // 60}
                result['status'] = 'breach'
            elif remaining < 1800:
                result['resolution'] = {'status': 'warning', 'remaining_minutes': remaining // 60}
                if result['status'] != 'breach':
                    result['status'] = 'warning'

        return result

    def get_sla_report(self, days: int = 30) -> Dict[str, Any]:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        total = db.fetchone("SELECT COUNT(*) as count FROM tickets WHERE created_at >= ?", (cutoff,))['count']
        resolved = db.fetchall("SELECT * FROM tickets WHERE resolved_at IS NOT NULL AND created_at >= ?", (cutoff,))

        met_sla = breached_sla = 0
        resolution_times = []

        for ticket in resolved:
            received = datetime.fromisoformat(ticket['received_date'])
            resolved_at = datetime.fromisoformat(ticket['resolved_at'])
            resolution_time = (resolved_at - received).total_seconds() / 60
            resolution_times.append(resolution_time)

            sla = self._sla_config.get(ticket['priority'], self._sla_config.get('medium'))
            if resolution_time <= sla['resolution_time']:
                met_sla += 1
            else:
                breached_sla += 1

        return {
            'period_days': days,
            'total_tickets': total,
            'resolved_tickets': len(resolved),
            'met_sla': met_sla,
            'breached_sla': breached_sla,
            'sla_compliance_rate': round(met_sla / len(resolved) * 100, 1) if resolved else 0,
            'avg_resolution_time_hours': round(sum(resolution_times) / len(resolution_times) / 60, 1) if resolution_times else 0
        }


sla_service = SLAService()
