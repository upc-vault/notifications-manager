"""
Notification Decision Service
Uses trained ML models to decide template, channel, and priority
"""

import json
import os
from typing import Dict, Tuple
from dataclasses import dataclass
from enum import Enum

from ..algorithms.template_bandit import SleepingTemplateBandit, NotificationTemplate
from ..algorithms.tug_of_war import TugOfWarSelector, NotificationChannel


class NotificationPriority(Enum):
    """Notification priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class NotificationDecision:
    """Result of notification decision"""
    template: NotificationTemplate
    channel: NotificationChannel
    priority: NotificationPriority
    template_score: float
    channel_score: float
    estimated_success_rate: float
    estimated_engagement: float


class NotificationDecisionService:
    """
    Service that uses trained ML models to make notification decisions
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the decision service with trained models
        
        Args:
            model_path: Path to trained model JSON file
        """
        if model_path is None:
            # Default to integrated model
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            model_path = os.path.join(base_path, 'models', 'integrated_model.json')
        
        # Load trained model statistics
        self.model_stats = self._load_model_stats(model_path)
        
        # Initialize algorithms
        self.template_bandit = SleepingTemplateBandit(
            templates=list(NotificationTemplate),
            exploration_factor=2.0
        )
        
        self.channel_selector = TugOfWarSelector(
            channels=list(NotificationChannel),
            alpha=0.1,
            beta=0.9
        )
        
        # Initialize with trained statistics
        self._initialize_from_trained_model()
    
    def _load_model_stats(self, model_path: str) -> Dict:
        """Load trained model statistics from JSON"""
        try:
            with open(model_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Trained model not found at {model_path}. "
                "Please run training first: python scripts/train_integrated.py"
            )
    
    def _initialize_from_trained_model(self):
        """Initialize algorithms with trained statistics"""
        # Initialize template bandit with trained engagement rates
        template_stats = self.model_stats.get('template_statistics', {})
        for template_name, stats in template_stats.items():
            try:
                template = NotificationTemplate[template_name.upper()]
                arm = self.template_bandit.arms[template]
                
                # Set trained statistics
                arm.total_pulls = stats['total_pulls']
                arm.success_count = stats['success_count']
                arm.failure_count = stats['failure_count']
                arm.engagement_sum = stats['avg_engagement'] * stats['total_pulls']
            except (KeyError, AttributeError):
                continue
        
        # Initialize channel selector with trained success rates
        channel_stats = self.model_stats.get('channel_statistics', {})
        for channel_name, stats in channel_stats.items():
            try:
                channel = NotificationChannel[channel_name.upper()]
                metrics = self.channel_selector.metrics[channel]
                
                # Set trained metrics
                metrics.success_rate = stats['success_rate']
                metrics.availability = stats.get('availability', 1.0)
                metrics.cost = stats.get('cost', 0.5)
                metrics.latency = stats.get('latency', 2.0)
                metrics.user_preference = stats.get('user_preference', 0.5)
                
                # Set selection count
                self.channel_selector.selection_count[channel] = stats.get('selections', 0)
            except (KeyError, AttributeError):
                continue
    
    def decide_notification(self, 
                           notification_type: str,
                           user_segment: str,
                           priority_hint: str = None,
                           time_of_day: str = 'afternoon',
                           available_channels: list = None) -> NotificationDecision:
        """
        Make complete notification decision using ML models
        
        Args:
            notification_type: Type of notification (transaction_alert, security_alert, etc.)
            user_segment: User segment (premium, standard, young)
            priority_hint: Optional priority hint (critical, high, medium, low)
            time_of_day: Time period (morning, afternoon, evening, night)
            available_channels: List of available channels (None = all available)
            
        Returns:
            NotificationDecision with template, channel, and priority
        """
        # Determine priority based on notification type and hint
        priority = self._determine_priority(notification_type, priority_hint)
        
        # Create context for ML models
        context = {
            'notification_type': notification_type,
            'user_segment': user_segment,
            'priority': priority.name.lower(),
            'time_of_day': time_of_day
        }
        
        # STEP 1: Select template using Sleeping Multi-Armed Bandit
        selected_template = self.template_bandit.select_template(context)
        
        # Get template statistics
        template_arm = self.template_bandit.arms[selected_template]
        template_score = template_arm.avg_engagement
        
        # STEP 2: Select channel using Tug of War
        if available_channels is None:
            available_channels = list(NotificationChannel)
        
        selected_channel = self.channel_selector.select_channel(
            context,
            available_channels
        )
        
        # Get channel statistics
        channel_metrics = self.channel_selector.metrics[selected_channel]
        channel_score = channel_metrics.success_rate
        
        # Create decision
        decision = NotificationDecision(
            template=selected_template,
            channel=selected_channel,
            priority=priority,
            template_score=template_score,
            channel_score=channel_score,
            estimated_success_rate=channel_score,
            estimated_engagement=template_score
        )
        
        return decision
    
    def _determine_priority(self, 
                           notification_type: str, 
                           priority_hint: str = None) -> NotificationPriority:
        """
        Determine notification priority based on type and hint
        
        Args:
            notification_type: Type of notification
            priority_hint: Optional explicit priority
            
        Returns:
            NotificationPriority enum
        """
        # If explicit priority provided, use it
        if priority_hint:
            priority_map = {
                'critical': NotificationPriority.CRITICAL,
                'high': NotificationPriority.HIGH,
                'medium': NotificationPriority.MEDIUM,
                'low': NotificationPriority.LOW
            }
            return priority_map.get(priority_hint.lower(), NotificationPriority.MEDIUM)
        
        # Otherwise, infer from notification type
        priority_rules = {
            'security_alert': NotificationPriority.CRITICAL,
            'fraud_alert': NotificationPriority.CRITICAL,
            'transaction_alert': NotificationPriority.HIGH,
            'payment_due': NotificationPriority.HIGH,
            'balance_update': NotificationPriority.MEDIUM,
            'account_statement': NotificationPriority.MEDIUM,
            'promotional': NotificationPriority.LOW,
            'feature_announcement': NotificationPriority.LOW,
        }
        
        return priority_rules.get(notification_type, NotificationPriority.MEDIUM)
    
    def update_feedback(self, 
                       template: str,
                       channel: str, 
                       success: bool, 
                       engagement: float = 0.5):
        """
        Update models with feedback from sent notification
        
        Args:
            template: Template that was used
            channel: Channel that was used
            success: Whether notification was successfully delivered
            engagement: User engagement score (0-1)
        """
        try:
            template_enum = NotificationTemplate[template.upper()]
            channel_enum = NotificationChannel[channel.upper()]
            
            # Update template bandit
            context = {}  # Simplified for feedback
            self.template_bandit.update(template_enum, success, engagement, context)
            
            # Update channel selector
            self.channel_selector.update_success_rate(channel_enum, success)
            
        except KeyError:
            pass  # Invalid template or channel name
    
    def get_model_statistics(self) -> Dict:
        """Get current model statistics"""
        return {
            'template_statistics': self.template_bandit.get_statistics(),
            'channel_statistics': self.channel_selector.get_statistics()
        }
