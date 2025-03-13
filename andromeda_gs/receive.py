import websocket
import json
import threading
import time

ws = None  # global websocket instance
latest_message = None
ws_thread = None # thread for websocket connection
running = False # control flag for thread
connection_event = threading.Event()  # event to signal connection status
data = None

# 4 functions for handling websocket events, aka callback functions
def on_message(ws, message):
    """Handle incoming WebSocket messages."""
    global data
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print("Invalid message received:", message)

def process_message():
    """Process the latest message."""
    global data
    print(data)
    # Add any additional processing logic here

def on_error(ws, error):
    """Handle WebSocket errors."""
    print("WebSocket Error:", error)

def on_close(ws, close_status_code, close_msg):
    """Handle WebSocket closure."""
    print("WebSocket Closed")

def on_open(ws):
    """Handle WebSocket connection."""
    print("WebSocket Connected")
    connection_event.set()

# functions to manage the websocket connection
def run_websocket():
    """WebSocket connection loop in a separate thread."""
    global ws, running
    ws_url = "ws://192.168.4.1/ws"
    ws = websocket.WebSocketApp(
        ws_url, 
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    while running:  # Keep running while the flag is True
        #ws.run_forever(ping_interval=1, ping_timeout=0.5)
        ws.run_forever()

def connect_websocket():
    """Start the WebSocket connection in a new thread."""
    
    # Check if the WebSocket is already connected
    global ws_thread, running
    if ws_thread and ws_thread.is_alive():
        return "Already Connected"
    
    # Start the WebSocket connection
    running = True
    ws_thread = threading.Thread(target=run_websocket, daemon=True)
    ws_thread.start()

    # Check for valid connection
    if not connection_event.wait(timeout=2.5):
        running = False
        return "Failed to connect: Timeout"

    return "Connected"

def disconnect_websocket():
    """Disconnect from the WebSocket."""
    global ws, running
    running = False
    if ws:
        ws.close()
        print("Disconnected from WebSocket")
    if ws_thread:
        ws_thread.join() # Wait for the thread to finish
    
    return "Disconnected"

if __name__ == "__main__":
    try:
        connect_websocket()
        while True:
            process_message()
    except KeyboardInterrupt:
            disconnect_websocket()