"""
Routes package initialization
"""
from .webpush import webpush_bp, init_webpush_routes
from .templates import templates_bp, init_template_routes
from .analytics import analytics_bp, init_analytics_routes
from .notifications import notifications_bp, init_notification_routes
from .push import init_push_routes

__all__ = [
    'webpush_bp',
    'templates_bp',
    'analytics_bp',
    'notifications_bp',
    'init_webpush_routes',
    'init_template_routes',
    'init_analytics_routes',
    'init_notification_routes',
    'init_push_routes'
]
