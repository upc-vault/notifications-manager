"""
Sleeping Multi-Armed Bandit Algorithm
Used to select the optimal notification template based on user engagement.
Templates can be 'sleeping' (unavailable) at certain times or contexts.
"""
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
import time


@dataclass
class Template:
    """Represents a notification template"""
    id: str
    name: str
    content: str
    is_available: bool = True  # Whether template is currently available (not sleeping)
    

class SleepingMultiArmedBandit:
    """
    Sleeping Bandit algorithm for template selection.
    
    Templates can 'sleep' (become unavailable) based on context:
    - Time of day
    - User preferences
    - Template usage limits
    - A/B testing constraints
    """
    
    def __init__(self, templates: List[Template], epsilon: float = 0.1, decay_rate: float = 0.995):
        """
        Initialize the Sleeping Bandit.
        
        Args:
            templates: List of available templates
            epsilon: Exploration rate (0-1)
            decay_rate: Rate at which epsilon decays over time
        """
        self.templates = {t.id: t for t in templates}
        self.template_ids = [t.id for t in templates]
        
        # Track statistics for each template
        self.pulls = {t_id: 0 for t_id in self.template_ids}  # Number of times selected
        self.rewards = {t_id: 0.0 for t_id in self.template_ids}  # Total reward
        self.avg_reward = {t_id: 0.0 for t_id in self.template_ids}  # Average reward
        
        self.epsilon = epsilon
        self.initial_epsilon = epsilon
        self.decay_rate = decay_rate
        self.total_selections = 0
        
    def get_available_templates(self) -> List[str]:
        """Get list of currently available (non-sleeping) template IDs"""
        return [t_id for t_id, t in self.templates.items() if t.is_available]
    
    def select_template(self, context: Optional[Dict] = None) -> str:
        """
        Select a template using epsilon-greedy with sleeping arms.
        
        Args:
            context: Optional context info (time, user preferences, etc.)
            
        Returns:
            Selected template ID
        """
        available = self.get_available_templates()
        
        if not available:
            raise ValueError("No templates available for selection")
        
        # Epsilon-greedy selection among available templates
        if np.random.random() < self.epsilon:
            # Exploration: random selection
            selected = np.random.choice(available)
        else:
            # Exploitation: select best performing available template
            best_template = max(available, key=lambda t_id: self.avg_reward[t_id])
            selected = best_template
        
        self.total_selections += 1
        self.pulls[selected] += 1
        
        # Decay epsilon over time
        self.epsilon *= self.decay_rate
        
        return selected
    
    def update_reward(self, template_id: str, reward: float):
        """
        Update the reward for a template after observing user engagement.
        
        Args:
            template_id: ID of the template that was used
            reward: Reward value (e.g., 1.0 for click, 0.5 for open, 0.0 for ignore)
        """
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        self.rewards[template_id] += reward
        self.avg_reward[template_id] = self.rewards[template_id] / max(1, self.pulls[template_id])
    
    def set_template_availability(self, template_id: str, is_available: bool):
        """Put a template to sleep or wake it up"""
        if template_id in self.templates:
            self.templates[template_id].is_available = is_available
    
    def get_statistics(self) -> Dict:
        """Get current statistics for all templates"""
        return {
            'total_selections': self.total_selections,
            'current_epsilon': self.epsilon,
            'templates': [
                {
                    'id': t_id,
                    'name': self.templates[t_id].name,
                    'pulls': self.pulls[t_id],
                    'avg_reward': self.avg_reward[t_id],
                    'is_available': self.templates[t_id].is_available
                }
                for t_id in self.template_ids
            ]
        }
    
    def get_best_template(self) -> str:
        """Get the template with highest average reward"""
        return max(self.template_ids, key=lambda t_id: self.avg_reward[t_id])
