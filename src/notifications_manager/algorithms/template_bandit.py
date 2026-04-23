"""
Template Selection using Sleeping Multi-Armed Bandit
Selects optimal notification template based on user engagement and context
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class NotificationTemplate(Enum):
    """Available notification templates"""
    FORMAL = "formal"  # Professional, detailed
    CONCISE = "concise"  # Brief, to the point
    FRIENDLY = "friendly"  # Casual, personable
    URGENT = "urgent"  # Action-oriented, time-sensitive
    INFORMATIVE = "informative"  # Educational, detailed
    PROMOTIONAL = "promotional"  # Marketing-focused


@dataclass
class TemplateArm:
    """Represents a notification template (arm) in the bandit"""
    template: NotificationTemplate
    success_count: int = 0
    failure_count: int = 0
    total_pulls: int = 0
    engagement_sum: float = 0.0  # Sum of engagement scores
    
    @property
    def success_rate(self) -> float:
        """Calculate empirical success rate"""
        if self.total_pulls == 0:
            return 0.0
        return self.success_count / self.total_pulls
    
    @property
    def avg_engagement(self) -> float:
        """Calculate average engagement score"""
        if self.total_pulls == 0:
            return 0.0
        return self.engagement_sum / self.total_pulls
    
    def update(self, success: bool, engagement: float = 0.5):
        """
        Update arm statistics after receiving feedback
        
        Args:
            success: Whether template resulted in successful notification
            engagement: User engagement score (0-1)
        """
        self.total_pulls += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.engagement_sum += engagement


class SleepingTemplateBandit:
    """
    Sleeping Multi-Armed Bandit for template selection
    Uses UCB1 algorithm to balance exploration and exploitation
    """
    
    def __init__(self, templates: List[NotificationTemplate], 
                 exploration_factor: float = 2.0):
        """
        Initialize the sleeping bandit for templates
        
        Args:
            templates: List of notification templates
            exploration_factor: UCB exploration parameter
        """
        self.arms = {
            template: TemplateArm(template=template) 
            for template in templates
        }
        self.exploration_factor = exploration_factor
        self.total_time = 0
        self.history: List[Dict] = []
        
        # Template characteristics for context matching
        self.template_characteristics = {
            NotificationTemplate.FORMAL: {
                'best_for': ['account_statement', 'policy_update'],
                'user_segments': ['premium', 'standard'],
                'priority': ['medium', 'low']
            },
            NotificationTemplate.CONCISE: {
                'best_for': ['transaction_alert', 'balance_update'],
                'user_segments': ['young', 'premium'],
                'priority': ['high', 'medium']
            },
            NotificationTemplate.FRIENDLY: {
                'best_for': ['promotional', 'tips', 'reminder'],
                'user_segments': ['young', 'standard'],
                'priority': ['low', 'medium']
            },
            NotificationTemplate.URGENT: {
                'best_for': ['security_alert', 'fraud_alert', 'payment_due'],
                'user_segments': ['premium', 'standard', 'young'],
                'priority': ['critical', 'high']
            },
            NotificationTemplate.INFORMATIVE: {
                'best_for': ['product_info', 'feature_announcement'],
                'user_segments': ['premium', 'standard'],
                'priority': ['medium', 'low']
            },
            NotificationTemplate.PROMOTIONAL: {
                'best_for': ['promotional', 'special_offer', 'cross_sell'],
                'user_segments': ['young', 'standard'],
                'priority': ['low']
            }
        }
    
    def get_ucb_score(self, arm: TemplateArm, context_bonus: float = 0.0) -> float:
        """
        Calculate Upper Confidence Bound score for a template
        
        Args:
            arm: Template arm to score
            context_bonus: Additional bonus based on context matching
            
        Returns:
            UCB score (higher is better)
        """
        if arm.total_pulls == 0:
            return float('inf')  # Ensure unexplored templates are tried first
        
        # Base UCB score using engagement rate
        mean_reward = arm.avg_engagement
        exploration_bonus = self.exploration_factor * np.sqrt(
            np.log(self.total_time + 1) / arm.total_pulls
        )
        
        return mean_reward + exploration_bonus + context_bonus
    
    def _calculate_context_bonus(self, template: NotificationTemplate, 
                                 context: Dict) -> float:
        """
        Calculate bonus score based on context matching
        
        Args:
            template: Template to evaluate
            context: Context dictionary with notification_type, user_segment, priority
            
        Returns:
            Bonus score (0-0.3)
        """
        characteristics = self.template_characteristics[template]
        bonus = 0.0
        
        # Match notification type
        notification_type = context.get('notification_type', '')
        if notification_type in characteristics['best_for']:
            bonus += 0.1
        
        # Match user segment
        user_segment = context.get('user_segment', 'standard')
        if user_segment in characteristics['user_segments']:
            bonus += 0.1
        
        # Match priority
        priority = context.get('priority', 'medium')
        if priority in characteristics['priority']:
            bonus += 0.1
        
        return bonus
    
    def select_template(self, context: Dict,
                       available_templates: Optional[List[NotificationTemplate]] = None) -> NotificationTemplate:
        """
        Select the best template using UCB1 with context awareness
        
        Args:
            context: Context dictionary with:
                - notification_type: Type of notification
                - user_segment: User segment
                - priority: Message priority
                - time_of_day: Time period
            available_templates: List of currently available templates
            
        Returns:
            Selected notification template
        """
        if available_templates is None:
            available_templates = list(self.arms.keys())
        
        if not available_templates:
            raise ValueError("No available templates to select from")
        
        # Calculate UCB scores with context bonuses
        scores = {}
        for template in available_templates:
            arm = self.arms[template]
            context_bonus = self._calculate_context_bonus(template, context)
            scores[template] = self.get_ucb_score(arm, context_bonus)
        
        # Select template with highest score
        best_template = max(scores.keys(), key=lambda t: scores[t])
        
        return best_template
    
    def update(self, template: NotificationTemplate, success: bool, 
               engagement: float, context: Dict):
        """
        Update bandit state after observing outcome
        
        Args:
            template: Template that was used
            success: Whether notification was delivered
            engagement: User engagement score (0-1)
                - 0.0-0.3: User ignored
                - 0.3-0.6: User viewed but no action
                - 0.6-0.8: User clicked/interacted
                - 0.8-1.0: User completed desired action
            context: Context used for selection
        """
        self.arms[template].update(success, engagement)
        self.total_time += 1
        
        # Record history
        self.history.append({
            'time': self.total_time,
            'template': template,
            'success': success,
            'engagement': engagement,
            'context': context,
            'success_rate': self.arms[template].success_rate,
            'avg_engagement': self.arms[template].avg_engagement
        })
    
    def get_statistics(self) -> Dict:
        """Get current statistics for all templates"""
        stats = {}
        for template, arm in self.arms.items():
            stats[template.value] = {
                'total_pulls': arm.total_pulls,
                'success_count': arm.success_count,
                'failure_count': arm.failure_count,
                'success_rate': arm.success_rate,
                'avg_engagement': arm.avg_engagement,
                'ucb_score': self.get_ucb_score(arm) if arm.total_pulls > 0 else 'inf'
            }
        return stats
    
    def get_best_template(self) -> Tuple[NotificationTemplate, float]:
        """Get the template with highest average engagement"""
        best_arm = max(
            self.arms.values(),
            key=lambda arm: arm.avg_engagement if arm.total_pulls > 0 else -1
        )
        return best_arm.template, best_arm.avg_engagement
    
    def get_template_recommendations(self, context: Dict, 
                                    top_k: int = 3) -> List[Tuple[NotificationTemplate, float]]:
        """
        Get top-k template recommendations for given context
        
        Args:
            context: Context dictionary
            top_k: Number of recommendations to return
            
        Returns:
            List of (template, score) tuples sorted by score
        """
        scores = []
        for template in self.arms.keys():
            arm = self.arms[template]
            context_bonus = self._calculate_context_bonus(template, context)
            score = self.get_ucb_score(arm, context_bonus)
            if score != float('inf'):  # Exclude unexplored arms
                scores.append((template, score))
        
        # Sort by score and return top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
