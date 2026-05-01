"""
Testing configuration
"""
from .base import Config


class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    
    # Use in-memory/test databases
    DATABASE_PATH = ':memory:'
    MODEL_PATH = 'tests/fixtures/test_model.json'
    
    # Test logging
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = None  # No file logging in tests
    
    # No rate limiting in tests
    API_RATE_LIMIT = None
    
    # Test Redis (or use fakeredis)
    REDIS_HOST = 'localhost'
    REDIS_DB = 15  # Use different DB for tests
