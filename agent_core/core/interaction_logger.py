"""
InteractionLogger — Structured interaction logging with daily rotation.

Logs all agent interactions as JSON Lines (.jsonl), one file per day.
Automatically cleans up old logs beyond MAX_LOG_DAYS.
"""

import os
import json
import glob
from datetime import datetime, timedelta


class InteractionLogger:
    """Logs interactions to daily JSONL files with automatic rotation."""

    MAX_LOG_DAYS = 7

    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "logs"
        )
        os.makedirs(self.log_dir, exist_ok=True)
        self._rotate_old_logs()

    @property
    def current_log_path(self) -> str:
        """Path to today's log file."""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"aurora_{today}.jsonl")

    def log(self, event_type: str, content: str, metadata: dict = None):
        """
        Append a structured log entry.

        Args:
            event_type: One of: user_input, brain_decision, tool_call,
                        tool_result, voice_output, error, thought, plan,
                        memory_recall, gatekeeper
            content: Main content of the event
            metadata: Optional extra data (args, mode, etc.)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "content": content if isinstance(content, str) else str(content),
            "metadata": metadata or {},
        }

        try:
            with open(self.current_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[Logger] Error writing log: {e}")

    def read_day_logs(self, date_str: str = None) -> list:
        """
        Read all log entries for a given day.

        Args:
            date_str: Date in YYYY-MM-DD format. Defaults to today.

        Returns:
            List of log entry dicts.
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        log_path = os.path.join(self.log_dir, f"aurora_{date_str}.jsonl")
        entries = []

        if not os.path.exists(log_path):
            return entries

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except Exception as e:
            print(f"[Logger] Error reading logs: {e}")

        return entries

    def get_available_dates(self) -> list:
        """Returns list of dates (YYYY-MM-DD) that have log files."""
        pattern = os.path.join(self.log_dir, "aurora_*.jsonl")
        files = glob.glob(pattern)
        dates = []
        for f in sorted(files):
            basename = os.path.basename(f)
            # Extract date from aurora_YYYY-MM-DD.jsonl
            date_part = basename.replace("aurora_", "").replace(".jsonl", "")
            dates.append(date_part)
        return dates

    def _rotate_old_logs(self):
        """Delete log files older than MAX_LOG_DAYS."""
        cutoff = datetime.now() - timedelta(days=self.MAX_LOG_DAYS)
        pattern = os.path.join(self.log_dir, "aurora_*.jsonl")

        for filepath in glob.glob(pattern):
            basename = os.path.basename(filepath)
            date_part = basename.replace("aurora_", "").replace(".jsonl", "")
            try:
                file_date = datetime.strptime(date_part, "%Y-%m-%d")
                if file_date < cutoff:
                    os.remove(filepath)
                    print(f"[Logger] Rotated old log: {basename}")
            except (ValueError, OSError) as e:
                print(f"[Logger] Could not rotate {basename}: {e}")
