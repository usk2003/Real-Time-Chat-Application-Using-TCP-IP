#server.py

import socket
import threading
import uuid

clients = []
clients_lock = threading.Lock()
chat_history = []  # Store the recent chat messages
history_lock = threading.Lock()

passkey = ""

def generate_passkey():
    # Generate a dynamic passkey (can use any method, here using UUID)
    return uuid.uuid4().hex[:8]  # Generate an 8-character passkey

def handle_client(client_socket, client_address):
    global passkey
    send_chat_history(client_socket)
    try:
        # Receive the username and passkey
        data = client_socket.recv(4096).decode('utf-8')
        username, client_passkey = data.split()

        if client_passkey != passkey:
            client_socket.send("Invalid passkey! Connection closed.".encode('utf-8'))
            client_socket.close()
            return

        # Broadcast that the user has joined
        broadcast(client_socket, f"{username} joined the chat.")
        #save_message(f"{username} joined the chat.")

        # Handle incoming messages
        while True:
            message = client_socket.recv(4096).decode('utf-8')
            if not message:
                break

            # Detect file transfer
            if message.startswith("[FILE_TRANSFER]"):
                handle_file_transfer(client_socket, username)
            else:
                broadcast(client_socket, f"{username}: {message}")
                # save_message(f"{username}: {message}")
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    except (ConnectionResetError, socket.error) as e:
        print(f"Connection error with {client_address}: {e}")
    finally:
        disconnect_client(client_socket, username)


# Broadcast function
def broadcast(sender_socket, message):
    if message.strip():  # Only process non-empty messages
        with clients_lock:
            for client in clients:
                if client != sender_socket:
                    try:
                        client.send(message.encode('utf-8'))
                    except Exception as e:
                        print(f"Error broadcasting message: {e}")
        save_message(message)  # Save only valid messages

def handle_file_transfer(client_socket, username):
    try:
        # Receive the file name
        file_name = client_socket.recv(4096).decode('utf-8')
        file_path = f"received_{file_name}"

        # Open file for writing
        with open(file_path, "wb") as file:
            while True:
                chunk = client_socket.recv(4096)
                if chunk == b"[FILE_END]":
                    break
                file.write(chunk)

        # Notify all clients about the received file
        broadcast(client_socket, f"{username} sent a file: {file_name}")
        save_message(f"{username} sent a file: {file_name}")
    except Exception as e:
        print(f"Error handling file transfer from {username}: {e}")

# Send chat history to new clients
def send_chat_history(client_socket):
    with history_lock:  # Ensure thread-safe access to history
        if chat_history:
            history_data = "[HISTORY]\n" + "\n".join(chat_history)
            client_socket.send(history_data.encode('utf-8'))

def save_message(message):
    with history_lock:
        chat_history.append(message)
        if len(chat_history) > 50:
            chat_history.pop(0)  # Keep only the last 50 messages

def disconnect_client(client_socket, username):
    with clients_lock:
        if client_socket in clients:
            clients.remove(client_socket)

    if username:  # Ensure the username is valid
        departure_message = f"{username} left the chat."
        broadcast(None, departure_message)
    else:
        print("Anonymous user disconnected (no username provided).")

    try:
        client_socket.close()
    except Exception as e:
        print(f"Error closing client socket: {e}")

    print(f"{username if username else 'A client'} disconnected.")

def start_server():
    global passkey
    passkey = generate_passkey()  # Generate a new passkey when server starts
    print(f"Server passkey: {passkey}")  # Show passkey for the admin
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345))  # Listen on all interfaces
    server_socket.listen(5)

    ip_address = socket.gethostbyname(socket.gethostname())
    print(f"Chat Server started, listening on IP {ip_address}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address[0]}:{client_address[1]}")
            with clients_lock:
                clients.append(client_socket)
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address), daemon=True)
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server_socket.close()
        # Ensure to close all client connections before exiting
        with clients_lock:
            for client in clients:
                client.close()

if __name__ == "__main__":
    start_server()