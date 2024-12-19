#client.py

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog, simpledialog, END, messagebox

# Global variables
client_socket = None
username = None
is_running = True

def receive_messages(client_socket):
    try:
        while is_running:
            message = client_socket.recv(4096).decode('utf-8')
            if not message:
                break
            
            if message.startswith("[HISTORY]"):
                history_lines = message.replace("[HISTORY]", "").strip().splitlines()
                display_message("[Chat History]\n", is_history=True)
                for line in history_lines:
                    display_message(line, is_history=True)
                display_message("\n[End of Chat History]", is_history=True) #\n before if want

            elif message.startswith("[FILE_TRANSFER]"):
                file_name = client_socket.recv(4096).decode('utf-8')
                with open(file_name, "wb") as file:
                    while True:
                        chunk = client_socket.recv(4096)
                        if chunk == b"[FILE_END]":
                            break
                        file.write(chunk)
                display_message(f"Received file: {file_name}")
            else:
                display_message(message.strip())  # Regular messages
    except (ConnectionResetError, socket.error):
        if is_running:
            display_message("Connection lost with the server.")
    except Exception as e:
        if is_running:
            display_message(f"Unexpected error: {e}")
    finally:
        close_client()


def send_message(event=None):
    try:
        message = input_box.get().strip()
        if message:
            formatted_message = f"You: {message}"
            client_socket.send(message.encode('utf-8'))
            display_message(formatted_message)
            input_box.delete(0, END)
    except Exception as e:
        display_message(f"Error sending message: {e}")

def display_message(message, is_history=False):
    """Display messages in the chat log, with optional styling for history."""
    chat_log.configure(state='normal')  # Temporarily enable editing
    
    if is_history:
        chat_log.insert(END, message + "\n", 'history_tag')  # Apply the history style
    else:
        chat_log.insert(END, message + "\n")  # Regular message styling
    
    chat_log.configure(state='disabled')  # Disable editing
    chat_log.see(END)  # Scroll to the latest message

def send_file():
    """Allow the user to select and send a file."""
    try:
        file_path = filedialog.askopenfilename()
        if file_path:
            # Inform the server that a file is being sent
            client_socket.send("[FILE_TRANSFER]".encode('utf-8'))

            # Send the file name and size
            file_name = file_path.split("/")[-1]
            client_socket.send(file_name.encode('utf-8'))

            # Read and send the file content in chunks
            with open(file_path, "rb") as file:
                while chunk := file.read(4096):
                    client_socket.send(chunk)
            
            client_socket.send(b"[FILE_END]")  # Indicate file transfer completion
            display_message(f"File '{file_name}' sent successfully.")
    except Exception as e:
        display_message(f"Error sending file: {e}")

def close_client():
    global client_socket, is_running
    is_running = False  # Signal threads to stop

    try:
        if client_socket:
            client_socket.close()
    except Exception as e:
        print(f"Error closing socket: {e}")
    finally:
        client_socket = None
        is_running = False  # Set to False when closing the client
        root.quit()  
        
    root.destroy()  # Destroy the window

def connect_to_server():
    global client_socket, username, passkey

    try:
        server_ip = server_ip_entry.get().strip()
        server_port = int(server_port_entry.get().strip())
        client_socket.connect((server_ip, server_port))

        username = username_entry.get().strip()
        passkey = passkey_entry.get().strip()  # Get passkey input
        if not username:
            username = "Anonymous"
        if not passkey:
            passkey = ""  # Default to empty if no passkey provided

        # Send username and passkey to the server
        client_socket.send(f"{username} {passkey}".encode('utf-8'))

        # Show chat frame
        server_frame.grid_forget()
        chat_frame.grid(row=0, column=0, sticky="NSEW")
        display_message(f"Welcome to the chat, {username}!")

        # Start receiving messages
        threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()
    except Exception as e:
        messagebox.showerror("Connection Error", f"Unable to connect: {e}")

def start_client():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Center and dynamic GUI adjustments
    window_width = 500
    window_height = 400
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_coord = (screen_width // 2) - (window_width // 2)
    y_coord = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x_coord}+{y_coord}")
    root.update()

def toggle_password_visibility():
    """Toggle the visibility of the passkey."""
    if show_password_var.get():
        passkey_entry.config(show="")
    else:
        passkey_entry.config(show="*")

def validate_password_length(new_value):
    """Validate the max length of the passkey."""
    return len(new_value) <= 8
#-------------------------------------------------------------
# Main GUI setup
root = tk.Tk()
root.title("Chat Client")
root.resizable(True, True)

# Frames for different UI states
server_frame = tk.Frame(root)
server_frame.grid(row=0, column=0, sticky="NSEW")

chat_frame = tk.Frame(root)
chat_frame.grid(row=0, column=0, sticky="NSEW")
chat_frame.grid_remove()  # Hide chat frame initially

# Configure grid weights for dynamic resizing
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
chat_frame.grid_rowconfigure(0, weight=1)  # Chat log row
chat_frame.grid_rowconfigure(1, weight=0)  # Input box row
chat_frame.grid_rowconfigure(2, weight=0)  # Buttons row
chat_frame.grid_columnconfigure(0, weight=1)  # Main column
chat_frame.grid_columnconfigure(1, weight=0)  # Buttons column


# Server frame layout with the "Connect" button mapped to the Enter key
for i in range(6):  # Increase the number of rows for more control
    server_frame.grid_rowconfigure(i, weight=1)  # Equal vertical spacing
server_frame.grid_columnconfigure(0, weight=1)  # Center alignment
server_frame.grid_columnconfigure(1, weight=2)  # Increase weight for input fields

# Server IP
tk.Label(server_frame, text="Server IP:", font=('Arial', 12)).grid(row=0, column=0, padx=10, pady=10, sticky="E")
server_ip_entry = tk.Entry(server_frame, width=30, font=('Arial', 12))
server_ip_entry.grid(row=0, column=1, padx=10, pady=10)
server_ip_entry.insert(0, "127.0.0.1")

# Server Port
tk.Label(server_frame, text="Server Port:", font=('Arial', 12)).grid(row=1, column=0, padx=10, pady=10, sticky="E")
server_port_entry = tk.Entry(server_frame, width=30, font=('Arial', 12))
server_port_entry.grid(row=1, column =1, padx=10, pady=10)
server_port_entry.insert(0, "12345")

# Username
tk.Label(server_frame, text="Username:", font=('Arial', 12)).grid(row=2, column=0, padx=10, pady=10, sticky="E")
username_entry = tk.Entry(server_frame, width=30, font=('Arial', 12))
username_entry.grid(row=2, column=1, padx=10, pady=10)

# Passkey
tk.Label(server_frame, text="Passkey:", font=('Arial', 12)).grid(row=3, column=0, padx=10, pady=10, sticky="E")
validate_cmd = (root.register(validate_password_length), '%P')  # Register validation command
passkey_entry = tk.Entry(server_frame, width=30, font=('Arial', 12), show="*", validate="key", validatecommand=validate_cmd)
passkey_entry.grid(row=3, column=1, padx=10, pady=10)

# Show passkey checkbox
show_password_var = tk.BooleanVar(value=False)
show_password_checkbox = tk.Checkbutton(server_frame, text="Show", variable=show_password_var, command=toggle_password_visibility)
show_password_checkbox.grid(row=3, column=2, sticky="W", padx=10, pady=5)

# Separator
separator = tk.Frame(server_frame, height=2, bd=1, relief="sunken")
separator.grid(row=5, column=0, columnspan=3, sticky="EW", pady=10)

# Connect button
connect_button = tk.Button(server_frame, text="Connect", font=('Arial', 12), bg="#4CAF50", fg="white", command=connect_to_server)
connect_button.grid(row=6, column=0, columnspan=3, pady=10, sticky="EW")

# Bind Enter key to trigger the connect_to_server function
passkey_entry.bind("<Return>", lambda event: connect_to_server())

# Optional: Adjust window size dynamically based on screen size and center it
window_width = 400
window_height = 350
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_coord = (screen_width // 2) - (window_width // 2)
y_coord = (screen_height // 2) - (window_height // 2)
root.geometry(f"{window_width}x{window_height}+{x_coord}+{y_coord}")

# Chat frame - Improved aesthetic version
chat_log = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, state='disabled', width=60, height=15, font=('Arial', 12), bg="#f4f4f4", fg="black", bd=2, relief="sunken")
chat_log.grid(row=0, column=0, columnspan=2, padx=10, pady=15, sticky="NSEW")

# Input box
input_box = tk.Entry(chat_frame, width=40, font=('Helvetica', 12,'italic'), relief="sunken", bd=2)
input_box.grid(row=1, column=0, padx=10, pady=10, sticky="EW")
input_box.bind("<Return>", send_message)

# Send button styling
send_button = tk.Button(chat_frame, text="Send", font=('Courier New', 12 , 'bold'), bg="#4CAF50", fg="white", relief="raised", bd=3, command=send_message)
send_button.grid(row=1, column=1, padx=10, pady=10)

# Exit button styling
exit_button = tk.Button(chat_frame, text="Exit", font=('Courier New', 12 , 'bold'), bg="#f44336", fg="white", relief="raised", bd=3, command=close_client)
exit_button.grid(row=2, column=1, padx=10, pady=10)

# Send File button
file_button = tk.Button(chat_frame, text="Send File", font=('Courier New', 12, 'bold'), bg="#2196F3", fg="white", relief="raised", bd=3, command=send_file)
file_button.grid(row=2, column=0, padx=10, pady=10, sticky="EW")

# Adjusting grid layout to make sure it resizes dynamically
chat_frame.grid_rowconfigure(0, weight=1)  # Chat log row should resize
chat_frame.grid_rowconfigure(1, weight=0)  # Input box row does not resize
chat_frame.grid_rowconfigure(2, weight=0)  # Button rows should remain fixed
chat_frame.grid_columnconfigure(0, weight=1)  # Input box and chat log will resize to fill width
chat_frame.grid_columnconfigure(1, weight=0)  # Buttons remain fixed width

# Optional: Add hover effects for buttons
def on_button_enter(event, color):
    event.widget.config(bg=color)

def on_button_leave(event, color):
    event.widget.config(bg=color)

# Add padding to buttons and input box for better spacing
send_button.config(padx=10, pady=5)
exit_button.config(padx=10, pady=5)

root.protocol("WM_DELETE_WINDOW", close_client)

if __name__ == "__main__":
    start_client()
    root.mainloop()