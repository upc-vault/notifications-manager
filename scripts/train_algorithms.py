"""
Training script for Sleeping Multi-Armed Bandit and Tug of War algorithms.
Simulates notification scenarios based on realistic user profiles and preferences.
"""
import numpy as np
import matplotlib.pyplot as plt
from typing import List
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ml.sleeping_bandit import SleepingMultiArmedBandit, Template
from ml.tug_of_war import TugOfWarChannelSelector, Channel
from models.user_profile import UserProfile, create_sample_users
import json


def simulate_user_engagement(template_id: str, channel: Channel, user: UserProfile) -> tuple[bool, float]:
    """
    Simulate user engagement based on user profile, preferences, and behavior.
    
    Args:
        template_id: The notification template used
        channel: The communication channel used
        user: The user profile with preferences and history
    
    Returns:
        (success: bool, reward: float)
    """
    # Base success rates for template types
    base_rates = {
        'template_urgent': 0.85,
        'template_promo': 0.45,
        'template_info': 0.60,
        'template_security': 0.90,
    }
    
    # Channel delivery reliability
    channel_multipliers = {
        Channel.PUSH: 1.0,
        Channel.EMAIL: 0.7,
        Channel.SMS: 0.85,
        Channel.WHATSAPP: 0.95,
        Channel.WEBPUSH: 0.6,
    }
    
    # Get user affinities
    template_affinity = user.get_template_affinity(template_id)
    channel_affinity = user.get_channel_affinity(channel.value)
    
    # Calculate success probability incorporating user profile
    base_rate = base_rates.get(template_id, 0.5)
    multiplier = channel_multipliers.get(channel, 0.5)
    
    # Combine all factors
    success_prob = base_rate * multiplier * template_affinity * channel_affinity
    
    # Add behavioral learning component
    if user.behavior.total_notifications > 10:
        # Users with history have more predictable behavior
        success_prob = 0.7 * success_prob + 0.3 * user.behavior.open_rate
    
    # Add randomness for natural variation
    success_prob += np.random.uniform(-0.08, 0.08)
    success_prob = np.clip(success_prob, 0, 1)
    
    # Determine success
    success = np.random.random() < success_prob
    
    # Calculate reward based on engagement level
    reward = 0.0
    clicked = False
    opened = False
    
    if success:
        engagement_level = np.random.random()
        # Higher digital adoption leads to higher engagement
        engagement_threshold = 0.7 - (user.digital_adoption * 0.2)
        
        if engagement_level > engagement_threshold:
            reward = 1.0  # Click/Action
            clicked = True
            opened = True
        elif engagement_level > 0.3:
            reward = 0.6  # Open
            opened = True
        else:
            reward = 0.3  # Delivered
    
    # Update user behavior
    user.update_behavior(template_id, channel.value, opened, clicked)
    
    return success, reward


def train_sleeping_bandit(users: List[UserProfile], n_iterations: int = 1000):
    """Train the Sleeping Multi-Armed Bandit algorithm with user profiles"""
    print("=" * 60)
    print("TRAINING SLEEPING MULTI-ARMED BANDIT")
    print("=" * 60)
    print(f"Training with {len(users)} user profiles\n")
    
    # Define templates
    templates = [
        Template("template_urgent", "Urgent Alert", "¡Transferencia detectada! Revisa ahora."),
        Template("template_promo", "Promotional", "Oferta especial: 50% descuento en préstamos"),
        Template("template_info", "Informational", "Tu estado de cuenta está disponible"),
        Template("template_security", "Security Alert", "Inicio de sesión desde nuevo dispositivo"),
    ]
    
    # Initialize bandit per user (personalized learning)
    bandits = {user.user_id: SleepingMultiArmedBandit(templates, epsilon=0.3, decay_rate=0.995) 
               for user in users}
    
    # Tracking metrics
    rewards_history = []
    template_selection_count = {t.id: 0 for t in templates}
    user_rewards = {user.user_id: [] for user in users}
    
    # Training loop
    for i in range(n_iterations):
        # Select a random user for this iteration
        user = np.random.choice(users)
        bandit = bandits[user.user_id]
        
        # Simulate template sleeping based on time/context and user preferences
        # Promos sleep if user has marketing opt-out
        if not user.preferences.marketing_opt_in:
            bandit.set_template_availability("template_promo", False)
        elif i % 100 < 20:  # 20% of the time, promos sleep (night hours)
            bandit.set_template_availability("template_promo", False)
        else:
            bandit.set_template_availability("template_promo", True)
        
        # Select template
        selected_template = bandit.select_template()
        template_selection_count[selected_template] += 1
        
        # Simulate user engagement with user profile
        _, reward = simulate_user_engagement(selected_template, Channel.PUSH, user)
        
        # Update bandit
        bandit.update_reward(selected_template, reward)
        rewards_history.append(reward)
        user_rewards[user.user_id].append(reward)
        
        # Print progress
        if (i + 1) % 200 == 0:
            avg_reward = np.mean(rewards_history[-200:])
            print(f"Iteration {i+1}: Avg Reward = {avg_reward:.3f}")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    
    # Aggregate statistics across all users
    all_stats = [bandit.get_statistics() for bandit in bandits.values()]
    
    print(f"Total selections: {sum(s['total_selections'] for s in all_stats)}")
    print(f"Average reward across all users: {np.mean(rewards_history):.3f}")
    
    print("\nTemplate Performance (Aggregated):")
    template_summary = {}
    for stats in all_stats:
        for t in stats['templates']:
            if t['name'] not in template_summary:
                template_summary[t['name']] = {'pulls': 0, 'total_reward': 0}
            template_summary[t['name']]['pulls'] += t['pulls']
            template_summary[t['name']]['total_reward'] += t['pulls'] * t['avg_reward']
    
    for name, data in template_summary.items():
        avg_reward = data['total_reward'] / data['pulls'] if data['pulls'] > 0 else 0
        print(f"  {name:20s} | Pulls: {data['pulls']:4d} | Avg Reward: {avg_reward:.3f}")
    
    print("\nPer-User Performance:")
    for user in users:
        user_avg = np.mean(user_rewards[user.user_id]) if user_rewards[user.user_id] else 0
        print(f"  {user.name:20s} ({user.banking_tier.value:12s}) | "
              f"Avg Reward: {user_avg:.3f} | "
              f"Open Rate: {user.behavior.open_rate:.2%}")
    
    return bandits, rewards_history


def train_tug_of_war(users: List[UserProfile], n_iterations: int = 1000):
    """Train the Tug of War channel selector with user profiles"""
    print("\n" + "=" * 60)
    print("TRAINING TUG OF WAR CHANNEL SELECTOR")
    print("=" * 60)
    print(f"Training with {len(users)} user profiles\n")
    
    # Initialize selector with all channels
    channels = [Channel.PUSH, Channel.EMAIL, Channel.SMS, Channel.WHATSAPP, Channel.WEBPUSH]
    
    # Personalized selector per user
    selectors = {user.user_id: TugOfWarChannelSelector(
        channels,
        pull_strength=0.05,
        position_weight=0.6,
        performance_weight=0.4
    ) for user in users}
    
    # Tracking metrics
    channel_selection_count = {ch: 0 for ch in channels}
    success_rates_history = {ch: [] for ch in channels}
    user_channel_prefs = {user.user_id: {ch: [] for ch in channels} for user in users}
    
    # Training loop
    for i in range(n_iterations):
        # Select a random user
        user = np.random.choice(users)
        selector = selectors[user.user_id]
        
        # Select channel based on TOW algorithm
        selected_channel = selector.select_channel()
        channel_selection_count[selected_channel] += 1
        
        # Simulate notification delivery with user profile
        success, _ = simulate_user_engagement("template_security", selected_channel, user)
        
        # Update selector
        selector.update_result(selected_channel, success)
        
        # Track per-user success rates
        user_channel_prefs[user.user_id][selected_channel].append(success)
        
        # Track aggregate success rates
        for ch in channels:
            # Aggregate across all users
            all_successes = []
            for sel in selectors.values():
                stats = sel.stats[ch]
                if stats.total_attempts > 0:
                    all_successes.append(stats.success_rate)
            success_rates_history[ch].append(np.mean(all_successes) if all_successes else 0)
        
        # Print progress
        if (i + 1) % 200 == 0:
            print(f"\nIteration {i+1}:")
            # Show aggregate statistics
            for ch in channels:
                all_stats = [sel.stats[ch] for sel in selectors.values()]
                avg_pos = np.mean([s.position for s in all_stats])
                avg_success = np.mean([s.success_rate for s in all_stats if s.total_attempts > 0])
                total_attempts = sum(s.total_attempts for s in all_stats)
                print(f"  {ch.value:10s} | Avg Pos: {avg_pos:+.3f} | "
                      f"Avg Success: {avg_success:.3f} | Total Attempts: {total_attempts}")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    
    # Aggregate statistics
    print("\nChannel Performance (Aggregated across all users):")
    for ch in channels:
        all_stats = [sel.stats[ch] for sel in selectors.values()]
        avg_pos = np.mean([s.position for s in all_stats])
        avg_success = np.mean([s.success_rate for s in all_stats if s.total_attempts > 0])
        total_attempts = sum(s.total_attempts for s in all_stats)
        print(f"  {ch.value:10s} | Avg Position: {avg_pos:+.3f} | "
              f"Avg Success Rate: {avg_success:.3f} | "
              f"Total Attempts: {total_attempts}")
    
    print("\nPer-User Best Channels:")
    for user in users:
        selector = selectors[user.user_id]
        best = selector.get_best_channel()
        best_success = selector.stats[best].success_rate
        print(f"  {user.name:20s} ({user.banking_tier.value:12s}) | "
              f"Best: {best.value:10s} ({best_success:.2%})")
    
    return selectors, success_rates_history


def plot_results(bandit_rewards, tow_success_rates):
    """Plot training results"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Bandit rewards over time
    ax1.plot(np.convolve(bandit_rewards, np.ones(50)/50, mode='valid'))
    ax1.set_title('Sleeping Multi-Armed Bandit: Average Reward Over Time')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Average Reward (50-iteration moving average)')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Tug of War channel success rates
    for channel, rates in tow_success_rates.items():
        if rates:  # Only plot if there's data
            ax2.plot(rates, label=channel.value, alpha=0.7)
    
    ax2.set_title('Tug of War: Channel Success Rates Over Time')
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Success Rate')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('training_results.png', dpi=150)
    print("\n✓ Training results plot saved to: training_results.png")


def main():
    """Main training function"""
    print("\n" + "=" * 60)
    print("NOTIFICATION MANAGER ALGORITHM TRAINING")
    print("WITH USER PROFILES AND PREFERENCES")
    print("=" * 60)
    
    # Create diverse user profiles
    users = create_sample_users()
    print(f"\nCreated {len(users)} diverse user profiles:")
    for user in users:
        print(f"  - {user.name} ({user.age}y, {user.banking_tier.value}, "
              f"Digital Adoption: {user.digital_adoption:.0%})")
    
    # Train Sleeping Bandit with user profiles
    bandits, bandit_rewards = train_sleeping_bandit(users, n_iterations=1000)
    
    # Train Tug of War with user profiles
    selectors, tow_success_rates = train_tug_of_war(users, n_iterations=1000)
    
    # Plot results
    plot_results(bandit_rewards, tow_success_rates)
    
    # Save trained models
    print("\n" + "=" * 60)
    print("Saving trained models...")
    
    # Get data directory path
    data_dir = Path(__file__).parent.parent / "data" / "training"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save aggregated bandit statistics
    all_bandit_stats = {
        'users': [
            {
                'user_id': user_id,
                'stats': bandit.get_statistics()
            }
            for user_id, bandit in bandits.items()
        ],
        'aggregate_reward': float(np.mean(bandit_rewards))
    }
    with open(data_dir / 'bandit_stats.json', 'w') as f:
        json.dump(all_bandit_stats, f, indent=2)
    print(f"✓ Bandit statistics saved to: {data_dir / 'bandit_stats.json'}")
    
    # Save aggregated TOW statistics
    all_tow_stats = {
        'users': [
            {
                'user_id': user_id,
                'stats': selector.get_statistics()
            }
            for user_id, selector in selectors.items()
        ]
    }
    with open(data_dir / 'tow_stats.json', 'w') as f:
        json.dump(all_tow_stats, f, indent=2)
    print(f"✓ TOW statistics saved to: {data_dir / 'tow_stats.json'}")
    
    # Save user profiles with learned behavior
    user_profiles_data = [
        {
            'user_id': user.user_id,
            'name': user.name,
            'age': user.age,
            'banking_tier': user.banking_tier.value,
            'digital_adoption': user.digital_adoption,
            'behavior': {
                'total_notifications': user.behavior.total_notifications,
                'open_rate': user.behavior.open_rate,
                'click_rate': user.behavior.click_rate,
                'template_engagement': user.behavior.template_engagement,
                'channel_engagement': user.behavior.channel_engagement,
            }
        }
        for user in users
    ]
    with open(data_dir / 'user_profiles.json', 'w') as f:
        json.dump(user_profiles_data, f, indent=2)
    print(f"✓ User profiles saved to: {data_dir / 'user_profiles.json'}")
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
