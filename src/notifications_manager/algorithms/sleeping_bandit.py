"""
Sleeping Multi-Armed Bandit Algorithm
For intelligent notification channel selection in banking notifications.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class NotificationChannel(Enum):
    """Available notification channels"""
    SMS = "sms"
    PUSH = "push"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


@dataclass
class BanditArm:
    """Represents a notification channel (arm) in the bandit"""
    channel: NotificationChannel
    success_count: int = 0
    failure_count: int = 0
    total_pulls: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate empirical success rate"""
        if self.total_pulls == 0:
            return 0.0
        return self.success_count / self.total_pulls
    
    def update(self, reward: float):
        """Update arm statistics after receiving reward"""
        self.total_pulls += 1
        if reward > 0:
            self.success_count += 1
        else:
            self.failure_count += 1


class SleepingBandit:
    """
    Sleeping Multi-Armed Bandit using UCB1 algorithm
    Handles cases where some arms (channels) are not always available
    """
    
    def __init__(self, channels: List[NotificationChannel], exploration_factor: float = 2.0):
        """
        Initialize the sleeping bandit
        
        Args:
            channels: List of notification channels
            exploration_factor: UCB exploration parameter (typically sqrt(2))
        """
        self.arms = {channel: BanditArm(channel=channel) for channel in channels}
        self.exploration_factor = exploration_factor
        self.total_time = 0
        self.history: List[Dict] = []
        
    def get_ucb_score(self, arm: BanditArm) -> float:
        """
        Calculate Upper Confidence Bound score for an arm
        
        UCB1 formula: mean_reward + c * sqrt(ln(t) / n)
        where t = total time, n = arm pulls, c = exploration factor
        """
        if arm.total_pulls == 0:
            return float('inf')  # Ensure unexplored arms are tried first
        
        mean_reward = arm.success_rate
        exploration_bonus = self.exploration_factor * np.sqrt(
            np.log(self.total_time + 1) / arm.total_pulls
        )
        
        return mean_reward + exploration_bonus
    
    def select_channel(self, available_channels: List[NotificationChannel]) -> NotificationChannel:
        """
        Select the best channel from available ones using UCB1
        
        Args:
            available_channels: List of currently available channels (not sleeping)
            
        Returns:
            Selected notification channel
        """
        if not available_channels:
            raise ValueError("No available channels to select from")
        
        # Calculate UCB scores for available arms only
        available_arms = {channel: self.arms[channel] for channel in available_channels}
        
        best_channel = max(
            available_arms.keys(),
            key=lambda ch: self.get_ucb_score(available_arms[ch])
        )
        
        return best_channel
    
    def update(self, channel: NotificationChannel, reward: float, 
               available_channels: List[NotificationChannel]):
        """
        Update bandit state after observing reward
        
        Args:
            channel: Channel that was used
            reward: Reward received (1 for success, 0 for failure)
            available_channels: Channels that were available at decision time
        """
        self.arms[channel].update(reward)
        self.total_time += 1
        
        # Record history for analysis
        self.history.append({
            'time': self.total_time,
            'channel': channel,
            'reward': reward,
            'available': available_channels,
            'success_rate': self.arms[channel].success_rate
        })
    
    def get_statistics(self) -> Dict:
        """Get current statistics for all arms"""
        stats = {}
        for channel, arm in self.arms.items():
            stats[channel.value] = {
                'total_pulls': arm.total_pulls,
                'success_count': arm.success_count,
                'failure_count': arm.failure_count,
                'success_rate': arm.success_rate,
                'ucb_score': self.get_ucb_score(arm) if arm.total_pulls > 0 else 'inf'
            }
        return stats
    
    def get_best_channel(self) -> Tuple[NotificationChannel, float]:
        """Get the channel with highest empirical success rate"""
        best_arm = max(
            self.arms.values(),
            key=lambda arm: arm.success_rate if arm.total_pulls > 0 else -1
        )
        return best_arm.channel, best_arm.success_rate


class EpsilonGreedyBandit:
    """
    Epsilon-Greedy algorithm for comparison
    Simpler baseline algorithm
    """
    
    def __init__(self, channels: List[NotificationChannel], epsilon: float = 0.1):
        """
        Initialize epsilon-greedy bandit
        
        Args:
            channels: List of notification channels
            epsilon: Exploration probability (0-1)
        """
        self.arms = {channel: BanditArm(channel=channel) for channel in channels}
        self.epsilon = epsilon
        self.total_time = 0
        self.history: List[Dict] = []
        
    def select_channel(self, available_channels: List[NotificationChannel]) -> NotificationChannel:
        """Select channel using epsilon-greedy strategy"""
        if not available_channels:
            raise ValueError("No available channels to select from")
        
        # Exploration: random choice
        if np.random.random() < self.epsilon:
            return np.random.choice(available_channels)
        
        # Exploitation: choose best known arm
        available_arms = {channel: self.arms[channel] for channel in available_channels}
        
        # If no arm has been tried, choose randomly
        if all(arm.total_pulls == 0 for arm in available_arms.values()):
            return np.random.choice(available_channels)
        
        best_channel = max(
            available_arms.keys(),
            key=lambda ch: available_arms[ch].success_rate if available_arms[ch].total_pulls > 0 else -1
        )
        
        return best_channel
    
    def update(self, channel: NotificationChannel, reward: float,
               available_channels: List[NotificationChannel]):
        """Update arm statistics"""
        self.arms[channel].update(reward)
        self.total_time += 1
        
        self.history.append({
            'time': self.total_time,
            'channel': channel,
            'reward': reward,
            'available': available_channels,
            'success_rate': self.arms[channel].success_rate
        })
    
    def get_statistics(self) -> Dict:
        """Get current statistics"""
        stats = {}
        for channel, arm in self.arms.items():
            stats[channel.value] = {
                'total_pulls': arm.total_pulls,
                'success_count': arm.success_count,
                'failure_count': arm.failure_count,
                'success_rate': arm.success_rate
            }
        return stats
    
    def get_best_channel(self) -> Tuple[NotificationChannel, float]:
        """Get best performing channel"""
        best_arm = max(
            self.arms.values(),
            key=lambda arm: arm.success_rate if arm.total_pulls > 0 else -1
        )
        return best_arm.channel, best_arm.success_rate
