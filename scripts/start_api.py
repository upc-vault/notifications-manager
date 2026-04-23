"""
Start the Notifications Manager API
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from notifications_manager.api.app import create_app

if __name__ == '__main__':
    app = create_app()
    
    print("\n" + "="*70)
    print("🚀 NOTIFICATIONS MANAGER API")
    print("="*70)
    print()
    print("📡 API Endpoints:")
    print("   POST   http://localhost:5000/api/v1/notifications")
    print("   GET    http://localhost:5000/api/v1/queue")
    print("   POST   http://localhost:5000/api/v1/queue/dequeue")
    print("   POST   http://localhost:5000/api/v1/feedback")
    print("   GET    http://localhost:5000/api/v1/models/stats")
    print("   GET    http://localhost:5000/health")
    print()
    print("🤖 ML Models:")
    print("   ✓ Template Selection: Sleeping Multi-Armed Bandit")
    print("   ✓ Channel Selection: Tug of War Algorithm")
    print()
    print("💾 Redis Cache:")
    print("   Host: localhost:6379")
    print("   (Falls back to in-memory if Redis unavailable)")
    print()
    print("="*70)
    print()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
