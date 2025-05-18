# image_sender.py
import socket
import cv2
import struct

# Connect to server (receiver)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.76.1', 9999))  # Replace 'receiver_ip' with actual IP

# Read and encode image
img = cv2.imread('image.jpg')
_, img_encoded = cv2.imencode('.jpg', img)
img_bytes = img_encoded.tobytes()

# Send length of image
client_socket.sendall(struct.pack(">L", len(img_bytes)))

# Send image data
client_socket.sendall(img_bytes)
print("Image sent.")
client_socket.close()
