"""
Notifications Manager - Intelligent notification system for banking
Template selection: Sleeping Multi-Armed Bandit
Channel selection: Tug of War Algorithm
"""

__version__ = '1.0.0'
__author__ = 'UPC PI2 Team'

from .algorithms.template_bandit import SleepingTemplateBandit, NotificationTemplate
from .algorithms.tug_of_war import TugOfWarSelector, NotificationChannel
from .utils.notification_environment import NotificationEnvironment, BankingScenario

__all__ = [
    'SleepingTemplateBandit',
    'NotificationTemplate',
    'TugOfWarSelector', 
    'NotificationChannel',
    'NotificationEnvironment',
    'BankingScenario'
]
