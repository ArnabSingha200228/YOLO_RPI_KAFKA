import os
from ultralytics import YOLO
import socket
import struct
import cv2  # Ensure OpenCV is imported

# Connect to server (receiver)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.76.1', 9999))  # Replace 'receiver_ip' with actual IP

# Load YOLOv8 model
model = YOLO("best.pt")  # Replace with your model name if different

# Input and output directories
image_dir = "furniture_image"  # Folder containing input images

# Check if the image directory exists
if not os.path.isdir(image_dir):
    print(f"Directory not found: {image_dir}")
    exit()

# Get all image files in the directory
image_files = [f for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]

# Process each image one by one
for image_file in sorted(image_files):
    image_path = os.path.join(image_dir, image_file)
    image = cv2.imread(image_path)

    if image is None:
        print(f"Skipping invalid image: {image_file}")
        continue

    # Run YOLO detection
    results = model(image)

    # Save annotated image to output directory
    for result in results:
        annotated_image = result.plot()  # Get the image with annotations
        _, img_encoded = cv2.imencode('.jpg', annotated_image)  # Encode the resultant image
        img_bytes = img_encoded.tobytes()

        # Send length of image
        client_socket.sendall(struct.pack(">L", len(img_bytes)))

        # Send image data
        client_socket.sendall(img_bytes)

    print(f"✅ Processed and saved: {image_file}")

client_socket.close()
print("🎉 All images are processed and sent to   producer")

