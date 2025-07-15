from flask import Flask, render_template, request
from websocket_server import WebsocketServer
import threading
import json
import os

app = Flask(__name__)
clients = []
MESSAGE_FILE = "last_message.json"

# WebSocket send function
def send_to_all(msg_obj):
    message = json.dumps(msg_obj)
    print("Sending to ESP:", message)

    if not clients:
        print("No clients connected. Saving message to file.")
        with open(MESSAGE_FILE, "w") as f:
            json.dump(msg_obj, f)
        return

    for client in clients:
        try:
            server.send_message(client, message)
        except Exception as e:
            print("Failed to send to a client:", e)

# WebSocket server event handlers
def new_client(client, server):
    print(f"[WS] Client connected: {client['id']}")
    clients.append(client)

    # Check if there's a saved message
    if os.path.exists(MESSAGE_FILE):
        try:
            with open(MESSAGE_FILE, "r") as f:
                saved_msg = json.load(f)
            print(f"Sending stored message to client {client['id']}: {saved_msg}")
            server.send_message(client, json.dumps(saved_msg))
            os.remove(MESSAGE_FILE)
        except Exception as e:
            print("Error reading/sending stored message:", e)

def client_left(client, server):
    print(f"[WS] Client disconnected: {client['id']}")
    if client in clients:
        clients.remove(client)

def message_received(client, server, message):
    print(f"[WS] Received from client: {message}")

# Start WebSocket server in background thread
def start_websocket():
    global server
    server = WebsocketServer(host='0.0.0.0', port=8765)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    server.run_forever()

threading.Thread(target=start_websocket, daemon=True).start()

# HTTP Routes
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("message", "")
        size = int(request.form.get("size", 2))
        x = int(request.form.get("x", 0))
        y = int(request.form.get("y", 0))

        json_payload = {
            "text": text,
            "size": size,
            "pos": [x, y]
        }

        send_to_all(json_payload)

        return render_template("index.html", sent=True, msg=text, size=size, x=x, y=y)

    # On GET, provide defaults
    return render_template("index.html", sent=False, msg="", size=2, x=0, y=0)

if __name__ == '__main__':
    print("[HTTP] Flask running on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
