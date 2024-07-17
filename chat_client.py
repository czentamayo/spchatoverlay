import asyncio
import websockets
import base64

async def receive_messages(websocket):
    try:
        while True:
            try:
                message = await websocket.recv()
                if message.startswith("FILE"):
                    file_name = message.split(" ", 1)[1]
                    file_data = await websocket.recv()
                    with open(file_name, 'wb') as file:
                        file.write(base64.b64decode(file_data))
                    print(f"Received file {file_name}")
                elif message:
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
                if response == "Enter your username: " or response == "Enter your password: ":
                    message = input()
                    await websocket.send(message)
                elif response == "Authentication successful":
                    break
                elif response == "Authentication failed":
                    print("Authentication failed. Disconnecting.")
                    await websocket.close()
                    return

            receive_task = asyncio.create_task(receive_messages(websocket))

            while True:
                message = await asyncio.to_thread(input)
                if message.strip().upper() == 'EXIT':
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
                        with open(file_path, 'rb') as file:
                            file_data = file.read()
                        file_message = f"FILE {target_username} {file_path}"
                        await websocket.send(file_message)
                        await websocket.send(base64.b64encode(file_data).decode('utf-8'))
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

if __name__ == '__main__':
    asyncio.run(start_client())
