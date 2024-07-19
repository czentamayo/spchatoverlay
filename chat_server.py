import logging
import logging.config
import yaml

import os

log_directory = 'log'

# Create the log directory if it doesn't exist
if not os.path.exists(log_directory):
    os.makedirs(log_directory)


# Load logging configuration from YAML file
with open('server_logging.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Configure logging based on the YAML configuration
logging.config.dictConfig(config)

# Create logger
logger = logging.getLogger(__name__)

import traceback
import websockets
import aiofiles
import hashlib



class ChatServer:

    def __init__(self):
        self.clients = {}
        self.client_names = {}
        self.server_name = 's4'

    def set_exchange_server(self, exchange_server):
        self.exchange_server = exchange_server

    async def load_accounts(self, filename="theaccounts.txt"):
        accounts = {}
        async with aiofiles.open(filename, "r") as file:
            async for line in file:
                username, password = line.strip().split("::")
                accounts[username] = password
        return accounts

    async def hash_password(self, password):
        h = hashlib.sha256()
        h.update(password.encode())
        return h.hexdigest()

    async def authenticate(self, websocket):
        try:
            await websocket.send("Enter your username: ")
            username = (await websocket.recv()).strip()
            await websocket.send("Enter your password: ")
            password = (await websocket.recv()).strip()
            password = await self.hash_password(password)
            accounts = await self.load_accounts()
            if username in accounts and accounts[username] == password:
                await websocket.send("Authentication successful")
                user_pub_key = await websocket.recv()
                return username, user_pub_key
            else:
                await websocket.send("Authentication failed")
                return None, None
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected during authentication.")
            return None, None

    async def handle_client(self, websocket):
        username, user_pub_key = await self.authenticate(websocket)
        if not username:
            await websocket.close()
            return

        self.clients[username] = websocket
        self.client_names[websocket] = username
        await self.exchange_server.update_presence(
            "LOCAL", username, username, user_pub_key
        )
        welcome_message = f"{username} has joined the chat.\n"
        logger.info(welcome_message)
        await self.broadcast_message(welcome_message, websocket)

        try:
            while True:
                message = await websocket.recv()
                if message:
                    logger.debug(f"Received from {username}: {message}")
                    if message.startswith("@"):
                        message_array = message.split(" ", 1)
                        if len(message_array) < 2:
                            continue
                        target, msg = message.split(" ", 1)
                        target_array = target.split("@")
                        if len(target_array) < 3 or target_array[2] == self.server_name:
                            # local message, e.g. @c1, @c1@s4
                            await self.send_message_to_client(
                                msg, username, target_array[1]
                            )
                        else:
                            await self.exchange_server.send_message_to_server(
                                f"{username}@{self.server_name}",
                                target_array[2],
                                target_array[1],
                                msg
                            )
                    elif message.startswith("FILE"):
                        await self.handle_file_transfer(message, websocket)
                    else:
                        await self.broadcast_message(
                            f"{username}: {message}", websocket
                        )
                else:
                    await websocket.close()
                    await self.remove_client(websocket)
                    break
        except websockets.ConnectionClosed:
            await self.remove_client(websocket)
        except Exception as e:
            logger.error(f"Error: {e}")
            await self.remove_client(websocket)


    async def broadcast_message(self, message, sender_socket):
        for client in self.clients.values():
            if client != sender_socket:
                try:
                    await client.send(message)
                except:
                    await client.close()
                    await self.remove_client(client)


    async def broadcast_presence(self, presence_json):
        for client in self.clients.values():
            try:
                await client.send(presence_json)
            except:
                await client.close()
                await self.remove_client(client)


    async def send_message_to_client(self, message, sender_username, target_username):
        logger.info(f"sending to {target_username}")
        if target_username in self.clients:
            target_socket = self.clients[target_username]
            try:
                await target_socket.send(
                    f"@{sender_username} to {target_username}: {message}"
                )
            except:
                await target_socket.close()
                await self.remove_client(target_socket)
        else:
            sender_socket = self.clients[sender_username]
            await sender_socket.send(f"User {target_username} not found.")

    async def handle_file_transfer(self, message, websocket):
        parts = message.split(" ", 3)
        if len(parts) < 4:
            await websocket.send("Invalid FILE command")
            return

        _, target_username, file_name, file_data = parts
        if target_username in self.clients:
            target_socket = self.clients[target_username]
            try:
                await target_socket.send(f"FILE {file_name}")
                await target_socket.send(file_data)
            except:
                await target_socket.close()
                await self.remove_client(target_socket)
        else:
            await websocket.send(f"User {target_username} not found.")


    async def remove_client(self, websocket):
        username = self.client_names.get(websocket)
        if username:
            del self.clients[username]
            del self.client_names[websocket]
            await self.exchange_server.remove_presence("LOCAL", f'{username}@{self.server_name}')
            logger.info(f"{username} has left the chat.")
            await self.broadcast_message(f"{username} has left the chat.", websocket)

    def start_server(self):
        config = {}
        with open("server_config.yaml", "r") as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError:
                logging.error("unable to read config yaml file")
        self.server_name = config.get("server_name", "s4")
        chat_server_config = config.get("chat_server", {})
        host = chat_server_config.get("host", "localhost")
        port = chat_server_config.get("port", 12345)
        server = websockets.serve(self.handle_client, host, port)
        logger.info(f"Server started at {host}:{port}")
        return server
