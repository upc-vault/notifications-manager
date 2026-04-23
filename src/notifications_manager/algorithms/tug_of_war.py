"""
Tug of War (TOW) Algorithm for Dynamic Channel Selection
Selects optimal notification channel based on real-time metrics and preferences
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class NotificationChannel(Enum):
    """Available notification channels"""
    SMS = "sms"
    PUSH = "push"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEBPUSH = "webpush"


@dataclass
class ChannelMetrics:
    """Metrics for a notification channel"""
    channel: NotificationChannel
    availability: float = 1.0  # 0-1, whether channel is available
    cost: float = 0.0  # Normalized cost (0-1)
    latency: float = 0.0  # Expected latency in seconds
    success_rate: float = 0.5  # Historical success rate (0-1)
    user_preference: float = 0.5  # User preference score (0-1)
    priority_weight: float = 1.0  # Priority multiplier for urgent messages
    
    def get_score(self, weights: Dict[str, float]) -> float:
        """
        Calculate weighted score for this channel
        
        Args:
            weights: Dictionary of metric weights
            
        Returns:
            Composite score (higher is better)
        """
        # Positive metrics (higher is better)
        positive = (
            weights.get('availability', 0.3) * self.availability +
            weights.get('success_rate', 0.3) * self.success_rate +
            weights.get('user_preference', 0.2) * self.user_preference +
            weights.get('priority', 0.1) * self.priority_weight
        )
        
        # Negative metrics (lower is better, so invert)
        negative = (
            weights.get('cost', 0.05) * (1 - self.cost) +
            weights.get('latency', 0.05) * (1 - min(self.latency / 10.0, 1.0))
        )
        
        return positive + negative


class TugOfWarSelector:
    """
    Tug of War algorithm for dynamic channel selection
    
    Models channel selection as a competitive process where channels
    "compete" based on their current metrics and historical performance.
    """
    
    def __init__(self, channels: List[NotificationChannel], 
                 alpha: float = 0.1, beta: float = 0.9):
        """
        Initialize TOW selector
        
        Args:
            channels: List of available notification channels
            alpha: Learning rate for updating success rates
            beta: Momentum factor for historical performance
        """
        self.channels = channels
        self.alpha = alpha  # Learning rate
        self.beta = beta  # Momentum factor
        
        # Initialize channel metrics
        self.metrics: Dict[NotificationChannel, ChannelMetrics] = {
            channel: ChannelMetrics(
                channel=channel,
                success_rate=0.5,  # Start with neutral assumption
                cost=self._get_default_cost(channel),
                latency=self._get_default_latency(channel)
            )
            for channel in channels
        }
        
        # History tracking
        self.history: List[Dict] = []
        self.selection_count: Dict[NotificationChannel, int] = {
            ch: 0 for ch in channels
        }
        
    def _get_default_cost(self, channel: NotificationChannel) -> float:
        """Get default normalized cost for channel"""
        costs = {
            NotificationChannel.SMS: 0.9,  # Most expensive
            NotificationChannel.WHATSAPP: 0.3,  # Low cost
            NotificationChannel.PUSH: 0.1,  # Very cheap
            NotificationChannel.EMAIL: 0.05  # Cheapest
        }
        return costs.get(channel, 0.5)
    
    def _get_default_latency(self, channel: NotificationChannel) -> float:
        """Get default latency for channel (in seconds)"""
        latencies = {
            NotificationChannel.PUSH: 0.5,  # Almost instant
            NotificationChannel.SMS: 2.0,  # Few seconds
            NotificationChannel.WHATSAPP: 1.5,  # Quick
            NotificationChannel.EMAIL: 5.0  # Slower delivery
        }
        return latencies.get(channel, 2.0)
    
    def update_channel_metrics(self, channel: NotificationChannel,
                               availability: Optional[float] = None,
                               user_preference: Optional[float] = None,
                               priority_weight: Optional[float] = None):
        """
        Update real-time metrics for a channel
        
        Args:
            channel: Channel to update
            availability: Current availability (0-1)
            user_preference: User preference score (0-1)
            priority_weight: Priority multiplier
        """
        metrics = self.metrics[channel]
        
        if availability is not None:
            metrics.availability = availability
        if user_preference is not None:
            metrics.user_preference = user_preference
        if priority_weight is not None:
            metrics.priority_weight = priority_weight
    
    def select_channel(self, context: Dict, 
                      available_channels: Optional[List[NotificationChannel]] = None) -> NotificationChannel:
        """
        Select best channel using Tug of War algorithm
        
        Args:
            context: Context dictionary with:
                - priority: 'critical', 'high', 'medium', 'low'
                - time_of_day: 'morning', 'afternoon', 'evening', 'night'
                - user_segment: 'premium', 'standard', 'young'
            available_channels: List of currently available channels
            
        Returns:
            Selected notification channel
        """
        if available_channels is None:
            available_channels = self.channels
        
        if not available_channels:
            raise ValueError("No available channels to select from")
        
        # Get priority-based weights
        weights = self._get_priority_weights(context.get('priority', 'medium'))
        
        # Update metrics based on context
        self._update_context_metrics(context)
        
        # Calculate scores for available channels
        scores = {}
        for channel in available_channels:
            metrics = self.metrics[channel]
            if metrics.availability > 0:  # Only consider available channels
                scores[channel] = metrics.get_score(weights)
            else:
                scores[channel] = -float('inf')
        
        # Select channel with highest score (Tug of War winner)
        best_channel = max(scores.keys(), key=lambda ch: scores[ch])
        
        # Track selection
        self.selection_count[best_channel] += 1
        
        return best_channel
    
    def _get_priority_weights(self, priority: str) -> Dict[str, float]:
        """
        Get metric weights based on message priority
        
        Args:
            priority: Message priority level
            
        Returns:
            Dictionary of metric weights
        """
        if priority == 'critical':
            # Critical: prioritize availability, success, minimize latency
            return {
                'availability': 0.4,
                'success_rate': 0.35,
                'latency': 0.15,
                'user_preference': 0.05,
                'cost': 0.025,
                'priority': 0.025
            }
        elif priority == 'high':
            # High: balance success and availability
            return {
                'availability': 0.3,
                'success_rate': 0.35,
                'user_preference': 0.15,
                'latency': 0.1,
                'cost': 0.05,
                'priority': 0.05
            }
        elif priority == 'medium':
            # Medium: consider user preference and cost
            return {
                'success_rate': 0.3,
                'availability': 0.25,
                'user_preference': 0.25,
                'cost': 0.1,
                'latency': 0.05,
                'priority': 0.05
            }
        else:  # low
            # Low: optimize for cost and user preference
            return {
                'user_preference': 0.3,
                'cost': 0.25,
                'success_rate': 0.25,
                'availability': 0.15,
                'latency': 0.025,
                'priority': 0.025
            }
    
    def _update_context_metrics(self, context: Dict):
        """Update channel metrics based on current context"""
        time_of_day = context.get('time_of_day', 'afternoon')
        user_segment = context.get('user_segment', 'standard')
        
        # Time-based availability adjustments
        if time_of_day == 'night':
            # Lower push notification availability at night
            self.metrics[NotificationChannel.PUSH].availability = 0.6
        else:
            self.metrics[NotificationChannel.PUSH].availability = 0.9
        
        # User segment preferences
        if user_segment == 'premium':
            # Premium users prefer push and WhatsApp
            self.update_channel_metrics(NotificationChannel.PUSH, user_preference=0.8)
            self.update_channel_metrics(NotificationChannel.WHATSAPP, user_preference=0.85)
            self.update_channel_metrics(NotificationChannel.EMAIL, user_preference=0.6)
        elif user_segment == 'young':
            # Young users prefer WhatsApp and push
            self.update_channel_metrics(NotificationChannel.WHATSAPP, user_preference=0.9)
            self.update_channel_metrics(NotificationChannel.PUSH, user_preference=0.8)
            self.update_channel_metrics(NotificationChannel.EMAIL, user_preference=0.3)
        else:  # standard
            # Standard users have balanced preferences
            self.update_channel_metrics(NotificationChannel.SMS, user_preference=0.7)
            self.update_channel_metrics(NotificationChannel.EMAIL, user_preference=0.6)
    
    def update_success_rate(self, channel: NotificationChannel, success: bool):
        """
        Update channel success rate based on outcome
        
        Uses exponential moving average with momentum:
        new_rate = beta * old_rate + (1 - beta) * current_result
        
        Args:
            channel: Channel that was used
            success: Whether the notification was successful
        """
        current_rate = self.metrics[channel].success_rate
        observed_rate = 1.0 if success else 0.0
        
        # Exponential moving average
        new_rate = self.beta * current_rate + (1 - self.beta) * observed_rate
        
        self.metrics[channel].success_rate = new_rate
        
        # Record history
        self.history.append({
            'channel': channel,
            'success': success,
            'new_rate': new_rate
        })
    
    def get_statistics(self) -> Dict:
        """Get current statistics for all channels"""
        stats = {}
        total_selections = sum(self.selection_count.values())
        
        for channel, metrics in self.metrics.items():
            stats[channel.value] = {
                'success_rate': metrics.success_rate,
                'availability': metrics.availability,
                'cost': metrics.cost,
                'latency': metrics.latency,
                'user_preference': metrics.user_preference,
                'selections': self.selection_count[channel],
                'selection_rate': (
                    self.selection_count[channel] / total_selections 
                    if total_selections > 0 else 0
                )
            }
        
        return stats
    
    def get_best_channel_by_context(self, priority: str) -> Tuple[NotificationChannel, float]:
        """
        Get best channel for a given priority without selection
        
        Args:
            priority: Message priority
            
        Returns:
            Tuple of (best_channel, score)
        """
        weights = self._get_priority_weights(priority)
        
        best_channel = None
        best_score = -float('inf')
        
        for channel, metrics in self.metrics.items():
            if metrics.availability > 0:
                score = metrics.get_score(weights)
                if score > best_score:
                    best_score = score
                    best_channel = channel
        
        return best_channel, best_score


class AdaptiveTOW(TugOfWarSelector):
    """
    Adaptive Tug of War with dynamic weight adjustment
    Learns optimal weights based on historical performance
    """
    
    def __init__(self, channels: List[NotificationChannel],
                 alpha: float = 0.1, beta: float = 0.9, gamma: float = 0.05):
        """
        Initialize adaptive TOW
        
        Args:
            channels: Available channels
            alpha: Learning rate for success rates
            beta: Momentum factor
            gamma: Weight adaptation rate
        """
        super().__init__(channels, alpha, beta)
        self.gamma = gamma  # Weight learning rate
        
        # Adaptive weights for each priority
        self.adaptive_weights: Dict[str, Dict[str, float]] = {
            priority: self._get_priority_weights(priority)
            for priority in ['critical', 'high', 'medium', 'low']
        }
    
    def adapt_weights(self, priority: str, channel: NotificationChannel, 
                     success: bool, reward: float):
        """
        Adapt weights based on outcome
        
        Args:
            priority: Priority level used
            channel: Channel selected
            success: Whether notification succeeded
            reward: Reward signal (-1 to 1)
        """
        weights = self.adaptive_weights[priority]
        metrics = self.metrics[channel]
        
        # Increase weight of metrics that contributed to success
        if success:
            # Reward high-performing metrics
            if metrics.success_rate > 0.7:
                weights['success_rate'] *= (1 + self.gamma)
            if metrics.availability > 0.8:
                weights['availability'] *= (1 + self.gamma)
        else:
            # Penalize metrics that didn't help
            if metrics.success_rate < 0.5:
                weights['success_rate'] *= (1 - self.gamma)
        
        # Normalize weights to sum to 1
        total = sum(weights.values())
        for key in weights:
            weights[key] /= total
