"""Data models for the notification manager system"""

from .user_profile import (
    UserProfile,
    UserPreferences,
    UserBehavior,
    BankingTier,
    PreferredTime,
    create_sample_users
)

__all__ = [
    'UserProfile',
    'UserPreferences',
    'UserBehavior',
    'BankingTier',
    'PreferredTime',
    'create_sample_users',
]
