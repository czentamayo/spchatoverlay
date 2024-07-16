import asyncio
import websockets
import aiofiles
import hashlib

import server_exchange

clients = {}
client_names = {}
exchange_server = server_exchange.ExchangeServer()


async def load_accounts(filename="theaccounts.txt"):
    accounts = {}
    async with aiofiles.open(filename, 'r') as file:
        async for line in file:
            username, password = line.strip().split('::')
            accounts[username] = password
    return accounts


async def hash_password(password):
    h = hashlib.sha256()
    h.update(password.encode())
    return h.hexdigest()


async def authenticate(websocket):
    try:
        await websocket.send("Enter your username: ")
        username = (await websocket.recv()).strip()
        await websocket.send("Enter your password: ")
        password = (await websocket.recv()).strip()
        password = await hash_password(password)
        accounts = await load_accounts()
        if username in accounts and accounts[username] == password:
            await websocket.send("Authentication successful")
            return username
        else:
            await websocket.send("Authentication failed")
            return None
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected during authentication.")
        return None


async def handle_client(websocket):
    username = await authenticate(websocket)
    if not username:
        await websocket.close()
        return

    clients[username] = websocket
    client_names[websocket] = username
    await exchange_server.update_presence('LOCAL', username, username, 'tmp')
    welcome_message = f'{username} has joined the chat.\n'
    print(welcome_message)
    await broadcast_message(welcome_message, websocket)
    
    try:
        while True:
            message = await websocket.recv()
            if message:
                print(f'Received from {username}: {message}')
                if message.startswith("@"):
                    target_username, msg = message.split(" ", 1)
                    target_username = target_username[1:]
                    await send_message_to_client(msg, username, target_username)
                elif message.startswith("FILE"):
                    await handle_file_transfer(message, websocket)
                else:
                    await broadcast_message(f"{username}: {message}", websocket)
            else:
                await websocket.close()
                await remove_client(websocket)
                break
    except websockets.ConnectionClosed:
        await remove_client(websocket)
    except Exception as e:
        print(f'Error: {e}')
        await remove_client(websocket)


async def broadcast_message(message, sender_socket):
    print(exchange_server.get_presences())
    for client in clients.values():
        if client != sender_socket:
            try:
                await client.send(message)
            except:
                await client.close()
                await remove_client(client)


async def send_message_to_client(message, sender_username, target_username):
    print(f"sending to {target_username}")
    if target_username in clients:
        target_socket = clients[target_username]
        try:
            await target_socket.send(f"{sender_username} to {target_username}: {message}")
        except:
            await target_socket.close()
            await remove_client(target_socket)
    else:
        sender_socket = clients[sender_username]
        await sender_socket.send(f"User {target_username} not found.")


async def handle_file_transfer(message, websocket):
    parts = message.split(" ", 2)
    if len(parts) < 3:
        await websocket.send("Invalid FILE command")
        return

    _, target_username, file_name = parts
    file_data = await websocket.recv()
    if target_username in clients:
        target_socket = clients[target_username]
        try:
            await target_socket.send(f"FILE {file_name}")
            await target_socket.send(file_data)
        except:
            await target_socket.close()
            await remove_client(target_socket)
    else:
        await websocket.send(f"User {target_username} not found.")


async def remove_client(websocket):
    username = client_names.get(websocket)
    if username:
        del clients[username]
        del client_names[websocket]
        await exchange_server.remove_presence('LOCAL', username)
        print(f"{username} has left the chat.")
        await broadcast_message(f"{username} has left the chat.", websocket)


def start_server():
    host = 'localhost'
    port = 12345
    server = websockets.serve(handle_client, host, port)
    print(f'Server started at {host}:{port}')
    return server
    

async def main():
    await asyncio.gather(exchange_server.start_server(), start_server())

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
    loop.close()
