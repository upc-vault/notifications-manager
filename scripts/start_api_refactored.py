"""
Start the Notifications Manager API (Refactored Version)
Uses the new modular blueprint architecture
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from notifications_manager.api.app_refactored import create_app

if __name__ == '__main__':
    app = create_app()
    
    print("\n" + "="*70)
    print("🚀 NOTIFICATIONS MANAGER API (Refactored)")
    print("="*70)
    print()
    print("✨ New Features:")
    print("   • Modular blueprints (webpush, templates, analytics, notifications)")
    print("   • Configuration management (dev/prod/test)")
    print("   • Extracted JavaScript (static/js/)")
    print()
    print("📡 API Endpoints:")
    print("   POST   /api/v1/notifications          - Create notification")
    print("   POST   /api/v1/webpush/subscribe      - Subscribe to WebPush")
    print("   GET    /api/v1/templates              - List templates")
    print("   GET    /api/v1/analytics/summary      - Get analytics")
    print("   GET    /api/v1/models/stats           - ML statistics")
    print()
    print("🌐 Web Pages:")
    print("   http://localhost:5000/                - WebPush Demo")
    print("   http://localhost:5000/dashboard       - ML Dashboard")
    print("   http://localhost:5000/templates       - Template Manager")
    print()
    print("💡 Environment: " + os.getenv('FLASK_ENV', 'development'))
    print("="*70)
    print()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
