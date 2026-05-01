"""
Base configuration for Notifications Manager
"""
import os


class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/analytics.db')
    
    # ML Models
    MODEL_PATH = os.getenv('MODEL_PATH', 'models/integrated_model.json')
    
    # WebPush
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
    VAPID_PRIVATE_KEY_FILE = os.getenv('VAPID_PRIVATE_KEY_FILE', 'config/vapid_private.pem')
    VAPID_EMAIL = os.getenv('VAPID_EMAIL', 'mailto:admin@yourbank.com')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # API
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100/minute')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Queue
    MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE', 10000))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 100))
