import websocket
import json
import threading
import time

ws = None  # global websocket instance
latest_message = None
ws_thread = None  # thread for websocket connection
running = False  # control flag for thread
connection_event = threading.Event()  # event to signal connection status
data = None

# 4 functions for handling websocket events, aka callback functions
def on_message(ws, message):
    """Handle incoming WebSocket messages."""
    global data
    try:
        data = json.loads(message)
        #print(data)
    except json.JSONDecodeError:
        print("Invalid message received:", message)

'''
def process_message():
    """Process the latest message."""
    global data
    print(data)
    # Add any additional processing logic here
'''

def get_data():
    return data

def on_error(ws, error):
    """Handle WebSocket errors."""
    print("WebSocket Error:", error)
    connection_event.set()  # Signal that an error occurred

def on_close(ws, close_status_code, close_msg):
    """Handle WebSocket closure."""
    print("WebSocket Closed")
    connection_event.set()  # Signal that the connection was closed

def on_open(ws):
    """Handle WebSocket connection."""
    print("WebSocket Connected")
    connection_event.set()  # Signal that the connection was successful

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
        ws.run_forever()

def connect_websocket():
    """Start the WebSocket connection in a new thread."""
    global ws_thread, running, ws
    if ws_thread and ws_thread.is_alive():
        return "Already Connected"
    
    # Start the WebSocket connection
    running = True
    connection_event.clear()  # Clear the event before starting the connection
    ws_thread = threading.Thread(target=run_websocket, daemon=True)
    ws_thread.start()

    # Check for valid connection
    if not connection_event.wait(timeout=2.5):
        running = False
        if ws and ws.sock and ws.sock.connected:
            ws.close()
        return "Failed to connect"

    return "Connected"

def disconnect_websocket():
    """Disconnect from the WebSocket."""
    global ws, running
    running = False
    if ws and ws.sock and ws.sock.connected:
        ws.close()
        print("Disconnected from WebSocket")
    if ws_thread:
        ws_thread.join()  # Wait for the thread to finish
    
    return "Disconnected"

if __name__ == "__main__":
    while True:
        connect_websocket()