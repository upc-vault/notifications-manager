"""
Intelligent Notification Manager - Machine Learning Algorithms
Implements Sleeping Multi-Armed Bandit and Tug of War algorithms
for optimal template and channel selection in banking notifications.
"""

from .sleeping_bandit import SleepingMultiArmedBandit, Template
from .tug_of_war import TugOfWarChannelSelector, Channel

__all__ = [
    'SleepingMultiArmedBandit',
    'Template',
    'TugOfWarChannelSelector',
    'Channel',
]

__version__ = '0.1.0'
