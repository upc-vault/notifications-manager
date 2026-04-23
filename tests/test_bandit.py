"""
Test and evaluate the trained sleeping bandit model
Includes unit tests and scenario-based testing
"""

import unittest
import numpy as np
from sleeping_bandit import (
    SleepingBandit, 
    EpsilonGreedyBandit, 
    NotificationChannel,
    BanditArm
)
from notification_environment import NotificationEnvironment, BankingScenario


class TestBanditArm(unittest.TestCase):
    """Test BanditArm functionality"""
    
    def test_initialization(self):
        """Test arm initialization"""
        arm = BanditArm(channel=NotificationChannel.SMS)
        self.assertEqual(arm.channel, NotificationChannel.SMS)
        self.assertEqual(arm.success_count, 0)
        self.assertEqual(arm.failure_count, 0)
        self.assertEqual(arm.total_pulls, 0)
        self.assertEqual(arm.success_rate, 0.0)
    
    def test_update_success(self):
        """Test arm update with success"""
        arm = BanditArm(channel=NotificationChannel.PUSH)
        arm.update(1.0)
        self.assertEqual(arm.total_pulls, 1)
        self.assertEqual(arm.success_count, 1)
        self.assertEqual(arm.failure_count, 0)
        self.assertEqual(arm.success_rate, 1.0)
    
    def test_update_failure(self):
        """Test arm update with failure"""
        arm = BanditArm(channel=NotificationChannel.EMAIL)
        arm.update(0.0)
        self.assertEqual(arm.total_pulls, 1)
        self.assertEqual(arm.success_count, 0)
        self.assertEqual(arm.failure_count, 1)
        self.assertEqual(arm.success_rate, 0.0)
    
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        arm = BanditArm(channel=NotificationChannel.WHATSAPP)
        arm.update(1.0)
        arm.update(1.0)
        arm.update(0.0)
        arm.update(1.0)
        
        self.assertEqual(arm.total_pulls, 4)
        self.assertEqual(arm.success_count, 3)
        self.assertEqual(arm.success_rate, 0.75)


class TestSleepingBandit(unittest.TestCase):
    """Test SleepingBandit algorithm"""
    
    def setUp(self):
        """Set up test bandit"""
        channels = list(NotificationChannel)
        self.bandit = SleepingBandit(channels=channels, exploration_factor=2.0)
    
    def test_initialization(self):
        """Test bandit initialization"""
        self.assertEqual(len(self.bandit.arms), 4)
        self.assertEqual(self.bandit.total_time, 0)
        self.assertIn(NotificationChannel.SMS, self.bandit.arms)
    
    def test_ucb_score_unexplored(self):
        """Test UCB score for unexplored arm"""
        arm = self.bandit.arms[NotificationChannel.SMS]
        score = self.bandit.get_ucb_score(arm)
        self.assertEqual(score, float('inf'))
    
    def test_select_channel_single(self):
        """Test channel selection with single available channel"""
        available = [NotificationChannel.SMS]
        selected = self.bandit.select_channel(available)
        self.assertEqual(selected, NotificationChannel.SMS)
    
    def test_select_channel_no_available(self):
        """Test channel selection with no available channels"""
        with self.assertRaises(ValueError):
            self.bandit.select_channel([])
    
    def test_update(self):
        """Test bandit update"""
        channel = NotificationChannel.PUSH
        available = [NotificationChannel.PUSH, NotificationChannel.SMS]
        
        self.bandit.update(channel, 1.0, available)
        
        self.assertEqual(self.bandit.total_time, 1)
        self.assertEqual(self.bandit.arms[channel].total_pulls, 1)
        self.assertEqual(len(self.bandit.history), 1)
    
    def test_exploration_exploitation(self):
        """Test that bandit explores all arms initially"""
        available = list(NotificationChannel)
        
        # Run multiple selections
        selections = []
        for _ in range(100):
            channel = self.bandit.select_channel(available)
            selections.append(channel)
            self.bandit.update(channel, np.random.random(), available)
        
        # Check that all channels were tried at least once
        unique_channels = set(selections)
        self.assertEqual(len(unique_channels), 4)
    
    def test_get_statistics(self):
        """Test statistics retrieval"""
        stats = self.bandit.get_statistics()
        self.assertEqual(len(stats), 4)
        self.assertIn('sms', stats)
        self.assertIn('success_rate', stats['sms'])


class TestEpsilonGreedyBandit(unittest.TestCase):
    """Test EpsilonGreedyBandit algorithm"""
    
    def setUp(self):
        """Set up test bandit"""
        channels = list(NotificationChannel)
        self.bandit = EpsilonGreedyBandit(channels=channels, epsilon=0.1)
    
    def test_initialization(self):
        """Test bandit initialization"""
        self.assertEqual(len(self.bandit.arms), 4)
        self.assertEqual(self.bandit.epsilon, 0.1)
        self.assertEqual(self.bandit.total_time, 0)
    
    def test_select_channel(self):
        """Test channel selection"""
        available = list(NotificationChannel)
        selected = self.bandit.select_channel(available)
        self.assertIn(selected, available)


class TestNotificationEnvironment(unittest.TestCase):
    """Test NotificationEnvironment"""
    
    def setUp(self):
        """Set up test environment"""
        self.env = NotificationEnvironment(seed=42)
    
    def test_initialization(self):
        """Test environment initialization"""
        self.assertIsNotNone(self.env.base_success_rates)
        self.assertEqual(len(self.env.base_success_rates), 4)
    
    def test_get_available_channels(self):
        """Test getting available channels"""
        available = self.env.get_available_channels('morning')
        self.assertIsInstance(available, list)
        self.assertGreater(len(available), 0)
    
    def test_get_reward(self):
        """Test reward generation"""
        reward = self.env.get_reward(
            NotificationChannel.SMS, 
            'morning', 
            'standard'
        )
        self.assertIn(reward, [0.0, 1.0])
    
    def test_time_of_day(self):
        """Test time of day calculation"""
        self.assertEqual(self.env.get_time_of_day(8), 'morning')
        self.assertEqual(self.env.get_time_of_day(14), 'afternoon')
        self.assertEqual(self.env.get_time_of_day(20), 'evening')
        self.assertEqual(self.env.get_time_of_day(2), 'night')
    
    def test_user_segment(self):
        """Test user segment generation"""
        segment = self.env.get_user_segment(0)
        self.assertIn(segment, ['standard', 'premium', 'young'])


class TestBankingScenarios(unittest.TestCase):
    """Test banking scenario definitions"""
    
    def test_transaction_alert(self):
        """Test transaction alert scenario"""
        scenario = BankingScenario.transaction_alert()
        self.assertEqual(scenario['priority'], 'high')
        self.assertIn(NotificationChannel.PUSH, scenario['preferred_channels'])
    
    def test_security_alert(self):
        """Test security alert scenario"""
        scenario = BankingScenario.security_alert()
        self.assertEqual(scenario['priority'], 'critical')
        self.assertEqual(scenario['max_delay'], 30)


class IntegrationTest(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def test_complete_training_cycle(self):
        """Test a complete training cycle"""
        # Setup
        channels = list(NotificationChannel)
        bandit = SleepingBandit(channels=channels)
        env = NotificationEnvironment(seed=42)
        
        # Run training episodes
        num_episodes = 100
        for episode in range(num_episodes):
            time_of_day = env.get_time_of_day(episode)
            available = env.get_available_channels(time_of_day)
            
            selected = bandit.select_channel(available)
            reward = env.get_reward(selected, time_of_day, 'standard')
            bandit.update(selected, reward, available)
        
        # Verify training results
        self.assertEqual(bandit.total_time, num_episodes)
        stats = bandit.get_statistics()
        
        # Check that at least some arms were pulled
        total_pulls = sum(stats[ch.value]['total_pulls'] for ch in NotificationChannel)
        self.assertEqual(total_pulls, num_episodes)
    
    def test_channel_preference_learning(self):
        """Test that bandit learns channel preferences"""
        channels = list(NotificationChannel)
        bandit = SleepingBandit(channels=channels)
        
        # Create biased environment where SMS always succeeds
        class BiasedEnv:
            def get_available_channels(self, time):
                return channels
            
            def get_reward(self, channel, time, segment):
                return 1.0 if channel == NotificationChannel.SMS else 0.0
        
        env = BiasedEnv()
        
        # Train
        for _ in range(1000):
            available = env.get_available_channels('morning')
            selected = bandit.select_channel(available)
            reward = env.get_reward(selected, 'morning', 'standard')
            bandit.update(selected, reward, available)
        
        # Verify SMS has highest success rate
        best_channel, _ = bandit.get_best_channel()
        self.assertEqual(best_channel, NotificationChannel.SMS)


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBanditArm))
    suite.addTests(loader.loadTestsFromTestCase(TestSleepingBandit))
    suite.addTests(loader.loadTestsFromTestCase(TestEpsilonGreedyBandit))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationEnvironment))
    suite.addTests(loader.loadTestsFromTestCase(TestBankingScenarios))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
