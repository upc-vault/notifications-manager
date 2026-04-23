"""
Training script for Sleeping Multi-Armed Bandit
Trains the algorithm to select optimal notification channels
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict
import json
from datetime import datetime

from sleeping_bandit import (
    SleepingBandit, 
    EpsilonGreedyBandit, 
    NotificationChannel
)
from notification_environment import NotificationEnvironment, BankingScenario


class BanditTrainer:
    """Handles training and evaluation of bandit algorithms"""
    
    def __init__(self, num_episodes: int = 10000, seed: int = 42):
        """
        Initialize trainer
        
        Args:
            num_episodes: Number of training episodes
            seed: Random seed for reproducibility
        """
        self.num_episodes = num_episodes
        self.seed = seed
        self.environment = NotificationEnvironment(seed=seed)
        
        # Initialize both algorithms for comparison
        channels = list(NotificationChannel)
        self.ucb_bandit = SleepingBandit(channels=channels, exploration_factor=2.0)
        self.epsilon_bandit = EpsilonGreedyBandit(channels=channels, epsilon=0.1)
        
        # Training metrics
        self.metrics = {
            'ucb': {'rewards': [], 'cumulative_rewards': [], 'regret': []},
            'epsilon': {'rewards': [], 'cumulative_rewards': [], 'regret': []}
        }
        
    def train_episode(self, bandit, algorithm_name: str, episode: int):
        """
        Run a single training episode
        
        Args:
            bandit: Bandit algorithm instance
            algorithm_name: 'ucb' or 'epsilon'
            episode: Current episode number
        """
        # Get context for this episode
        time_of_day = self.environment.get_time_of_day(episode)
        user_segment = self.environment.get_user_segment(episode)
        
        # Get available channels (some may be sleeping)
        available_channels = self.environment.get_available_channels(time_of_day)
        
        # Select channel using bandit algorithm
        selected_channel = bandit.select_channel(available_channels)
        
        # Get reward from environment
        reward = self.environment.get_reward(selected_channel, time_of_day, user_segment)
        
        # Update bandit
        bandit.update(selected_channel, reward, available_channels)
        
        # Track metrics
        self.metrics[algorithm_name]['rewards'].append(reward)
        
        cumulative = (
            self.metrics[algorithm_name]['cumulative_rewards'][-1] + reward
            if self.metrics[algorithm_name]['cumulative_rewards']
            else reward
        )
        self.metrics[algorithm_name]['cumulative_rewards'].append(cumulative)
        
    def train(self):
        """Run complete training process"""
        print(f"Starting training for {self.num_episodes} episodes...")
        print("=" * 60)
        
        for episode in range(self.num_episodes):
            # Train both algorithms
            self.train_episode(self.ucb_bandit, 'ucb', episode)
            self.train_episode(self.epsilon_bandit, 'epsilon', episode)
            
            # Print progress
            if (episode + 1) % 1000 == 0:
                ucb_avg = np.mean(self.metrics['ucb']['rewards'][-1000:])
                eps_avg = np.mean(self.metrics['epsilon']['rewards'][-1000:])
                print(f"Episode {episode + 1}/{self.num_episodes}")
                print(f"  UCB avg reward (last 1000): {ucb_avg:.4f}")
                print(f"  Epsilon-Greedy avg reward (last 1000): {eps_avg:.4f}")
        
        print("\n" + "=" * 60)
        print("Training completed!")
        self._print_final_statistics()
    
    def _print_final_statistics(self):
        """Print final training statistics"""
        print("\nFINAL STATISTICS")
        print("=" * 60)
        
        # UCB Statistics
        print("\nUCB1 Algorithm:")
        print("-" * 40)
        ucb_stats = self.ucb_bandit.get_statistics()
        for channel, stats in ucb_stats.items():
            print(f"{channel:12s}: {stats['total_pulls']:5d} pulls, "
                  f"Success rate: {stats['success_rate']:.4f}")
        
        best_channel, best_rate = self.ucb_bandit.get_best_channel()
        print(f"\nBest channel: {best_channel.value} (success rate: {best_rate:.4f})")
        
        # Epsilon-Greedy Statistics
        print("\nEpsilon-Greedy Algorithm:")
        print("-" * 40)
        eps_stats = self.epsilon_bandit.get_statistics()
        for channel, stats in eps_stats.items():
            print(f"{channel:12s}: {stats['total_pulls']:5d} pulls, "
                  f"Success rate: {stats['success_rate']:.4f}")
        
        best_channel, best_rate = self.epsilon_bandit.get_best_channel()
        print(f"\nBest channel: {best_channel.value} (success rate: {best_rate:.4f})")
        
        # Overall comparison
        print("\nOVERALL PERFORMANCE:")
        print("-" * 40)
        ucb_total = self.metrics['ucb']['cumulative_rewards'][-1]
        eps_total = self.metrics['epsilon']['cumulative_rewards'][-1]
        
        print(f"UCB1 total reward: {ucb_total:.2f}")
        print(f"Epsilon-Greedy total reward: {eps_total:.2f}")
        print(f"Difference: {abs(ucb_total - eps_total):.2f} "
              f"({'UCB1 wins' if ucb_total > eps_total else 'Epsilon-Greedy wins'})")
        
        # Average reward per episode
        ucb_avg = np.mean(self.metrics['ucb']['rewards'])
        eps_avg = np.mean(self.metrics['epsilon']['rewards'])
        print(f"\nUCB1 avg reward per episode: {ucb_avg:.4f}")
        print(f"Epsilon-Greedy avg reward per episode: {eps_avg:.4f}")
    
    def plot_results(self, save_path: str = 'training_results.png'):
        """Plot training results"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Cumulative rewards
        ax1 = axes[0, 0]
        ax1.plot(self.metrics['ucb']['cumulative_rewards'], label='UCB1', alpha=0.8)
        ax1.plot(self.metrics['epsilon']['cumulative_rewards'], label='Epsilon-Greedy', alpha=0.8)
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Cumulative Reward')
        ax1.set_title('Cumulative Rewards Over Time')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Moving average reward (window=100)
        ax2 = axes[0, 1]
        window = 100
        ucb_ma = np.convolve(self.metrics['ucb']['rewards'], 
                             np.ones(window)/window, mode='valid')
        eps_ma = np.convolve(self.metrics['epsilon']['rewards'], 
                             np.ones(window)/window, mode='valid')
        ax2.plot(ucb_ma, label='UCB1', alpha=0.8)
        ax2.plot(eps_ma, label='Epsilon-Greedy', alpha=0.8)
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Average Reward')
        ax2.set_title(f'Moving Average Reward (window={window})')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Channel selection distribution (UCB)
        ax3 = axes[1, 0]
        ucb_stats = self.ucb_bandit.get_statistics()
        channels = list(ucb_stats.keys())
        pulls = [ucb_stats[ch]['total_pulls'] for ch in channels]
        ax3.bar(channels, pulls, alpha=0.7, color='steelblue')
        ax3.set_xlabel('Channel')
        ax3.set_ylabel('Number of Selections')
        ax3.set_title('Channel Selection Distribution (UCB1)')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Plot 4: Channel success rates comparison
        ax4 = axes[1, 1]
        ucb_rates = [ucb_stats[ch]['success_rate'] for ch in channels]
        eps_stats = self.epsilon_bandit.get_statistics()
        eps_rates = [eps_stats[ch]['success_rate'] for ch in channels]
        
        x = np.arange(len(channels))
        width = 0.35
        ax4.bar(x - width/2, ucb_rates, width, label='UCB1', alpha=0.7)
        ax4.bar(x + width/2, eps_rates, width, label='Epsilon-Greedy', alpha=0.7)
        ax4.set_xlabel('Channel')
        ax4.set_ylabel('Success Rate')
        ax4.set_title('Learned Success Rates by Channel')
        ax4.set_xticks(x)
        ax4.set_xticklabels(channels, rotation=45)
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nPlot saved to: {save_path}")
        
    def save_model(self, filepath: str = 'trained_bandit_model.json'):
        """Save trained model statistics"""
        model_data = {
            'timestamp': datetime.now().isoformat(),
            'num_episodes': self.num_episodes,
            'seed': self.seed,
            'ucb_statistics': self.ucb_bandit.get_statistics(),
            'epsilon_statistics': self.epsilon_bandit.get_statistics(),
            'total_rewards': {
                'ucb': float(self.metrics['ucb']['cumulative_rewards'][-1]),
                'epsilon': float(self.metrics['epsilon']['cumulative_rewards'][-1])
            },
            'average_rewards': {
                'ucb': float(np.mean(self.metrics['ucb']['rewards'])),
                'epsilon': float(np.mean(self.metrics['epsilon']['rewards']))
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2, default=str)
        
        print(f"Model statistics saved to: {filepath}")


def main():
    """Main training function"""
    print("=" * 60)
    print("SLEEPING MULTI-ARMED BANDIT TRAINING")
    print("Notification Channel Selection for Banking")
    print("=" * 60)
    print()
    
    # Create trainer
    trainer = BanditTrainer(num_episodes=10000, seed=42)
    
    # Train the models
    trainer.train()
    
    # Plot results
    trainer.plot_results('training_results.png')
    
    # Save model
    trainer.save_model('trained_bandit_model.json')
    
    print("\n" + "=" * 60)
    print("Training pipeline completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
