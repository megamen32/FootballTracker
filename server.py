#TensorFlow can train and process very large models, whereas TensorFlow.js is limited to smaller models due to the performance limitations of JavaScript engines.
#JavaScript engines are less powerful compared to specialised machine learning frameworks and hardware accelerators such as GPUs or TPUs. This means that TensorFlow.js is usually suitable for smaller models due to the limited processing power and memory of JavaScript engines.

#Therefore, TensorFlow is recommended for projects where large models need to be trained or complex calculations need to be performed, while TensorFlow.js is better suited for applications that use smaller models and are intended to run in web browsers or JavaScript environments.
from flask import Flask, jsonify,send_file,send_from_directory
import threading
from io import BytesIO
# Assuming previous classes ModelHandler and ImageHandler are defined as shown above
import image_handler
from app import MainApp

# Flask server
server = Flask(__name__)


@server.route("/command/<action>", methods=["GET"])
def server_command(action):
    if action == "exit":
        main_app.while_loop = False
        return jsonify(message="stop Server")
    elif action == "pusto":
        pusto = image_handler.ImageHandler.read_image_file(main_app.json_input.pusto)
        return jsonify(message="pusto update")
    elif action == "pause":
        main_app.pause_state = True
        return jsonify(message="pause on")
    elif action == "start":
        main_app.pause_state = False
        return jsonify(message="pause off")
    else:
        return jsonify(message="Unknown command")
@server.route('/canvas_image', methods=['GET'])
def serve_canvas():
    # Convert the Pillow Image to BytesIO (in-memory byte stream)
    byte_io = BytesIO()
    main_app.canvFull.save(byte_io, 'PNG')  # Save as PNG
    byte_io.seek(0)
    return send_file(byte_io, mimetype='image/png')

def run_server():
    server.run(port=5000)

if __name__ == "__main__":
    main_app = MainApp()
    model_name = "model"  # Replace with your actual model path

    # Start Flask server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    # Start main loop in the main thread
    main_app.load_json('json_input.json')
    main_app.main_loop(model_name)
