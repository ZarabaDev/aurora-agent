#!/usr/bin/env python3
"""
Aurora Sleep Routine — Run nightly to consolidate memories.

Usage:
    python scripts/run_sleep.py              # Consolidate yesterday
    python scripts/run_sleep.py 2026-02-09   # Consolidate specific date

Cron example (run daily at 3 AM):
    0 3 * * * cd /home/zarabatana/Documentos/aurora && venv/bin/python scripts/run_sleep.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from agent_core.core.sleep_consolidator import SleepConsolidator


def main():
    date_str = None
    if len(sys.argv) > 1:
        date_str = sys.argv[1]

    print("=" * 50)
    print("🌙 Aurora Sleep Routine — Memory Consolidation")
    print("=" * 50)

    consolidator = SleepConsolidator()
    result = consolidator.consolidate(date_str)

    print()
    print("📊 Results:")
    print(f"   Date:            {result['date']}")
    print(f"   Insights saved:  {result['insights_saved']}")
    print(f"   Summary:         {result.get('summary', 'N/A')}")

    if "total_logs" in result:
        print(f"   Total log entries: {result['total_logs']}")

    print()
    print("💤 Sleep complete. Good night, Aurora.")


if __name__ == "__main__":
    main()
