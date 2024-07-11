import socket
import threading

clients = {}
client_names = {}

def load_accounts(filename="theaccounts.txt"):
    accounts = {}
    with open(filename, 'r') as file:
        for line in file:
            username, password = line.strip().split('::')
            accounts[username] = password
    return accounts

def authenticate(client_socket):
    client_socket.send(b"Enter your username: ")
    username = client_socket.recv(1024).strip().decode()
    client_socket.send(b"Enter your password: ")
    password = client_socket.recv(1024).strip().decode()
    accounts = load_accounts()
    if username in accounts and accounts[username] == password:
        client_socket.send(b"Authentication successful")
        return username
    else:
        client_socket.send(b"Authentication failed")
        client_socket.close()
        return None

def handle_client(client_socket, addr):
    username = authenticate(client_socket)
    if not username:
        return

    clients[username] = client_socket
    client_names[client_socket] = username
    welcome_message = f'{username} has joined the chat.\n'
    print(welcome_message)
    broadcast_message(welcome_message.encode(), client_socket)
    
    try:
        while True:
            message = client_socket.recv(1024).decode()
            if message:
                print(f'Received from {username}: {message}')
                if message.startswith("@"):
                    target_username, msg = message.split(" ", 1)
                    target_username = target_username[1:]
                    send_message_to_client(msg, username, target_username)
                elif message.startswith("FILE"):
                    handle_file_transfer(message, client_socket)
                else:
                    broadcast_message(f"{username}: {message}".encode(), client_socket)
            else:
                client_socket.close()
                remove_client(client_socket)
                break
    except:
        client_socket.close()
        remove_client(client_socket)

def broadcast_message(message, sender_socket):
    for client in clients.values():
        if client != sender_socket:
            try:
                client.send(message)
            except:
                client.close()
                remove_client(client)

def send_message_to_client(message, sender_username, target_username):
    if target_username in clients:
        target_socket = clients[target_username]
        try:
            target_socket.send(f"{sender_username} to {target_username}: {message}".encode())
        except:
            target_socket.close()
            remove_client(target_socket)
    else:
        sender_socket = clients[sender_username]
        sender_socket.send(f"User {target_username} not found.".encode())

def handle_file_transfer(message, client_socket):
    parts = message.split(" ", 2)
    if len(parts) < 3:
        client_socket.send(b"Invalid FILE command")
        return

    _, target_username, file_name = parts
    file_data = client_socket.recv(1024 * 1024)
    if target_username in clients:
        target_socket = clients[target_username]
        try:
            target_socket.send(f"FILE {file_name}".encode())
            target_socket.send(file_data)
        except:
            target_socket.close()
            remove_client(target_socket)
    else:
        client_socket.send(f"User {target_username} not found.".encode())

def remove_client(client_socket):
    username = client_names.get(client_socket)
    if username:
        del clients[username]
        del client_names[client_socket]
        print(f"{username} has left the chat.")
        broadcast_message(f"{username} has left the chat.".encode(), client_socket)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # use this line if you want to use the default IP address of the machine
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)

    # use this line if you want to specify the IP address manually
    # host = '192.168.1.105'
    # host = 'localhost'

    # specify the port number
    port = 12345

    server_socket.bind((host, port))

    # allow 5 clients to queue
    server_socket.listen(5)

    print(f'Server started at {host}:{port}')

    def accept_connections():
        while True:
            client_socket, addr = server_socket.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_handler.start()

    accept_thread = threading.Thread(target=accept_connections)
    accept_thread.start()

    while True:
        command = input("Type 'STOP' to shut down the server: ")
        if command.strip().upper() == 'STOP':
            break

    server_socket.close()
    print('Server shut down.')

if __name__ == '__main__':
    start_server()
