from flask import Flask, send_from_directory, jsonify
import os
import random
app = Flask(__name__)

# Change this to the path of your directory containing images
IMAGE_FOLDER = "./imgs"

@app.route('/images', methods=['GET'])
def serve_random_image():
    """Serve a random image from the IMAGE_FOLDER."""
    files = os.listdir(IMAGE_FOLDER)
    images = [f for f in files if f.endswith(('jpeg', 'png', 'jpg', 'gif'))]
    if not images:
        return "No images found", 404
    selected_image = random.choice(images)
    return send_from_directory(IMAGE_FOLDER, selected_image)

@app.route('/images/<filename>', methods=['GET'])
def serve_image(filename):
    """Serve an image from the IMAGE_FOLDER."""
    return send_from_directory(IMAGE_FOLDER, filename)

if __name__ == '__main__':
    app.run(port=5001)
