#!/usr/bin/env python3
"""
Financial Market Intelligence Pipeline

Main entry point for the CLI. This script can be run directly or scheduled via cron.

Usage:
    python run_pipeline.py ingest          # Fetch and process new articles
    python run_pipeline.py digest          # Generate daily digest
    python run_pipeline.py query --topic earnings --days 7
    python run_pipeline.py stats           # Show statistics

Cron example (run daily at 8am):
    0 8 * * * cd /path/to/H-poc && python run_pipeline.py ingest && python run_pipeline.py digest
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.cli import main

if __name__ == "__main__":
    main()
