"""
User Profile System for Intelligent Notification Manager
Handles user segmentation, preferences, and behavioral patterns.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import numpy as np


class BankingTier(Enum):
    """Banking customer tiers"""
    NATURAL = "natural"          # Regular customers
    PRIME = "prime"              # Mid-tier customers
    PRIVATE = "private"          # High net worth
    PATRIMONIAL = "patrimonial"  # Ultra high net worth


class PreferredTime(Enum):
    """Preferred notification times"""
    MORNING = "morning"      # 6-12
    AFTERNOON = "afternoon"  # 12-18
    EVENING = "evening"      # 18-22
    NIGHT = "night"          # 22-6


@dataclass
class UserPreferences:
    """User notification preferences"""
    preferred_channels: List[str] = field(default_factory=lambda: ["push"])
    preferred_times: List[PreferredTime] = field(default_factory=lambda: [PreferredTime.MORNING])
    language: str = "es"  # Spanish by default
    frequency_limit: int = 5  # Max notifications per day
    marketing_opt_in: bool = True
    push_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = True
    whatsapp_enabled: bool = True


@dataclass
class UserBehavior:
    """Historical user behavior patterns"""
    template_engagement: Dict[str, float] = field(default_factory=dict)
    channel_engagement: Dict[str, float] = field(default_factory=dict)
    avg_response_time: float = 300.0  # seconds
    total_notifications: int = 0
    opened_notifications: int = 0
    clicked_notifications: int = 0
    ignored_notifications: int = 0
    
    @property
    def open_rate(self) -> float:
        """Calculate open rate"""
        if self.total_notifications == 0:
            return 0.0
        return self.opened_notifications / self.total_notifications
    
    @property
    def click_rate(self) -> float:
        """Calculate click-through rate"""
        if self.total_notifications == 0:
            return 0.0
        return self.clicked_notifications / self.total_notifications


@dataclass
class UserProfile:
    """Complete user profile for personalized notifications"""
    user_id: str
    name: str
    age: int
    banking_tier: BankingTier
    preferences: UserPreferences = field(default_factory=UserPreferences)
    behavior: UserBehavior = field(default_factory=UserBehavior)
    
    # Demographics
    income_level: str = "medium"  # low, medium, high
    digital_adoption: float = 0.7  # 0-1, how tech-savvy
    risk_tolerance: str = "medium"  # low, medium, high
    
    # Context
    timezone: str = "America/Lima"
    device_type: str = "mobile"  # mobile, desktop, tablet
    
    def get_channel_affinity(self, channel: str) -> float:
        """
        Get user's affinity for a specific channel based on preferences and behavior.
        
        Returns value between 0 and 1
        """
        # Base affinity from preferences
        affinity = 0.5
        
        # Check if channel is in preferred channels
        if channel in self.preferences.preferred_channels:
            affinity += 0.3
        
        # Check if channel is enabled
        channel_enabled = {
            'push': self.preferences.push_enabled,
            'email': self.preferences.email_enabled,
            'sms': self.preferences.sms_enabled,
            'whatsapp': self.preferences.whatsapp_enabled,
            'webpush': self.preferences.push_enabled,
        }
        
        if not channel_enabled.get(channel, False):
            return 0.0  # Channel disabled
        
        # Add behavioral component
        if channel in self.behavior.channel_engagement:
            affinity += self.behavior.channel_engagement[channel] * 0.2
        
        # Adjust based on banking tier
        tier_adjustments = {
            BankingTier.NATURAL: {'email': -0.1, 'whatsapp': +0.1},
            BankingTier.PRIME: {'push': +0.1, 'email': +0.1},
            BankingTier.PRIVATE: {'whatsapp': +0.2, 'email': +0.1},
            BankingTier.PATRIMONIAL: {'whatsapp': +0.3, 'sms': +0.1},
        }
        
        tier_adj = tier_adjustments.get(self.banking_tier, {}).get(channel, 0)
        affinity += tier_adj
        
        # Digital adoption affects tech channels
        if channel in ['push', 'webpush', 'whatsapp']:
            affinity += (self.digital_adoption - 0.5) * 0.2
        
        return np.clip(affinity, 0.0, 1.0)
    
    def get_template_affinity(self, template_id: str) -> float:
        """
        Get user's affinity for a specific template type.
        
        Returns value between 0 and 1
        """
        affinity = 0.5
        
        # Historical engagement
        if template_id in self.behavior.template_engagement:
            affinity += self.behavior.template_engagement[template_id] * 0.3
        
        # Tier-based preferences
        if self.banking_tier in [BankingTier.PRIVATE, BankingTier.PATRIMONIAL]:
            # High-value customers prefer security and urgent notifications
            if 'security' in template_id or 'urgent' in template_id:
                affinity += 0.2
            if 'promo' in template_id:
                affinity -= 0.2 if not self.preferences.marketing_opt_in else 0.0
        
        # Age-based preferences
        if self.age < 30:
            # Younger users more receptive to promos
            if 'promo' in template_id:
                affinity += 0.1
        elif self.age > 60:
            # Older users prefer informational content
            if 'info' in template_id:
                affinity += 0.15
        
        return np.clip(affinity, 0.0, 1.0)
    
    def update_behavior(self, template_id: str, channel: str, 
                       opened: bool, clicked: bool):
        """Update user behavior based on notification interaction"""
        self.behavior.total_notifications += 1
        
        if opened:
            self.behavior.opened_notifications += 1
        if clicked:
            self.behavior.clicked_notifications += 1
        if not opened and not clicked:
            self.behavior.ignored_notifications += 1
        
        # Update template engagement
        if template_id not in self.behavior.template_engagement:
            self.behavior.template_engagement[template_id] = 0.5
        
        engagement_change = 0.1 if clicked else (0.05 if opened else -0.05)
        self.behavior.template_engagement[template_id] = np.clip(
            self.behavior.template_engagement[template_id] + engagement_change,
            0.0, 1.0
        )
        
        # Update channel engagement
        if channel not in self.behavior.channel_engagement:
            self.behavior.channel_engagement[channel] = 0.5
        
        self.behavior.channel_engagement[channel] = np.clip(
            self.behavior.channel_engagement[channel] + engagement_change,
            0.0, 1.0
        )


def create_sample_users() -> List[UserProfile]:
    """Create a diverse set of sample users for training"""
    users = []
    
    # User 1: Young professional, tech-savvy
    users.append(UserProfile(
        user_id="user_001",
        name="Carlos Mendez",
        age=28,
        banking_tier=BankingTier.PRIME,
        preferences=UserPreferences(
            preferred_channels=["push", "whatsapp"],
            preferred_times=[PreferredTime.MORNING, PreferredTime.EVENING],
            marketing_opt_in=True,
        ),
        income_level="medium",
        digital_adoption=0.9,
        device_type="mobile"
    ))
    
    # User 2: Middle-aged executive, private banking
    users.append(UserProfile(
        user_id="user_002",
        name="Maria Rodriguez",
        age=45,
        banking_tier=BankingTier.PRIVATE,
        preferences=UserPreferences(
            preferred_channels=["email", "whatsapp"],
            preferred_times=[PreferredTime.AFTERNOON],
            marketing_opt_in=False,
        ),
        income_level="high",
        digital_adoption=0.7,
        device_type="desktop"
    ))
    
    # User 3: Senior citizen, conservative
    users.append(UserProfile(
        user_id="user_003",
        name="Roberto Silva",
        age=68,
        banking_tier=BankingTier.PATRIMONIAL,
        preferences=UserPreferences(
            preferred_channels=["email", "sms"],
            preferred_times=[PreferredTime.MORNING],
            marketing_opt_in=False,
            whatsapp_enabled=False,
        ),
        income_level="high",
        digital_adoption=0.4,
        device_type="desktop"
    ))
    
    # User 4: Young student, natural banking
    users.append(UserProfile(
        user_id="user_004",
        name="Ana Jimenez",
        age=22,
        banking_tier=BankingTier.NATURAL,
        preferences=UserPreferences(
            preferred_channels=["push", "whatsapp"],
            preferred_times=[PreferredTime.EVENING, PreferredTime.NIGHT],
            marketing_opt_in=True,
        ),
        income_level="low",
        digital_adoption=0.95,
        device_type="mobile"
    ))
    
    # User 5: Mid-career professional
    users.append(UserProfile(
        user_id="user_005",
        name="Luis Torres",
        age=38,
        banking_tier=BankingTier.PRIME,
        preferences=UserPreferences(
            preferred_channels=["push", "email"],
            preferred_times=[PreferredTime.MORNING, PreferredTime.AFTERNOON],
            marketing_opt_in=True,
        ),
        income_level="medium",
        digital_adoption=0.75,
        device_type="mobile"
    ))
    
    return users
