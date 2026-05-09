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
    print("   POST   /api/v1/notifications          - Create notification")
    print("   POST   /api/v1/webpush/subscribe      - Subscribe to WebPush")
    print("   GET    /api/v1/templates              - List templates")
    print("   GET    /api/v1/analytics/summary      - Get analytics")
    print("   GET    /api/v1/models/stats           - ML statistics")
    print()
    print("🌐 Web Pages:")
    print("   http://localhost:8080/                - Landing Page (System Overview)")
    print("   http://localhost:8080/test            - Testing Center (WebPush, Email, SMS, Push)")
    print("   http://localhost:8080/dashboard       - ML Dashboard (Analytics & Stats)")
    print("   http://localhost:8080/templates       - Template Manager (CRUD)")
    print()
    print("💡 Environment: development")
    print("="*70)
    print()
    
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True
    )
