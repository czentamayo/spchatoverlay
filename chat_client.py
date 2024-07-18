import asyncio
import websockets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
import base64
import json

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

# Convert json string to dict
def parse_json(json_str: str) -> dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("JSON parsing error")
        return {}


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
                    if "tag" in message and "presence" in message:
                        presence_json = parse_json(message)
                        current_presence = presence_json["presence"]
                    else:
                        print(message)
                else:
                    break
            except websockets.ConnectionClosed:
                print("Server connection closed.")
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
    finally:
        await websocket.close()
        print("Connection closed gracefully.")


async def start_client():
    uri = "ws://localhost:12345"
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
                    await websocket.send(local_public_key_pem)
                    break
                elif response == "Authentication failed":
                    print("Authentication failed. Disconnecting.")
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
                        file_message = f"FILE {target_username} {file_path}"
                        await websocket.send(file_message)
                        await websocket.send(
                            base64.b64encode(file_data).decode("utf-8")
                        )
                    except FileNotFoundError:
                        print(f"File {file_path} not found.")
                else:
                    await websocket.send(message)
    except websockets.ConnectionClosed:
        print("Connection closed by server.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Client shutting down.")


if __name__ == "__main__":
    asyncio.run(start_client())
