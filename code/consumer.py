# kafka_image_consumer.py (on Machine C)
from kafka import KafkaConsumer
import cv2
import numpy as np

KAFKA_SERVER = '172.20.242.162:9092'  # Machine D

consumer = KafkaConsumer(
    'image_topic',
    bootstrap_servers=KAFKA_SERVER,
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

print("Waiting for image from Kafka...")

for message in consumer:
    img_bytes = message.value
    img_np = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

    cv2.imshow("Received Image", img)
    cv2.imwrite("received_image.jpg", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    break  # remove for continuous streaming
