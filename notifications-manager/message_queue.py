import pika
import json
from typing import Callable
from config import Config


class MessageQueueProducer:
    """Producer for sending messages to RabbitMQ."""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()
    
    def connect(self):
        """Establish connection to RabbitMQ."""
        credentials = pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=Config.RABBITMQ_HOST,
            port=Config.RABBITMQ_PORT,
            virtual_host=Config.RABBITMQ_VHOST,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declare queues
        self.channel.queue_declare(queue=Config.NOTIFICATION_QUEUE, durable=True)
        self.channel.queue_declare(queue=Config.FEEDBACK_QUEUE, durable=True)
    
    def publish_notification(self, notification_data: dict):
        """Publish a notification to the queue."""
        message = json.dumps(notification_data)
        self.channel.basic_publish(
            exchange='',
            routing_key=Config.NOTIFICATION_QUEUE,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type='application/json'
            )
        )
    
    def publish_feedback(self, feedback_data: dict):
        """Publish feedback to the feedback queue."""
        message = json.dumps(feedback_data)
        self.channel.basic_publish(
            exchange='',
            routing_key=Config.FEEDBACK_QUEUE,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type='application/json'
            )
        )
    
    def close(self):
        """Close the connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


class MessageQueueConsumer:
    """Consumer for processing messages from RabbitMQ."""
    
    def __init__(self, queue_name: str, callback: Callable):
        self.queue_name = queue_name
        self.callback = callback
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ."""
        credentials = pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=Config.RABBITMQ_HOST,
            port=Config.RABBITMQ_PORT,
            virtual_host=Config.RABBITMQ_VHOST,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declare queue
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.channel.basic_qos(prefetch_count=1)
    
    def start_consuming(self):
        """Start consuming messages."""
        def on_message(ch, method, properties, body):
            try:
                data = json.loads(body)
                self.callback(data)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing message: {e}")
                # Reject and don't requeue if there's an error
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=on_message
        )
        
        print(f' [*] Waiting for messages in {self.queue_name}. To exit press CTRL+C')
        self.channel.start_consuming()
    
    def close(self):
        """Close the connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


# Global producer instance
mq_producer = MessageQueueProducer()
