import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='task_queue')
channel.basic_publish(exchange='',
                      routing_key='task_queue',
                      body='Hello World!',
                      properties=pika.BasicProperties(
                          delivery_mode=pika.DeliveryMode.Persistent
                      ))
print(" [x] Sent 'Hello World!'")
connection.close()
