"""
AEGIS Log Store
Centralized, indexed log storage with filtering by service, level, trace_id, and keywords.
"""

import time
from typing import List, Optional, Dict, Any
from engine.models.schemas import LogEntry, LogLevel

class LogStore:
    def __init__(self, max_entries: int = 5000):
        self.max_entries = max_entries
        self._logs: List[LogEntry] = []

    def record(self, log_entry: LogEntry):
        self._logs.append(log_entry)
        if len(self._logs) > self.max_entries:
            self._logs.pop(0)

    def query(
        self,
        service_id: Optional[str] = None,
        level: Optional[LogLevel] = None,
        trace_id: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        results = []
        for entry in reversed(self._logs):
            if service_id and entry.service_id != service_id:
                continue
            if level and entry.level != level:
                continue
            if trace_id and entry.trace_id != trace_id:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if keyword and (keyword.lower() not in entry.message.lower()):
                continue
            
            results.append(entry)
            if len(results) >= limit:
                break
        
        return list(reversed(results))

    def get_recent_errors(self, service_id: Optional[str] = None, limit: int = 20) -> List[LogEntry]:
        return self.query(service_id=service_id, level=LogLevel.ERROR, limit=limit)

    def clear(self):
        self._logs.clear()
