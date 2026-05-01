"""
Production configuration
"""
from .base import Config


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Production paths
    DATABASE_PATH = '/var/lib/notifications/analytics.db'
    MODEL_PATH = '/var/lib/notifications/models/integrated_model.json'
    
    # Strict logging
    LOG_LEVEL = 'WARNING'
    LOG_FILE = '/var/log/notifications/app.log'
    
    # Rate limiting
    API_RATE_LIMIT = '100/minute'
    
    # Specific origins only
    CORS_ORIGINS = ['https://yourbank.com', 'https://app.yourbank.com']
    
    # Redis with password
    REDIS_PASSWORD = None  # Set via environment variable
