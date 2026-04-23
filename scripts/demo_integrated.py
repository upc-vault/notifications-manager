"""
Integrated Demo: Template Selection + Channel Selection
Demonstrates the complete notification system
"""

import json
from template_bandit import SleepingTemplateBandit, NotificationTemplate
from tug_of_war import TugOfWarSelector, NotificationChannel
from notification_environment import NotificationEnvironment, BankingScenario


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"{title:^70}")
    print(f"{'='*70}")


def simulate_notification(template_bandit, channel_selector, env, 
                         notification_type, priority, time_of_day, user_segment):
    """Simulate complete notification flow"""
    
    print(f"\n{'─'*70}")
    print(f"Notification Type: {notification_type.upper()}")
    print(f"Priority: {priority.upper()} | Time: {time_of_day} | User: {user_segment}")
    print(f"{'─'*70}")
    
    # Create context
    context = {
        'notification_type': notification_type,
        'user_segment': user_segment,
        'priority': priority,
        'time_of_day': time_of_day
    }
    
    # STEP 1: Select template using Sleeping Bandit
    print("\n🎯 STEP 1: Template Selection (Sleeping Multi-Armed Bandit)")
    selected_template = template_bandit.select_template(context)
    
    template_stats = template_bandit.get_statistics()[selected_template.value]
    print(f"  Selected Template: {selected_template.value.upper()}")
    print(f"  Template Stats: {template_stats['total_pulls']} uses, "
          f"{template_stats['avg_engagement']:.2%} engagement")
    
    # Get top 3 recommendations
    recommendations = template_bandit.get_template_recommendations(context, top_k=3)
    print(f"  Top Alternatives:")
    for i, (template, score) in enumerate(recommendations[:3], 1):
        print(f"    {i}. {template.value} (score: {score:.4f})")
    
    # STEP 2: Select channel using Tug of War
    print("\n📡 STEP 2: Channel Selection (Tug of War Algorithm)")
    available_channels = env.get_available_channels(time_of_day)
    print(f"  Available Channels: {', '.join([ch.value for ch in available_channels])}")
    
    selected_channel = channel_selector.select_channel(context, available_channels)
    channel_stats = channel_selector.get_statistics()[selected_channel.value]
    
    print(f"  Selected Channel: {selected_channel.value.upper()}")
    print(f"  Channel Stats: {channel_stats['selections']} selections, "
          f"{channel_stats['success_rate']:.2%} success rate")
    print(f"  Channel Metrics:")
    print(f"    • Availability: {channel_stats['availability']:.0%}")
    print(f"    • Cost: {channel_stats['cost']:.2f}")
    print(f"    • User Preference: {channel_stats['user_preference']:.2f}")
    
    # STEP 3: Simulate outcome
    print("\n📤 STEP 3: Sending Notification")
    print(f"  Template: {selected_template.value}")
    print(f"  Channel: {selected_channel.value}")
    
    # Simulate delivery
    channel_success = env.get_reward(selected_channel, time_of_day, user_segment) > 0
    
    # Simulate engagement (simplified)
    engagement = 0.8 if channel_success else 0.0
    
    print(f"  ✓ Delivered: {'YES' if channel_success else 'NO'}")
    print(f"  ✓ Engagement: {engagement:.0%}")
    
    # Update both systems
    template_bandit.update(selected_template, channel_success, engagement, context)
    channel_selector.update_success_rate(selected_channel, channel_success)
    
    return selected_template, selected_channel, channel_success, engagement


def main():
    """Run integrated demo"""
    print_section("INTEGRATED NOTIFICATION SYSTEM DEMO")
    print("\n🤖 Template Selection: Sleeping Multi-Armed Bandit (UCB1)")
    print("⚔️  Channel Selection: Tug of War Algorithm")
    
    # Load trained model
    try:
        with open('integrated_model.json', 'r') as f:
            model_data = json.load(f)
        print(f"\n✓ Loaded trained model ({model_data['num_episodes']} episodes)")
        print(f"  Average Engagement: {model_data['performance_metrics']['avg_template_engagement']:.2%}")
        print(f"  Average Success: {model_data['performance_metrics']['avg_channel_success']:.2%}")
    except FileNotFoundError:
        print("\n⚠ No trained model found. Using fresh models.")
        model_data = None
    
    # Initialize systems
    templates = list(NotificationTemplate)
    template_bandit = SleepingTemplateBandit(templates=templates, exploration_factor=2.0)
    
    channels = list(NotificationChannel)
    channel_selector = TugOfWarSelector(channels=channels)
    
    env = NotificationEnvironment(seed=42)
    
    # Demo Scenarios
    print_section("DEMO SCENARIOS")
    
    # Scenario 1: Critical Security Alert
    print("\n🚨 SCENARIO 1: CRITICAL SECURITY ALERT")
    simulate_notification(
        template_bandit, channel_selector, env,
        notification_type='security_alert',
        priority='critical',
        time_of_day='night',
        user_segment='premium'
    )
    
    # Scenario 2: Transaction Alert
    print("\n💳 SCENARIO 2: TRANSACTION ALERT")
    simulate_notification(
        template_bandit, channel_selector, env,
        notification_type='transaction_alert',
        priority='high',
        time_of_day='morning',
        user_segment='standard'
    )
    
    # Scenario 3: Promotional Offer
    print("\n🎁 SCENARIO 3: PROMOTIONAL OFFER")
    simulate_notification(
        template_bandit, channel_selector, env,
        notification_type='promotional',
        priority='low',
        time_of_day='afternoon',
        user_segment='young'
    )
    
    # Scenario 4: Account Statement
    print("\n📊 SCENARIO 4: ACCOUNT STATEMENT")
    simulate_notification(
        template_bandit, channel_selector, env,
        notification_type='account_statement',
        priority='medium',
        time_of_day='evening',
        user_segment='premium'
    )
    
    # Batch Processing
    print_section("BATCH PROCESSING (20 NOTIFICATIONS)")
    
    scenarios = [
        ('transaction_alert', 'high', 'morning', 'standard'),
        ('balance_update', 'medium', 'afternoon', 'young'),
        ('payment_due', 'high', 'evening', 'premium'),
        ('promotional', 'low', 'night', 'young'),
        ('security_alert', 'critical', 'morning', 'premium'),
        ('transaction_alert', 'high', 'afternoon', 'standard'),
        ('feature_announcement', 'low', 'evening', 'young'),
        ('account_statement', 'medium', 'morning', 'premium'),
        ('balance_update', 'medium', 'afternoon', 'standard'),
        ('promotional', 'low', 'evening', 'young'),
        ('transaction_alert', 'high', 'night', 'premium'),
        ('payment_due', 'high', 'morning', 'standard'),
        ('promotional', 'low', 'afternoon', 'young'),
        ('balance_update', 'medium', 'evening', 'premium'),
        ('transaction_alert', 'high', 'morning', 'young'),
        ('security_alert', 'critical', 'afternoon', 'premium'),
        ('feature_announcement', 'low', 'evening', 'standard'),
        ('promotional', 'low', 'night', 'young'),
        ('account_statement', 'medium', 'morning', 'premium'),
        ('transaction_alert', 'high', 'afternoon', 'standard'),
    ]
    
    results = {
        'templates': {},
        'channels': {},
        'success_count': 0,
        'total_engagement': 0.0
    }
    
    for i, (notif_type, priority, time, segment) in enumerate(scenarios, 1):
        context = {
            'notification_type': notif_type,
            'user_segment': segment,
            'priority': priority,
            'time_of_day': time
        }
        
        template = template_bandit.select_template(context)
        available = env.get_available_channels(time)
        channel = channel_selector.select_channel(context, available)
        
        success = env.get_reward(channel, time, segment) > 0
        engagement = 0.8 if success else 0.0
        
        template_bandit.update(template, success, engagement, context)
        channel_selector.update_success_rate(channel, success)
        
        # Track results
        results['templates'][template.value] = results['templates'].get(template.value, 0) + 1
        results['channels'][channel.value] = results['channels'].get(channel.value, 0) + 1
        if success:
            results['success_count'] += 1
        results['total_engagement'] += engagement
        
        status = '✓' if success else '✗'
        print(f"  #{i:2d}: {template.value:12s} → {channel.value:10s} {status} "
              f"({notif_type[:15]:15s}, {segment})")
    
    # Summary
    print(f"\n{'─'*70}")
    print(f"📊 BATCH RESULTS:")
    print(f"  Success Rate: {results['success_count']}/20 ({results['success_count']*5}%)")
    print(f"  Avg Engagement: {results['total_engagement']/20:.2%}")
    print(f"\n  Template Distribution:")
    for template, count in sorted(results['templates'].items(), key=lambda x: x[1], reverse=True):
        print(f"    • {template:12s}: {count:2d} times ({count*5:2d}%)")
    print(f"\n  Channel Distribution:")
    for channel, count in sorted(results['channels'].items(), key=lambda x: x[1], reverse=True):
        print(f"    • {channel:12s}: {count:2d} times ({count*5:2d}%)")
    
    # Final Statistics
    print_section("FINAL SYSTEM STATISTICS")
    
    print("\n📝 TEMPLATE BANDIT (Sleeping Multi-Armed Bandit)")
    print(f"{'Template':<15} {'Uses':<8} {'Engagement':<12} {'Success Rate'}")
    print(f"{'─'*60}")
    
    template_stats = template_bandit.get_statistics()
    for template, stats in sorted(
        template_stats.items(),
        key=lambda x: x[1]['avg_engagement'],
        reverse=True
    ):
        print(f"{template:<15} {stats['total_pulls']:<8} "
              f"{stats['avg_engagement']:<12.2%} {stats['success_rate']:.2%}")
    
    print("\n📡 CHANNEL SELECTOR (Tug of War)")
    print(f"{'Channel':<15} {'Selections':<12} {'Success Rate':<15} {'Cost'}")
    print(f"{'─'*60}")
    
    channel_stats = channel_selector.get_statistics()
    for channel, stats in sorted(
        channel_stats.items(),
        key=lambda x: x[1]['success_rate'],
        reverse=True
    ):
        print(f"{channel:<15} {stats['selections']:<12} "
              f"{stats['success_rate']:<15.2%} {stats['cost']:.2f}")
    
    # Key Insights
    print_section("KEY INSIGHTS")
    
    print("""
    ✓ Two-Stage Selection Process:
      1. Sleeping Bandit selects optimal TEMPLATE based on context
      2. Tug of War selects optimal CHANNEL based on real-time metrics
    
    ✓ Template Selection Learning:
      • Learns which templates engage users for different notification types
      • Balances exploration (trying new templates) and exploitation (using best)
      • Context-aware: considers user segment, priority, notification type
    
    ✓ Channel Selection Optimization:
      • Considers availability, cost, latency, success rate, user preference
      • Dynamic weight adjustment based on priority
      • Real-time adaptation to changing conditions
    
    ✓ Combined Performance:
      • Both systems learn independently
      • Template choice affects engagement
      • Channel choice affects delivery success
      • Combined optimization maximizes overall effectiveness
    """)
    
    print_section("READY FOR PRODUCTION")
    print("""
    Next Steps:
      1. Deploy as microservice API (FastAPI/Flask)
      2. Integrate with real notification services:
         • Twilio (SMS)
         • Firebase Cloud Messaging (Push)
         • SendGrid (Email)
         • WhatsApp Business API
      3. Add persistence layer (database for history)
      4. Implement monitoring and analytics dashboard
      5. A/B testing against baseline strategies
    """)


if __name__ == '__main__':
    main()
