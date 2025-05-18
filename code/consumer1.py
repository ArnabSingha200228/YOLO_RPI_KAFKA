# kafka_image_consumer.py
import os
import cv2
import numpy as np
from kafka import KafkaConsumer
from datetime import datetime

KAFKA_SERVER = '172.20.242.162:9092'  # Machine D
SAVE_DIR = 'received_images'

# Create save directory if it doesn't exist
os.makedirs(SAVE_DIR, exist_ok=True)

consumer = KafkaConsumer(
    'image_topic',
    bootstrap_servers=KAFKA_SERVER,
    auto_offset_reset='latest',
    enable_auto_commit=True
)

print("Listening for images on Kafka topic 'image_topic'...")

try:
    for message in consumer:
        img_bytes = message.value
        img_np = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        if img is not None:
            # Use timestamp to avoid overwriting
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            filename = f'image_{timestamp}.jpg'
            path = os.path.join(SAVE_DIR, filename)
            cv2.imwrite(path, img)
            print(f"Saved: {filename}")
        else:
            print("Received an invalid image.")

except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    consumer.close()

