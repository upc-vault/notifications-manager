"""
Notifications Manager - Sleeping Multi-Armed Bandit
Intelligent notification channel selection for banking
"""

from .sleeping_bandit import (
    SleepingBandit,
    EpsilonGreedyBandit,
    NotificationChannel,
    BanditArm
)

from .notification_environment import (
    NotificationEnvironment,
    BankingScenario
)

__version__ = '0.1.0'
__all__ = [
    'SleepingBandit',
    'EpsilonGreedyBandit',
    'NotificationChannel',
    'BanditArm',
    'NotificationEnvironment',
    'BankingScenario'
]
