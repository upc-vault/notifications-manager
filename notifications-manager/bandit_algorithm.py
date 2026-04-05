import numpy as np
import pandas as pd
import pickle
import os
from typing import Dict, List, Tuple
from datetime import datetime


class MultiArmedBandit:
    """
    Multi-Armed Bandit implementation for notification optimization.
    Supports Epsilon-Greedy and UCB (Upper Confidence Bound) strategies.
    """
    
    def __init__(self, strategy='epsilon_greedy', epsilon=0.1, model_path='models/bandit_model.pkl'):
        """
        Initialize the bandit algorithm.
        
        Args:
            strategy: 'epsilon_greedy' or 'ucb'
            epsilon: Exploration rate for epsilon-greedy (0-1)
            model_path: Path to save/load the model
        """
        self.strategy = strategy
        self.epsilon = epsilon
        self.model_path = model_path
        
        # Store rewards and counts per arm (template_id, user_id combination)
        self.arm_rewards = {}  # key: (template_id, user_id), value: total rewards
        self.arm_counts = {}   # key: (template_id, user_id), value: number of pulls
        self.total_pulls = 0
        
        # Load existing model if available
        self.load_model()
    
    def get_arm_key(self, template_id: str, user_id: str) -> str:
        """Create a unique key for template-user combination."""
        return f"{template_id}:{user_id}"
    
    def select_template(self, user_id: str, available_templates: List[str]) -> str:
        """
        Select the best template for a user based on bandit strategy.
        
        Args:
            user_id: User identifier
            available_templates: List of template IDs to choose from
            
        Returns:
            Selected template ID
        """
        if not available_templates:
            raise ValueError("No templates available")
        
        if self.strategy == 'epsilon_greedy':
            return self._epsilon_greedy_select(user_id, available_templates)
        elif self.strategy == 'ucb':
            return self._ucb_select(user_id, available_templates)
        else:
            # Default: random selection
            return np.random.choice(available_templates)
    
    def _epsilon_greedy_select(self, user_id: str, available_templates: List[str]) -> str:
        """Epsilon-Greedy selection strategy."""
        # Exploration: random selection
        if np.random.random() < self.epsilon:
            return np.random.choice(available_templates)
        
        # Exploitation: select best performing template
        best_template = None
        best_avg_reward = -float('inf')
        
        for template_id in available_templates:
            arm_key = self.get_arm_key(template_id, user_id)
            
            if arm_key not in self.arm_counts or self.arm_counts[arm_key] == 0:
                # Unexplored arm - give it high priority
                return template_id
            
            avg_reward = self.arm_rewards[arm_key] / self.arm_counts[arm_key]
            if avg_reward > best_avg_reward:
                best_avg_reward = avg_reward
                best_template = template_id
        
        return best_template if best_template else np.random.choice(available_templates)
    
    def _ucb_select(self, user_id: str, available_templates: List[str]) -> str:
        """Upper Confidence Bound (UCB1) selection strategy."""
        best_template = None
        best_ucb_value = -float('inf')
        
        for template_id in available_templates:
            arm_key = self.get_arm_key(template_id, user_id)
            
            if arm_key not in self.arm_counts or self.arm_counts[arm_key] == 0:
                # Unexplored arm - select immediately
                return template_id
            
            # UCB formula: avg_reward + sqrt(2 * ln(total_pulls) / arm_pulls)
            avg_reward = self.arm_rewards[arm_key] / self.arm_counts[arm_key]
            confidence = np.sqrt(2 * np.log(self.total_pulls + 1) / self.arm_counts[arm_key])
            ucb_value = avg_reward + confidence
            
            if ucb_value > best_ucb_value:
                best_ucb_value = ucb_value
                best_template = template_id
        
        return best_template if best_template else np.random.choice(available_templates)
    
    def update_reward(self, template_id: str, user_id: str, reward: float):
        """
        Update the model with feedback from a notification.
        
        Args:
            template_id: Template that was sent
            user_id: User who received it
            reward: Reward value (1.0 for tap, 0.0 for no tap)
        """
        arm_key = self.get_arm_key(template_id, user_id)
        
        if arm_key not in self.arm_rewards:
            self.arm_rewards[arm_key] = 0.0
            self.arm_counts[arm_key] = 0
        
        self.arm_rewards[arm_key] += reward
        self.arm_counts[arm_key] += 1
        self.total_pulls += 1
    
    def batch_update(self, notifications_df: pd.DataFrame):
        """
        Batch update from historical notification data.
        
        Expected columns: template_id, user_id, was_tapped
        """
        for _, row in notifications_df.iterrows():
            template_id = str(row.get('templateId', row.get('template_id', '')))
            user_id = str(row.get('receiver_id', row.get('user_id', '')))
            was_tapped = row.get('wasTapped', row.get('was_tapped', False))
            
            reward = 1.0 if was_tapped else 0.0
            self.update_reward(template_id, user_id, reward)
    
    def get_statistics(self) -> Dict:
        """Get performance statistics for all arms."""
        stats = {
            'total_pulls': self.total_pulls,
            'unique_arms': len(self.arm_counts),
            'arms': {}
        }
        
        for arm_key, count in self.arm_counts.items():
            if count > 0:
                avg_reward = self.arm_rewards[arm_key] / count
                stats['arms'][arm_key] = {
                    'pulls': count,
                    'total_reward': self.arm_rewards[arm_key],
                    'avg_reward': avg_reward,
                    'ctr': avg_reward  # Click-through rate
                }
        
        return stats
    
    def save_model(self):
        """Save the model to disk."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'strategy': self.strategy,
            'epsilon': self.epsilon,
            'arm_rewards': self.arm_rewards,
            'arm_counts': self.arm_counts,
            'total_pulls': self.total_pulls,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self):
        """Load the model from disk."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.arm_rewards = model_data.get('arm_rewards', {})
                self.arm_counts = model_data.get('arm_counts', {})
                self.total_pulls = model_data.get('total_pulls', 0)
                
                return True
            except Exception as e:
                print(f"Error loading model: {e}")
                return False
        return False
    
    def train_from_parquet(self, file_path: str, batch_size: int = 5000, max_elms: int = 100000):
        """Train the model from historical parquet data."""
        import pyarrow.parquet as pq
        
        counter = 0
        df = pd.DataFrame()
        parquet_file = pq.ParquetFile(file_path)

        for batch in parquet_file.iter_batches(batch_size=batch_size):
            batch_df = batch.to_pandas()
            df = pd.concat([df, batch_df], axis=0)
            counter += batch_size

            if counter >= max_elms:
                break

        df = df.reset_index()
        
        print(f"Training bandit model with {len(df)} records...")
        self.batch_update(df)
        self.save_model()
        print(f"Training complete. Total pulls: {self.total_pulls}, Unique arms: {len(self.arm_counts)}")
        
        return self.get_statistics()
