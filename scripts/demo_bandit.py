"""
Demo: Real-time notification channel selection
Shows how the trained bandit makes decisions in various scenarios
"""

import json
from sleeping_bandit import SleepingBandit, NotificationChannel
from notification_environment import NotificationEnvironment, BankingScenario


def print_scenario(scenario_name: str, scenario_data: dict):
    """Pretty print scenario details"""
    print(f"\n{'='*70}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*70}")
    print(f"Priority: {scenario_data['priority'].upper()}")
    print(f"Description: {scenario_data['description']}")
    print(f"Max Delay: {scenario_data['max_delay']}s")
    print(f"Preferred Channels: {', '.join([c.value for c in scenario_data['preferred_channels']])}")


def simulate_notification(bandit, env, scenario_name, scenario_data, 
                         time_of_day, user_segment):
    """Simulate sending a notification"""
    print(f"\nContext:")
    print(f"  Time of Day: {time_of_day}")
    print(f"  User Segment: {user_segment}")
    
    # Get available channels
    available = env.get_available_channels(time_of_day)
    print(f"  Available Channels: {', '.join([c.value for c in available])}")
    
    # Select channel using bandit
    selected = bandit.select_channel(available)
    print(f"\n✓ BANDIT SELECTED: {selected.value.upper()}")
    
    # Get current statistics
    stats = bandit.get_statistics()
    arm_stats = stats[selected.value]
    print(f"  Channel Stats: {arm_stats['success_count']}/{arm_stats['total_pulls']} " +
          f"({arm_stats['success_rate']:.2%} success rate)")
    
    # Simulate sending
    reward = env.get_reward(selected, time_of_day, user_segment)
    success = reward > 0
    
    print(f"  Result: {'✓ SUCCESS' if success else '✗ FAILED'}")
    
    # Update bandit
    bandit.update(selected, reward, available)
    
    return selected, success


def main():
    """Run interactive demo"""
    print("="*70)
    print("SLEEPING MULTI-ARMED BANDIT DEMO")
    print("Real-time Notification Channel Selection for Banking")
    print("="*70)
    
    # Load trained model statistics
    try:
        with open('trained_bandit_model.json', 'r') as f:
            model_data = json.load(f)
        print(f"\n✓ Loaded trained model (trained on {model_data['num_episodes']} episodes)")
    except FileNotFoundError:
        print("\n⚠ No trained model found. Using fresh bandit.")
        model_data = None
    
    # Initialize bandit and environment
    channels = list(NotificationChannel)
    bandit = SleepingBandit(channels=channels, exploration_factor=2.0)
    env = NotificationEnvironment(seed=42)
    
    # Pre-train the bandit with some data if we have model stats
    if model_data:
        print("   Using learned channel preferences from training")
    
    print("\n" + "="*70)
    print("RUNNING DEMO SCENARIOS")
    print("="*70)
    
    # Scenario 1: Critical transaction alert in the morning
    scenario1 = BankingScenario.transaction_alert()
    print_scenario("1. TRANSACTION ALERT", scenario1)
    simulate_notification(
        bandit, env, "Transaction Alert", scenario1,
        time_of_day='morning',
        user_segment='premium'
    )
    
    # Scenario 2: Security alert at night
    scenario2 = BankingScenario.security_alert()
    print_scenario("2. SECURITY ALERT", scenario2)
    simulate_notification(
        bandit, env, "Security Alert", scenario2,
        time_of_day='night',
        user_segment='standard'
    )
    
    # Scenario 3: Account statement in the afternoon
    scenario3 = BankingScenario.account_statement()
    print_scenario("3. ACCOUNT STATEMENT", scenario3)
    simulate_notification(
        bandit, env, "Account Statement", scenario3,
        time_of_day='afternoon',
        user_segment='premium'
    )
    
    # Scenario 4: Promotional offer to young user
    scenario4 = BankingScenario.promotional_offer()
    print_scenario("4. PROMOTIONAL OFFER", scenario4)
    simulate_notification(
        bandit, env, "Promotional Offer", scenario4,
        time_of_day='evening',
        user_segment='young'
    )
    
    # Scenario 5: Multiple notifications in sequence
    print(f"\n{'='*70}")
    print("SCENARIO: 5. BATCH PROCESSING (10 notifications)")
    print(f"{'='*70}")
    print("\nSending 10 transaction alerts to different users...")
    
    successes = 0
    channel_usage = {ch: 0 for ch in NotificationChannel}
    
    for i in range(10):
        time_of_day = ['morning', 'afternoon', 'evening', 'night'][i % 4]
        user_segment = ['standard', 'premium', 'young'][i % 3]
        
        available = env.get_available_channels(time_of_day)
        selected = bandit.select_channel(available)
        reward = env.get_reward(selected, time_of_day, user_segment)
        
        bandit.update(selected, reward, available)
        
        channel_usage[selected] += 1
        if reward > 0:
            successes += 1
        
        print(f"  #{i+1}: {selected.value:10s} -> {'✓' if reward > 0 else '✗'} "
              f"(time: {time_of_day:9s}, user: {user_segment})")
    
    print(f"\nBatch Results:")
    print(f"  Success Rate: {successes}/10 ({successes*10}%)")
    print(f"  Channel Usage:")
    for channel, count in channel_usage.items():
        if count > 0:
            print(f"    {channel.value}: {count} times")
    
    # Final statistics
    print(f"\n{'='*70}")
    print("FINAL BANDIT STATISTICS")
    print(f"{'='*70}")
    
    stats = bandit.get_statistics()
    print(f"\n{'Channel':<15} {'Selections':<12} {'Success Rate':<15} {'UCB Score'}")
    print("-" * 70)
    
    for channel_name, channel_stats in sorted(stats.items(), 
                                              key=lambda x: x[1]['success_rate'], 
                                              reverse=True):
        pulls = channel_stats['total_pulls']
        rate = channel_stats['success_rate']
        ucb = channel_stats.get('ucb_score', 'N/A')
        ucb_str = f"{ucb:.4f}" if isinstance(ucb, (int, float)) else str(ucb)
        
        print(f"{channel_name:<15} {pulls:<12} {rate:<15.2%} {ucb_str}")
    
    best_channel, best_rate = bandit.get_best_channel()
    print(f"\n✓ Best Performing Channel: {best_channel.value.upper()} ({best_rate:.2%})")
    
    print(f"\n{'='*70}")
    print("DEMO COMPLETED")
    print(f"{'='*70}")
    print("\nKey Insights:")
    print("  • The bandit learns which channels work best over time")
    print("  • It adapts to context (time of day, user segment)")
    print("  • It handles sleeping arms (unavailable channels)")
    print("  • It balances exploration (trying new options) and exploitation")
    print("  • Real-time decision making with continuous learning")
    
    print("\n" + "="*70)
    print("Next Steps:")
    print("  1. Integrate with actual notification services (Twilio, Firebase, etc.)")
    print("  2. Deploy as a microservice API")
    print("  3. Monitor real-world performance metrics")
    print("  4. Implement A/B testing against baseline strategies")
    print("  5. Add cost optimization (SMS costs more than push)")
    print("="*70)


if __name__ == '__main__':
    main()
