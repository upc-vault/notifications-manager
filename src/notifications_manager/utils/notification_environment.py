"""
Notification Environment Simulator
Simulates real-world banking notification scenarios with varying channel availability and success rates
Models both template selection and channel selection
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from ..algorithms.tug_of_war import NotificationChannel
from ..algorithms.template_bandit import NotificationTemplate


class NotificationEnvironment:
    """
    Simulates the banking notification environment
    Models different scenarios: day/night, weekday/weekend, user preferences, etc.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the environment with realistic success rates
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Base success rates for each channel (banking context)
        # These represent realistic delivery/read rates
        self.base_success_rates = {
            NotificationChannel.PUSH: 0.75,      # High engagement, but app must be installed
            NotificationChannel.SMS: 0.85,        # Very reliable, but costly
            NotificationChannel.EMAIL: 0.50,      # Lower engagement, often ignored
            NotificationChannel.WHATSAPP: 0.80    # High engagement, modern preference
        }
        
        # Time-based availability patterns
        self.current_time = 0
        
    def is_channel_available(self, channel: NotificationChannel, time_of_day: str) -> bool:
        """
        Determine if a channel is available based on context
        
        Args:
            channel: Notification channel
            time_of_day: 'morning', 'afternoon', 'evening', 'night'
            
        Returns:
            True if channel is available (not sleeping)
        """
        # SMS: Always available but expensive (rate-limited)
        if channel == NotificationChannel.SMS:
            return np.random.random() > 0.1  # 90% availability
        
        # Push: Requires app to be active/installed
        if channel == NotificationChannel.PUSH:
            # Lower availability at night
            if time_of_day == 'night':
                return np.random.random() > 0.4  # 60% availability
            return np.random.random() > 0.15  # 85% availability
        
        # Email: Always available but lower engagement
        if channel == NotificationChannel.EMAIL:
            return True  # 100% availability
        
        # WhatsApp: Requires user to have WhatsApp Business enabled
        if channel == NotificationChannel.WHATSAPP:
            # Higher availability during day
            if time_of_day in ['morning', 'afternoon']:
                return np.random.random() > 0.2  # 80% availability
            return np.random.random() > 0.3  # 70% availability
        
        return True
    
    def get_available_channels(self, time_of_day: str) -> List[NotificationChannel]:
        """
        Get list of currently available channels
        
        Args:
            time_of_day: Current time period
            
        Returns:
            List of available notification channels
        """
        available = []
        for channel in NotificationChannel:
            if self.is_channel_available(channel, time_of_day):
                available.append(channel)
        
        # Ensure at least one channel is available
        if not available:
            available = [NotificationChannel.EMAIL]  # Fallback to email
        
        return available
    
    def get_reward(self, channel: NotificationChannel, time_of_day: str, 
                   user_segment: str = 'standard') -> float:
        """
        Simulate reward (success/failure) for sending notification via channel
        
        Args:
            channel: Selected notification channel
            time_of_day: Time period when notification is sent
            user_segment: User segment ('premium', 'standard', 'young')
            
        Returns:
            1.0 for success (notification delivered and engaged), 0.0 for failure
        """
        base_rate = self.base_success_rates[channel]
        
        # Time-based adjustments
        time_modifier = 1.0
        if time_of_day == 'morning':
            time_modifier = 1.1  # Better engagement in morning
        elif time_of_day == 'night':
            time_modifier = 0.8  # Lower engagement at night
        
        # User segment adjustments
        segment_modifier = 1.0
        if user_segment == 'premium':
            # Premium users have better devices and engagement
            if channel == NotificationChannel.PUSH:
                segment_modifier = 1.15
            elif channel == NotificationChannel.WHATSAPP:
                segment_modifier = 1.1
        elif user_segment == 'young':
            # Young users prefer mobile channels
            if channel == NotificationChannel.EMAIL:
                segment_modifier = 0.7
            elif channel == NotificationChannel.WHATSAPP:
                segment_modifier = 1.2
        
        # Calculate final success probability
        success_prob = min(base_rate * time_modifier * segment_modifier, 0.95)
        
        # Add some noise for realism
        success_prob += np.random.normal(0, 0.05)
        success_prob = np.clip(success_prob, 0.0, 1.0)
        
        # Return binary reward
        return 1.0 if np.random.random() < success_prob else 0.0
    
    def get_time_of_day(self, step: int) -> str:
        """
        Get time period based on simulation step
        Simulates a 24-hour cycle
        """
        hour = (step % 24)
        
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def get_user_segment(self, step: int) -> str:
        """
        Simulate different user segments over time
        """
        segments = ['standard', 'premium', 'young']
        # Weight distribution: 60% standard, 25% premium, 15% young
        return np.random.choice(segments, p=[0.6, 0.25, 0.15])


class BankingScenario:
    """
    Represents specific banking notification scenarios
    """
    
    @staticmethod
    def transaction_alert() -> Dict:
        """High priority transaction alert scenario"""
        return {
            'priority': 'high',
            'preferred_channels': [NotificationChannel.PUSH, NotificationChannel.SMS],
            'max_delay': 60,  # seconds
            'description': 'Transaction Alert - Immediate notification required'
        }
    
    @staticmethod
    def account_statement() -> Dict:
        """Monthly account statement notification"""
        return {
            'priority': 'medium',
            'preferred_channels': [NotificationChannel.EMAIL, NotificationChannel.PUSH],
            'max_delay': 3600,  # 1 hour
            'description': 'Account Statement Available'
        }
    
    @staticmethod
    def promotional_offer() -> Dict:
        """Marketing/promotional notification"""
        return {
            'priority': 'low',
            'preferred_channels': [NotificationChannel.EMAIL, NotificationChannel.WHATSAPP],
            'max_delay': 86400,  # 24 hours
            'description': 'Special Offer - New Banking Product'
        }
    
    @staticmethod
    def security_alert() -> Dict:
        """Critical security alert"""
        return {
            'priority': 'critical',
            'preferred_channels': [NotificationChannel.SMS, NotificationChannel.PUSH],
            'max_delay': 30,  # 30 seconds
            'description': 'Security Alert - Suspicious Activity Detected'
        }
