"""
Development configuration
"""
from .base import Config


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    
    # Use local files
    DATABASE_PATH = 'data/analytics.db'
    MODEL_PATH = 'models/integrated_model.json'
    
    # Relaxed logging
    LOG_LEVEL = 'DEBUG'
    
    # No rate limiting in dev
    API_RATE_LIMIT = '1000/minute'
    
    # Allow all origins in dev
    CORS_ORIGINS = ['*']
