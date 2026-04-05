import pika
import requests
import json
import os
import time

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL', 'YOUR_OUTSYSTEMS_URL_HERE')

def callback(ch, method, properties, body):
    payload = json.loads(body)
    print(f"[WORKER] Received message for Customer ID: {payload.get('customer_id')}", flush=True)

    try:
        # Send it to OutSystems
        response = requests.post(NOTIFICATION_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("[WORKER] Successfully sent to OutSystems. Acknowledging message.", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag) # Tell RabbitMQ to delete the message
        else:
            print(f"[WORKER] OutSystems Error {response.status_code}. Requeueing...", flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    except Exception as e:
        print(f"[WORKER] Network error: {str(e)}. Requeueing...", flush=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

# Wait a moment for RabbitMQ to start up
time.sleep(10)

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue='notifications_queue', durable=True)

# Tell RabbitMQ to only give this worker 1 message at a time
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='notifications_queue', on_message_callback=callback)

print('[WORKER] Waiting for messages. To exit press CTRL+C', flush=True)
channel.start_consuming()