#!/usr/bin/env python3
"""
Feedback Worker - Consumes feedback events and updates the ML model.
"""

from datetime import datetime

from message_queue import MessageQueueConsumer
from config import Config
from bandit_algorithm import MultiArmedBandit


class FeedbackWorker:
    """Worker that processes feedback and updates ML model."""
    
    def __init__(self):
        self.bandit = MultiArmedBandit(
            strategy=Config.BANDIT_STRATEGY,
            epsilon=Config.BANDIT_EPSILON,
            model_path=Config.BANDIT_MODEL_PATH
        )
        self.update_counter = 0
        self.save_interval = 10  # Save model every 10 updates
    
    def process_feedback(self, feedback_data: dict):
        """Process feedback and update ML model."""
        notification_id = feedback_data.get('notification_id')
        template_id = feedback_data.get('template_id')
        user_id = feedback_data.get('user_id')
        reward = feedback_data.get('reward', 0.0)
        was_tapped = feedback_data.get('was_tapped', False)
        
        print(f"\n[{datetime.now()}] Processing feedback:")
        print(f"  Notification ID: {notification_id}")
        print(f"  Template: {template_id}")
        print(f"  User: {user_id}")
        print(f"  Was Tapped: {was_tapped}")
        print(f"  Reward: {reward}")
        
        try:
            # Update bandit model
            self.bandit.update_reward(template_id, user_id, reward)
            self.update_counter += 1
            
            # Save model periodically
            if self.update_counter % self.save_interval == 0:
                self.bandit.save_model()
                print(f"  → Model saved (updates: {self.update_counter})")
            else:
                print(f"  → Model updated (updates: {self.update_counter})")
            
        except Exception as e:
            print(f"  Status: ✗ Failed - {str(e)}")
            raise
    
    def start(self):
        """Start the feedback worker."""
        print("=" * 60)
        print("Feedback Worker Starting")
        print(f"Queue: {Config.FEEDBACK_QUEUE}")
        print(f"Bandit Strategy: {Config.BANDIT_STRATEGY}")
        print(f"Model Path: {Config.BANDIT_MODEL_PATH}")
        print("=" * 60)
        
        # Load existing model
        if self.bandit.load_model():
            stats = self.bandit.get_statistics()
            print(f"Loaded model: {stats['total_pulls']} pulls, {stats['unique_arms']} arms")
        
        # Create consumer
        consumer = MessageQueueConsumer(
            queue_name=Config.FEEDBACK_QUEUE,
            callback=self.process_feedback
        )
        
        try:
            consumer.connect()
            consumer.start_consuming()
        except KeyboardInterrupt:
            print("\nShutting down feedback worker...")
            # Save model before exiting
            self.bandit.save_model()
            print("Model saved.")
            consumer.close()
        except Exception as e:
            print(f"Feedback worker error: {e}")
            self.bandit.save_model()
            consumer.close()
            raise


if __name__ == '__main__':
    worker = FeedbackWorker()
    worker.start()
