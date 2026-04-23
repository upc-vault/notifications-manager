"""
Integrated Training: Template Selection (Bandit) + Channel Selection (TOW)
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict
import json
from datetime import datetime

from template_bandit import SleepingTemplateBandit, NotificationTemplate
from tug_of_war import TugOfWarSelector, NotificationChannel
from notification_environment import NotificationEnvironment, BankingScenario


class IntegratedTrainer:
    """Trains both template bandit and TOW channel selector"""
    
    def __init__(self, num_episodes: int = 10000, seed: int = 42):
        """
        Initialize integrated trainer
        
        Args:
            num_episodes: Number of training episodes
            seed: Random seed for reproducibility
        """
        self.num_episodes = num_episodes
        self.seed = seed
        self.environment = NotificationEnvironment(seed=seed)
        
        # Initialize template bandit (Sleeping Multi-Armed Bandit)
        templates = list(NotificationTemplate)
        self.template_bandit = SleepingTemplateBandit(
            templates=templates,
            exploration_factor=2.0
        )
        
        # Initialize channel selector (Tug of War)
        channels = list(NotificationChannel)
        self.channel_selector = TugOfWarSelector(
            channels=channels,
            alpha=0.1,  # Learning rate
            beta=0.9    # Momentum
        )
        
        # Training metrics
        self.metrics = {
            'template_engagement': [],
            'channel_success': [],
            'combined_reward': [],
            'cumulative_reward': []
        }
        
        # Notification type distribution
        self.notification_types = [
            'transaction_alert', 'security_alert', 'account_statement',
            'balance_update', 'promotional', 'payment_due', 'feature_announcement'
        ]
        
    def train_episode(self, episode: int):
        """
        Run a single training episode
        
        Args:
            episode: Current episode number
        """
        # Get context for this episode
        time_of_day = self.environment.get_time_of_day(episode)
        user_segment = self.environment.get_user_segment(episode)
        
        # Select notification type
        notification_type = np.random.choice(self.notification_types)
        
        # Determine priority based on notification type
        priority_map = {
            'security_alert': 'critical',
            'transaction_alert': 'high',
            'payment_due': 'high',
            'balance_update': 'medium',
            'account_statement': 'medium',
            'feature_announcement': 'low',
            'promotional': 'low'
        }
        priority = priority_map.get(notification_type, 'medium')
        
        # Create context
        context = {
            'notification_type': notification_type,
            'user_segment': user_segment,
            'priority': priority,
            'time_of_day': time_of_day
        }
        
        # STEP 1: Select template using Sleeping Multi-Armed Bandit
        selected_template = self.template_bandit.select_template(context)
        
        # STEP 2: Select channel using Tug of War
        available_channels = self.environment.get_available_channels(time_of_day)
        selected_channel = self.channel_selector.select_channel(
            context,
            available_channels
        )
        
        # STEP 3: Simulate sending notification
        # Channel success depends on channel choice and context
        channel_success_raw = self.environment.get_reward(
            selected_channel, time_of_day, user_segment
        )
        channel_success = channel_success_raw > 0
        
        # Engagement depends on template choice and user segment
        template_engagement = self._calculate_engagement(
            selected_template, notification_type, user_segment, channel_success
        )
        
        # Combined reward (both channel succeeded and good engagement)
        combined_reward = channel_success_raw * template_engagement
        
        # STEP 4: Update both algorithms
        self.template_bandit.update(
            selected_template, channel_success, template_engagement, context
        )
        
        self.channel_selector.update_success_rate(
            selected_channel, channel_success
        )
        
        # Track metrics
        self.metrics['template_engagement'].append(template_engagement)
        self.metrics['channel_success'].append(1.0 if channel_success else 0.0)
        self.metrics['combined_reward'].append(combined_reward)
        
        cumulative = (
            self.metrics['cumulative_reward'][-1] + combined_reward
            if self.metrics['cumulative_reward']
            else combined_reward
        )
        self.metrics['cumulative_reward'].append(cumulative)
    
    def _calculate_engagement(self, template: NotificationTemplate, 
                             notification_type: str, user_segment: str,
                             delivered: bool) -> float:
        """
        Calculate user engagement score based on template and context
        
        Returns:
            Engagement score (0-1)
        """
        if not delivered:
            return 0.0  # No engagement if not delivered
        
        # Base engagement by template-notification type match
        base_engagement = {
            ('URGENT', 'security_alert'): 0.95,
            ('URGENT', 'payment_due'): 0.90,
            ('CONCISE', 'transaction_alert'): 0.85,
            ('CONCISE', 'balance_update'): 0.80,
            ('FORMAL', 'account_statement'): 0.75,
            ('INFORMATIVE', 'feature_announcement'): 0.70,
            ('FRIENDLY', 'promotional'): 0.65,
            ('PROMOTIONAL', 'promotional'): 0.70,
        }
        
        key = (template.name, notification_type)
        engagement = base_engagement.get(key, 0.5)  # Default 0.5 if not matched
        
        # User segment modifiers
        if user_segment == 'young':
            if template in [NotificationTemplate.FRIENDLY, NotificationTemplate.CONCISE]:
                engagement *= 1.15
            elif template == NotificationTemplate.FORMAL:
                engagement *= 0.85
        elif user_segment == 'premium':
            if template in [NotificationTemplate.FORMAL, NotificationTemplate.CONCISE]:
                engagement *= 1.1
        
        # Add some noise for realism
        engagement += np.random.normal(0, 0.05)
        engagement = np.clip(engagement, 0.0, 1.0)
        
        return engagement
    
    def train(self):
        """Run complete training process"""
        print(f"Starting integrated training for {self.num_episodes} episodes...")
        print("=" * 70)
        print("Template Selection: Sleeping Multi-Armed Bandit (UCB1)")
        print("Channel Selection: Tug of War Algorithm")
        print("=" * 70)
        
        for episode in range(self.num_episodes):
            self.train_episode(episode)
            
            # Print progress
            if (episode + 1) % 1000 == 0:
                recent_engagement = np.mean(
                    self.metrics['template_engagement'][-1000:]
                )
                recent_success = np.mean(
                    self.metrics['channel_success'][-1000:]
                )
                recent_combined = np.mean(
                    self.metrics['combined_reward'][-1000:]
                )
                
                print(f"\nEpisode {episode + 1}/{self.num_episodes}")
                print(f"  Template Engagement (last 1000): {recent_engagement:.4f}")
                print(f"  Channel Success Rate (last 1000): {recent_success:.4f}")
                print(f"  Combined Reward (last 1000): {recent_combined:.4f}")
        
        print("\n" + "=" * 70)
        print("Training completed!")
        self._print_final_statistics()
    
    def _print_final_statistics(self):
        """Print final training statistics"""
        print("\nFINAL STATISTICS")
        print("=" * 70)
        
        # Template Bandit Statistics
        print("\nTEMPLATE SELECTION (Sleeping Multi-Armed Bandit):")
        print("-" * 70)
        template_stats = self.template_bandit.get_statistics()
        
        for template, stats in sorted(
            template_stats.items(),
            key=lambda x: x[1]['avg_engagement'],
            reverse=True
        ):
            print(f"{template:15s}: {stats['total_pulls']:5d} uses, "
                  f"Engagement: {stats['avg_engagement']:.4f}, "
                  f"Success: {stats['success_rate']:.4f}")
        
        best_template, best_engagement = self.template_bandit.get_best_template()
        print(f"\nBest Template: {best_template.value} "
              f"(avg engagement: {best_engagement:.4f})")
        
        # Channel Selector Statistics
        print("\nCHANNEL SELECTION (Tug of War):")
        print("-" * 70)
        channel_stats = self.channel_selector.get_statistics()
        
        for channel, stats in sorted(
            channel_stats.items(),
            key=lambda x: x[1]['success_rate'],
            reverse=True
        ):
            print(f"{channel:12s}: {stats['selections']:5d} selections "
                  f"({stats['selection_rate']:.1%}), "
                  f"Success: {stats['success_rate']:.4f}")
        
        # Overall Performance
        print("\nOVERALL PERFORMANCE:")
        print("-" * 70)
        avg_engagement = np.mean(self.metrics['template_engagement'])
        avg_success = np.mean(self.metrics['channel_success'])
        avg_combined = np.mean(self.metrics['combined_reward'])
        total_reward = self.metrics['cumulative_reward'][-1]
        
        print(f"Average Template Engagement: {avg_engagement:.4f}")
        print(f"Average Channel Success Rate: {avg_success:.4f}")
        print(f"Average Combined Reward: {avg_combined:.4f}")
        print(f"Total Cumulative Reward: {total_reward:.2f}")
    
    def plot_results(self, save_path: str = 'integrated_training_results.png'):
        """Plot training results"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        
        # Plot 1: Cumulative reward
        ax1 = axes[0, 0]
        ax1.plot(self.metrics['cumulative_reward'], 
                color='green', alpha=0.8, linewidth=2)
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Cumulative Reward')
        ax1.set_title('Cumulative Reward Over Time')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Moving average template engagement
        ax2 = axes[0, 1]
        window = 100
        engagement_ma = np.convolve(
            self.metrics['template_engagement'],
            np.ones(window)/window, mode='valid'
        )
        ax2.plot(engagement_ma, color='blue', alpha=0.8)
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Engagement Score')
        ax2.set_title(f'Template Engagement (MA-{window})')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Moving average channel success
        ax3 = axes[0, 2]
        success_ma = np.convolve(
            self.metrics['channel_success'],
            np.ones(window)/window, mode='valid'
        )
        ax3.plot(success_ma, color='orange', alpha=0.8)
        ax3.set_xlabel('Episode')
        ax3.set_ylabel('Success Rate')
        ax3.set_title(f'Channel Success Rate (MA-{window})')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Template usage distribution
        ax4 = axes[1, 0]
        template_stats = self.template_bandit.get_statistics()
        templates = list(template_stats.keys())
        pulls = [template_stats[t]['total_pulls'] for t in templates]
        ax4.bar(range(len(templates)), pulls, alpha=0.7, color='steelblue')
        ax4.set_xticks(range(len(templates)))
        ax4.set_xticklabels(templates, rotation=45, ha='right')
        ax4.set_xlabel('Template')
        ax4.set_ylabel('Number of Uses')
        ax4.set_title('Template Selection Distribution')
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Plot 5: Channel selection distribution
        ax5 = axes[1, 1]
        channel_stats = self.channel_selector.get_statistics()
        channels = list(channel_stats.keys())
        selections = [channel_stats[ch]['selections'] for ch in channels]
        ax5.bar(range(len(channels)), selections, alpha=0.7, color='coral')
        ax5.set_xticks(range(len(channels)))
        ax5.set_xticklabels(channels, rotation=45, ha='right')
        ax5.set_xlabel('Channel')
        ax5.set_ylabel('Number of Selections')
        ax5.set_title('Channel Selection Distribution (TOW)')
        ax5.grid(True, alpha=0.3, axis='y')
        
        # Plot 6: Combined performance metrics
        ax6 = axes[1, 2]
        combined_ma = np.convolve(
            self.metrics['combined_reward'],
            np.ones(window)/window, mode='valid'
        )
        ax6.plot(combined_ma, color='purple', alpha=0.8, linewidth=2)
        ax6.set_xlabel('Episode')
        ax6.set_ylabel('Combined Reward')
        ax6.set_title(f'Combined Performance (MA-{window})')
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nPlot saved to: {save_path}")
    
    def save_model(self, filepath: str = 'integrated_model.json'):
        """Save trained model statistics"""
        model_data = {
            'timestamp': datetime.now().isoformat(),
            'num_episodes': self.num_episodes,
            'seed': self.seed,
            'template_statistics': self.template_bandit.get_statistics(),
            'channel_statistics': self.channel_selector.get_statistics(),
            'performance_metrics': {
                'avg_template_engagement': float(np.mean(self.metrics['template_engagement'])),
                'avg_channel_success': float(np.mean(self.metrics['channel_success'])),
                'avg_combined_reward': float(np.mean(self.metrics['combined_reward'])),
                'total_cumulative_reward': float(self.metrics['cumulative_reward'][-1])
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2, default=str)
        
        print(f"Model statistics saved to: {filepath}")


def main():
    """Main training function"""
    print("=" * 70)
    print("INTEGRATED NOTIFICATION SYSTEM TRAINING")
    print("=" * 70)
    print("Template Selection: Sleeping Multi-Armed Bandit")
    print("Channel Selection: Tug of War Algorithm")
    print("=" * 70)
    print()
    
    # Create trainer
    trainer = IntegratedTrainer(num_episodes=10000, seed=42)
    
    # Train the models
    trainer.train()
    
    # Plot results
    trainer.plot_results('integrated_training_results.png')
    
    # Save model
    trainer.save_model('integrated_model.json')
    
    print("\n" + "=" * 70)
    print("Training pipeline completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    main()
