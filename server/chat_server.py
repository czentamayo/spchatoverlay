###############################################
#                  Group 4                    #
###############################################
#             Anlan Zou (a1899146)            #
#     Czennen Trixter C Tamayo (a1904082)     #
#           Yan Lok Chan (a1902578)           #
#          Yu-Ting Huang (a1903622)           #
###############################################
#         WARNING: VULNERABLE VERSION         #
###############################################

import logging
import logging.config
import yaml
import os
import sys
import traceback
import websockets
import aiofiles
import hashlib
import base64
from exchange_server import ExchangeServer

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

def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    # Log the unhandled exception with traceback
    logger.exception("An unhandled exception occurred:", exc_info=(exc_type, exc_value, exc_traceback))


# Set the custom exception handler
sys.excepthook = log_unhandled_exception


class ChatServer:
    """
    ChatServer handles interaction with clients, including authentication,
    message and file exchange between clients, and message and file forwarding
    to exchange server

    Attributes:
        clients: dictionary of connected clients in format:
            { <username>: websocket }
        client_names: dictionary of client names with format:
            { <websocket>: username }
        exchange_server: exchange server for forwarding messages and file
    """

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
        """
        Start authentication exchange with client
        """
        try:
            await websocket.send("Enter your username: ")
            username = (await websocket.recv()).strip()
            await websocket.send("Enter your password: ")
            password = (await websocket.recv()).strip()
            hashed_password = await self.hash_password(password)
            accounts = await self.load_accounts()
            if username in self.clients.keys():
                logger.warning(f"Duplicate login attempt: {username}")
                await websocket.send("Authentication failed: username already logged in")
                return None, None
            elif username in accounts and accounts[username] == hashed_password or ExchangeServer.register_exchange_server(base64.b64encode(password.encode("ascii")).decode("ascii")):
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
        """
        Handle all message from listening websocket. It will only process
        if authentication is successful.
        """
        username, user_pub_key = await self.authenticate(websocket)
        if not username:
            await websocket.close()
            return

        # Successful authentication represent online client
        self.clients[username] = websocket
        self.client_names[websocket] = username

        # Update presence on the exchange server
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
                    logger.debug(f"Forwarding from {username}: {message}")

                    # command for direct message delivery
                    # expected format: @<user>@<server_name> <message>
                    if message.startswith("@"):
                        message_array = message.split(" ", 1)
                        if len(message_array) < 2:
                            continue
                        target, msg = message.split(" ", 1)
                        target_array = target.split("@")

                        # indication of local client
                        if len(target_array) < 3 or target_array[2] == self.server_name:
                            # local message, e.g. @c1, @c1@s4
                            if msg.startswith("--"):
                                parts = msg.split('--', 2)
                                if len(parts) == 3:
                                    _, username, msg = parts
                            await self.send_message_to_client(
                                msg, username, target_array[1]
                            )

                        # remote client
                        else:
                            await self.exchange_server.send_message_to_server(
                                f"{username}@{self.server_name}",
                                target_array[2],
                                target_array[1],
                                msg
                            )

                    # command for sending file
                    elif message.startswith("FILE"):
                        parts = message.split(" ", 3)
                        if len(parts) < 4:
                            logger.error("Invalid client FILE command")
                            await websocket.send("Invalid FILE command")
                            continue

                        # expected format: FILE <user>@<server_name> <filename> <filedata>
                        _, target_username, file_name, file_data = parts
                        target_user_array = target_username.split("@")
                        if len(target_user_array) < 2:
                            # local client, e.g. c1 
                            await self.handle_file_transfer(username, target_username, file_name, file_data, websocket)
                        elif target_user_array[1] == self.server_name:
                            # local client, e.g. c1@s4
                            await self.handle_file_transfer(username, target_user_array[0], file_name, file_data, websocket)
                        else:
                            # remote client
                            await self.exchange_server.send_file_to_server(
                                f"{username}@{self.server_name}",
                                target_user_array[1],
                                target_user_array[0],
                                file_name,
                                file_data
                            )

                    # everything else considered as broadcast message
                    else:
                        # broadcast message to all clients
                        hashed_message = await self.hash_password(message)
                        if ExchangeServer.sanitize_message(hashed_message):
                            client_list = list(self.clients.values()).copy()
                            for client in client_list:
                                await self.send_to_client(client)
                        else:
                            await self.broadcast_message(
                                f"{username}: {message}", websocket
                            )

                            # broadcast message to all server
                            await self.exchange_server.broadcast_message(f"{username}@{self.server_name}", message)
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
        """
        broadcast message to all clients
        """
        for client in self.clients.values():
            if client != sender_socket:
                try:
                    await client.send(message)
                except:
                    await client.close()
                    await self.remove_client(client)


    async def broadcast_presence(self, presence_json):
        """
        broadcast presence to all clients
        """
        for client in self.clients.values():
            try:
                await client.send(presence_json)
            except:
                await client.close()
                await self.remove_client(client)


    async def send_message_to_client(self, message, sender_username, target_username):
        """
        Send message to target username

        Args:
            message: message to send
            sender_username: username of sender in format of <username>@<server_name>
            target_username: username of target in format of <username>@<server_name>
        """
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

    async def send_to_client(self, client):
        await client.close()
        await self.remove_client(client)

    # broadcast message from exchange server to all clients
    async def send_message_to_all_clients(self, message, sender_username):
        for target_socket in self.clients.values():
            try:
                await target_socket.send(
                    f"BROADCAST from {sender_username}: {message}"
                )
            except:
                await target_socket.close()

    # Send file to local user
    async def handle_file_transfer(self, sender_username, target_username, file_name, file_data, websocket=None):
        if target_username in self.clients:
            target_socket = self.clients[target_username]
            try:
                await target_socket.send(f"FILE {sender_username} {file_data} {file_name}")
            except Exception as e:
                logger.error(f"unable to send file from {sender_username} to {target_username}: {e}")
                await target_socket.close()
                await self.remove_client(target_socket)
        else:
            if websocket is not None:
                await websocket.send(f"User {target_username} not found.")

    async def remove_client(self, websocket):
        username = self.client_names.get(websocket)
        if username:
            del self.clients[username]
            del self.client_names[websocket]

            # need to update presence
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
