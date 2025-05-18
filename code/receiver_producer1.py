import socket
import struct
from kafka import KafkaProducer

KAFKA_SERVER = '172.20.242.162:9092'  # IP of Machine D (Kafka server)
KAFKA_TOPIC = 'image_topic'

# Set up Kafka producer
producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)

# Set up TCP socket server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 9999))  # Listen on all interfaces
server_socket.listen(5)

print("Waiting for incoming socket connections on port 9999...")

try:
    while True:
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")

        try:
            while True:
                # Receive 4-byte length prefix
                header = conn.recv(4)
                if not header:
                    print("Connection closed by client.")
                    break

                img_size = struct.unpack(">L", header)[0]

                # Receive the image data based on length
                img_data = b''
                while len(img_data) < img_size:
                    packet = conn.recv(4096)
                    if not packet:
                        break
                    img_data += packet

                if len(img_data) != img_size:
                    print("Incomplete image received. Skipping.")
                    continue

                # Send to Kafka
                producer.send(KAFKA_TOPIC, img_data)
                producer.flush()
                print(f"Sent image of size {img_size} bytes to Kafka.")
        except Exception as e:
            print(f"Error during socket communication: {e}")
        finally:
            conn.close()
            print("Socket connection closed.")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    server_socket.close()
    producer.close()
    print("Server and Kafka producer closed.")
