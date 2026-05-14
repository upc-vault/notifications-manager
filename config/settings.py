"""
Application settings and configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Application
APP_NAME = os.getenv("APP_NAME", "Intelligent Notification Manager")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
PORT = int(os.getenv("PORT", 8080))

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", 3600))  # 1 hour default

# ML Models Configuration
ML_MODELS_PATH = BASE_DIR / "data" / "training"
ML_BANDIT_EPSILON = float(os.getenv("ML_BANDIT_EPSILON", 0.1))
ML_BANDIT_DECAY = float(os.getenv("ML_BANDIT_DECAY", 0.995))
ML_TOW_PULL_STRENGTH = float(os.getenv("ML_TOW_PULL_STRENGTH", 0.05))
ML_TOW_POSITION_WEIGHT = float(os.getenv("ML_TOW_POSITION_WEIGHT", 0.6))
ML_TOW_PERFORMANCE_WEIGHT = float(os.getenv("ML_TOW_PERFORMANCE_WEIGHT", 0.4))

# Priority Queue Configuration
PRIORITY_QUEUE_MAX_SIZE = int(os.getenv("PRIORITY_QUEUE_MAX_SIZE", 10000))
PRIORITY_LEVELS = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4
}

# Rate Limiting
RATE_LIMIT_PER_USER_DAILY = int(os.getenv("RATE_LIMIT_PER_USER_DAILY", 50))
RATE_LIMIT_PER_USER_HOURLY = int(os.getenv("RATE_LIMIT_PER_USER_HOURLY", 10))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Web Push Configuration
def load_vapid_keys():
    """Load VAPID keys from JSON file"""
    vapid_keys_file = BASE_DIR / "config" / "vapid_keys.json"
    if vapid_keys_file.exists():
        import json
        with open(vapid_keys_file, 'r') as f:
            keys = json.load(f)
            return keys.get('private_key'), keys.get('public_key')
    return None, None

_vapid_private, _vapid_public = load_vapid_keys()

WEBPUSH_VAPID_PRIVATE_KEY = os.getenv("WEBPUSH_VAPID_PRIVATE_KEY", _vapid_private)
WEBPUSH_VAPID_PUBLIC_KEY = os.getenv("WEBPUSH_VAPID_PUBLIC_KEY", _vapid_public)
WEBPUSH_VAPID_ADMIN_EMAIL = os.getenv("WEBPUSH_VAPID_ADMIN_EMAIL", "admin@bbva-notifications.com")
LOG_FILE = BASE_DIR / "logs" / "app.log"

# WhatsApp Business API Configuration
# Get your credentials from: https://developers.facebook.com/apps
# WhatsApp > API Setup > Phone Number ID and Access Token
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", None)
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", None)
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v18.0")
# Set to False to use real API, True to use mock mode
WHATSAPP_MOCK_MODE = os.getenv("WHATSAPP_MOCK_MODE", "true").lower() == "true"

# Firebase Push Notification Configuration
# Download service account JSON from Firebase Console > Project Settings > Service Accounts
# Path to Firebase service account JSON file
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", 
                                          str(BASE_DIR / "config" / "firebase-service-account.json"))

# Database Configuration
DATABASE_PATH = BASE_DIR / "data" / "notifications.db"
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# JWT Configuration  
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-2026")
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 86400))  # 24 hours
JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))  # 30 days

# API Configuration
API_PREFIX = "/api/v1"
