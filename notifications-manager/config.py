import os
from typing import Optional


class Config:
    """Application configuration."""
    
    # Flask settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///notifications.db')
    
    # Redis settings
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # RabbitMQ settings
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
    RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
    RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', '/')
    
    # Queue names
    NOTIFICATION_QUEUE = 'notifications_queue'
    FEEDBACK_QUEUE = 'feedback_queue'
    
    # Bandit algorithm settings
    BANDIT_STRATEGY = os.getenv('BANDIT_STRATEGY', 'epsilon_greedy')  # or 'ucb'
    BANDIT_EPSILON = float(os.getenv('BANDIT_EPSILON', '0.1'))
    BANDIT_MODEL_PATH = os.getenv('BANDIT_MODEL_PATH', 'models/bandit_model.pkl')
    
    # API settings
    API_VERSION = 'v1'
    API_PREFIX = f'/notifications/{API_VERSION}'
    
    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis connection URL."""
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
    
    @classmethod
    def get_rabbitmq_url(cls) -> str:
        """Get RabbitMQ connection URL."""
        return f"amqp://{cls.RABBITMQ_USER}:{cls.RABBITMQ_PASSWORD}@{cls.RABBITMQ_HOST}:{cls.RABBITMQ_PORT}/{cls.RABBITMQ_VHOST}"