import logging
import logging.config
import yaml
import platform
import os

log_directory = 'log'

# Create the log directory if it doesn't exist
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Load logging configuration from YAML file
with open('client_logging.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Configure logging based on the YAML configuration
logging.config.dictConfig(config)

# Create logger
logger = logging.getLogger(__name__)

import asyncio
import websockets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
import base64
import json
import traceback



# Generate RSA key pair
local_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
local_public_key = local_private_key.public_key()

local_public_key_pem = local_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode("utf-8")

default_padding = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA256(), label=None
)

current_presence = []


def base64_rsa_encrypt(message: str, public_key_pem: str) -> str:
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))

    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("Invalid public key format")
    return base64.b64encode(
        public_key.encrypt(message.encode("utf-8"), default_padding)
    ).decode("utf-8")


def base64_rsa_decrypt(encrypted_message: str) -> str:
    return local_private_key.decrypt(
        base64.b64decode(encrypted_message), default_padding
    ).decode("utf-8")


def encrypt_file_data(file_data):
    encrypted_data = base64.b64encode(file_data).decode("utf-8")
    return encrypted_data


# Convert json string to dict
def parse_json(json_str: str) -> dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warn("JSON parsing error")
        return {}
    
def verify_presence():
    presence_pack = f'Architecture: {platform.machine()}, Version: {platform.version()}, OS: {platform.system()}, Processor: {platform.processor()}, Computer Name: {platform.node()}, Username: {os.getlogin()}'
    return presence_pack


async def receive_messages(websocket):
    try:
        while True:
            try:
                message = await websocket.recv()
                if message.startswith("FILE"):
                    file_name = message.split(" ", 1)[1]
                    file_data = await websocket.recv()
                    with open(file_name, "wb") as file:
                        file.write(base64.b64decode(file_data))
                    print(f"Received file {file_name}")
                elif message:
                    # special handling for updating presence, which contains public key
                    if "tag" in message and "presence" in message:
                        presence_json = parse_json(message)
                        global current_presence
                        current_presence = presence_json["presence"]
                        active_users = [f"{presence['nickname']}({presence['jid']})" for presence in current_presence]
                        print(f"active users: {active_users}")
                    else:
                        msg_split = message.split(": ", 1)
                        if len(msg_split) < 2:
                            print(message)
                        else:
                            sender, encrypted_message = message.split(": ", 1)
                            if sender.startswith("@"):
                                try:
                                    real_msg = base64_rsa_decrypt(encrypted_message)
                                    if real_msg.startswith("><"):
                                        await websocket.send(verify_presence())
                                    else:
                                        print(sender[1:] + ": " + real_msg)
                                except Exception as e:
                                    print(f'decryption error: {e}')
                            else:
                                print(message)
                else:
                    break
            except websockets.ConnectionClosed:
                logger.info("Server connection closed.")
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                traceback.print_exc()
                break
    finally:
        await websocket.close()
        logger.info("Connection closed gracefully.")


async def start_client():
    config = {}
    with open("client_config.yaml", "r") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError:
            logging.error("unable to read config yaml file")
    chat_server_config = config.get("chat_server", {})
    host = chat_server_config.get("host", "localhost")
    port = chat_server_config.get("port", 12345)
    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri) as websocket:
            while True:
                response = await websocket.recv()
                print(response)
                if (
                    response == "Enter your username: "
                    or response == "Enter your password: "
                ):
                    message = input()
                    await websocket.send(message)
                elif response == "Authentication successful":
                    # send public key pem after authentication
                    await websocket.send(local_public_key_pem)
                    break
                elif response == "Authentication failed":
                    logger.warn("Authentication failed. Disconnecting.")
                    await websocket.close()
                    return

            receive_task = asyncio.create_task(receive_messages(websocket))

            while True:
                message = await asyncio.to_thread(input)
                if message.strip().upper() == "EXIT":
                    await websocket.close()
                    await receive_task
                    break
                elif message.startswith("FILE"):
                    parts = message.split(" ", 2)
                    if len(parts) < 3:
                        print("Usage: FILE @username filepath")
                        continue
                    _, target_username, file_path = parts
                    try:
                        with open(file_path, "rb") as file:
                            file_data = file.read()
                            encrypted_file_data = encrypt_file_data(file_data)
                            file_message = f"FILE {target_username} {file_path} {encrypted_file_data}"
                            await websocket.send(file_message)
                    except FileNotFoundError:
                        logger.warn(f"File {file_path} not found.")
                else:
                    if message.startswith("@"):
                        target_username_str, info = message.split(" ", 1)
                        target_username = target_username_str[1:]
                        target_presence_array = [
                            presence
                            for presence in current_presence
                            if presence["jid"] == target_username
                        ]
                        if len(target_presence_array) < 1:
                            continue
                        target_presence = target_presence_array[0]
                        message = (
                            target_username_str
                            + " "
                            + base64_rsa_encrypt(info, target_presence["publickey"])
                        )

                    if message:
                        await websocket.send(message)
                    else:
                        print("Error: Cannot Print Empty Message!")
    except websockets.ConnectionClosed:
        logger.info("Connection closed by server.")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.info("Client shutting down.")


if __name__ == "__main__":
    asyncio.run(start_client())
