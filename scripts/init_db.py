#!/usr/bin/env python3
"""
Initialize the database and create tables.
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from notifications_manager.database import db_manager

if __name__ == '__main__':
    print("Initializing database...")
    db_manager.init_db()
    print("✓ Database tables created successfully")
