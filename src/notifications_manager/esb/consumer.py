"""
ESB Consumer - Polls priority queue and processes notifications
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
import requests
from datetime import datetime

from .esb_service import ESBService

logger = logging.getLogger(__name__)


class ESBConsumer:
    """
    Consumer that continuously polls the priority queue
    and processes notifications through the ESB
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.esb_service = ESBService(config.get('esb', {}))
        self.api_base_url = config.get('api_base_url', 'http://localhost:8080')
        self.poll_interval = config.get('poll_interval', 2.0)
        self.batch_size = config.get('batch_size', 10)
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"ESB Consumer initialized (poll_interval={self.poll_interval}s, batch_size={self.batch_size})")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def start(self):
        """Start consuming notifications from the queue"""
        self.running = True
        logger.info("ESB Consumer started")
        
        print("\n" + "="*70)
        print("🚀 ESB CONSUMER ACTIVE")
        print("="*70)
        print(f"📡 Polling queue every {self.poll_interval}s")
        print(f"📦 Batch size: {self.batch_size}")
        print(f"🔗 API: {self.api_base_url}")
        print("="*70 + "\n")
        
        consecutive_empty = 0
        
        try:
            while self.running:
                try:
                    # Dequeue notifications from priority queue
                    notifications = await self._dequeue_batch()
                    
                    if notifications:
                        consecutive_empty = 0
                        logger.info(f"Dequeued {len(notifications)} notifications")
                        
                        # Process each notification
                        tasks = [
                            self.esb_service.process_notification(notif)
                            for notif in notifications
                        ]
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Log results
                        successful = sum(1 for r in results if not isinstance(r, Exception) and r.success)
                        failed = len(results) - successful
                        
                        print(f"✅ Processed {len(notifications)} notifications: "
                              f"{successful} successful, {failed} failed")
                        
                    else:
                        consecutive_empty += 1
                        if consecutive_empty % 10 == 1:  # Log every 10th empty poll
                            logger.debug("Queue is empty, waiting...")
                    
                    # Wait before next poll
                    await asyncio.sleep(self.poll_interval)
                    
                except Exception as e:
                    logger.error(f"Error in consumer loop: {e}", exc_info=True)
                    await asyncio.sleep(self.poll_interval)
        
        finally:
            await self.esb_service.shutdown()
            logger.info("ESB Consumer stopped")
    
    async def _dequeue_batch(self) -> list:
        """Dequeue a batch of notifications from the API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/queue/dequeue",
                params={'count': self.batch_size},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('notifications', [])
            elif response.status_code == 404:
                # Queue is empty
                return []
            else:
                logger.warning(f"Dequeue failed with status {response.status_code}")
                return []
        
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to API - is it running?")
            return []
        except Exception as e:
            logger.error(f"Error dequeuing notifications: {e}")
            return []
    
    def get_status(self) -> dict:
        """Get consumer status"""
        return {
            'running': self.running,
            'poll_interval': self.poll_interval,
            'batch_size': self.batch_size,
            'api_base_url': self.api_base_url,
            'esb_health': self.esb_service.get_health_status()
        }


async def main():
    """Main entry point for ESB consumer"""
    # Load configuration
    config = {
        'api_base_url': 'http://localhost:8080',
        'poll_interval': 2.0,
        'batch_size': 10,
        'esb': {
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0
            },
            'providers': {
                'sms': {'enabled': True},
                'whatsapp': {'enabled': True},
                'email': {'enabled': True},
                'push': {'enabled': True}
            }
        }
    }
    
    consumer = ESBConsumer(config)
    await consumer.start()


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run consumer
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 ESB Consumer stopped by user")
