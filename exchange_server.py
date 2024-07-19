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

import json
from dataclasses import dataclass
from typing import List
import websockets
import yaml
import asyncio



@dataclass
class Presence:
    nickname: str
    jid: str
    publickey: str


# Json wrapper for messsage
def message_json(sender: str, recipient: str, info: str) -> str:
    return json.dumps(
        {
            "tag": "message",
            "from": sender,
            "to": recipient,
            "info": info,
        }
    )


# Json to send file
def file_json(sender: str, recipient: str, filename: str, encoded_file: str) -> str:
    return json.dumps(
        {
            "tag": "file",
            "from": sender,
            "to": recipient,
            "filename": filename,
            "info": encoded_file,
        }
    )


# Json to check if server is online
# if is_response is True, it will generate response for check request from other server
def check_json(is_response=False) -> str:
    if is_response:
        return json.dumps({"tag": "checked"})
    else:
        return json.dumps({"tag": "check"})


# Json containing list of presence, which represents online users and corresponding public keys
def presence_json(presence_list: List[Presence]) -> str:
    formated_presence_list = [
        dict(
            {
                "nickname": presence.nickname,
                "jid": presence.jid,
                "publickey": presence.publickey,
            }
        )
        for presence in presence_list
    ]
    return json.dumps({"tag": "presence", "presence": formated_presence_list})


# Json request for server presence list
def attendance_json() -> str:
    return json.dumps({"tag": "attendance"})


# Convert json string to dict
def parse_json(json_str: str) -> dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("JSON parsing error")
        return {}


class ExchangeServer:

    def __init__(self):
        # presences is in format {server_name: {client_jid: Presence}}
        self.presences = {}
        self.remote_servers = {}
        self.server_name = "s4"

    def set_chat_server(self, chat_server):
        self.chat_server = chat_server

    # broadcasting presence to all remote servers if connected
    async def broadcast_presence(self):
        for remote_server in self.remote_servers.values():
            if remote_server.get("request_websocket", None):
                await remote_server["request_websocket"].send(
                    presence_json(list(self.presences.get("LOCAL", {}).values()))
                )
            elif remote_server.get("websocket", None):
                await remote_server["websocket"].send(
                    presence_json(list(self.presences.get("LOCAL", {}).values()))
                )

    async def send_message_to_server(self, sender:str, target_server:str, target_client:str, msg:str):
        remote_server = self.remote_servers.get(target_server, None)
        logger.debug(remote_server)
        if remote_server:
            if remote_server.get("websocket", None):
                await remote_server["websocket"].send(
                    message_json(sender, f'{target_client}@{target_server}', msg)
                )
            elif remote_server.get("request_websocket", None):
                await remote_server["request_websocket"].send(
                    message_json(sender, f'{target_client}@{target_server}', msg)
                )

    async def update_presence(
        self, server_name: str, client_jid: str, nickname: str, publickey: str
    ):
        if server_name == "LOCAL":
            client_jid = f"{client_jid}@{self.server_name}"
        target_server_presences = self.presences.get(server_name, dict())
        target_server_presences.update(
            {client_jid: Presence(nickname, client_jid, publickey)}
        )
        self.presences[server_name] = target_server_presences
        flatten_presence = [value for sublist in self.presences.values() for value in sublist.values()]
        if server_name == "LOCAL":
            await self.broadcast_presence()
            await self.chat_server.broadcast_presence(presence_json(flatten_presence))
        else:
            await self.chat_server.broadcast_presence(presence_json(flatten_presence))

    async def remove_presence(self, server_name: str, client_jid: str):
        target_server_presence = self.presences.get(server_name, dict())
        target_server_presence.pop(client_jid, None)
        self.presences[server_name] = target_server_presence
        if server_name == "LOCAL":
            await self.broadcast_presence()
            flatten_presence = [value for sublist in self.presences.values() for value in sublist.values()]
            await self.chat_server.broadcast_presence(presence_json(flatten_presence))

    def get_presences(self) -> dict:
        return self.presences

    # handling all the request or response from known exchange servers
    async def exchange_handler(self, websocket, server_name=None):
        try:
            remote_address = websocket.remote_address
            if isinstance(websocket, websockets.WebSocketServerProtocol):
                matched_remote_servers = [
                    server
                    for server in self.remote_servers.values()
                    if server["host"] == remote_address[0]
                ]
                # disconnect if unknown server
                if not matched_remote_servers:
                    logger.warn("Unknown server, disconnecting...")
                    await websocket.close()
                    return
                remote_server = matched_remote_servers[0]
                # assoicate the websocket with remote server
                remote_server["websocket"] = websocket
                logger.info(f"accepted connection from {remote_server}")
            else:
                matched_remote_servers = [
                    server
                    for server in self.remote_servers.values()
                    if server["name"] == server_name
                ]
                remote_server = matched_remote_servers[0]
                remote_server["request_websocket"] = websocket
            self.remote_servers[remote_server["name"]] = remote_server
            async for message in websocket:
                try:
                    logger.debug(f"Received from exchange server: {message}" )
                    exchange = parse_json(str(message))
                    exchange_type = exchange.get("tag", None)
                    if exchange_type == "message":
                        exchange_from = exchange.get("from", None)
                        exchange_to = exchange.get("to", None)
                        exchange_info = exchange.get("info", None)

                        # message validation
                        if not exchange_from or not exchange_to or not exchange_info:
                            continue
                        to_array = exchange_to.split("@")
                        if len(to_array) < 2:
                            continue
                        to_client = to_array[0]
                        to_server = to_array[1]
                        if to_server != self.server_name:
                            continue
                        if self.presences['LOCAL'].get(exchange_to, None):
                            logger.debug("forwarding to client")
                            await self.chat_server.send_message_to_client(
                                exchange_info, exchange_from, to_client
                        )
                    elif exchange_type == "file":
                        pass
                    elif exchange_type == "check":
                        await websocket.send(check_json(True))
                    elif exchange_type == "attendance":
                        await websocket.send(
                            presence_json(list(self.presences.get("LOCAL", {}).values()))
                        )
                    elif exchange_type == "presence":
                        for presence in exchange.get("presence", []):
                            await self.update_presence(
                                remote_server["name"],
                                presence["jid"],
                                presence["nickname"],
                                presence["publickey"],
                            )
                        logger.debug(f"updated presence: {self.presences}")
                except json.JSONDecodeError:
                    logger.warn("incorrect json format")
        except websockets.exceptions.ConnectionClosedOK:
            remote_address = websocket.remote_address
            logger.info(f"Server {remote_address} closed the connection.")
        except websockets.exceptions.ConnectionClosedError as e:
            remote_address = websocket.remote_address
            logger.error(f"Connection {remote_address} closed with error: {e.code}, {e.reason}")
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")

                
    def start_server(self) -> websockets.serve:
        config = {}
        with open("server_config.yaml", "r") as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError:
                logging.error("unable to read config yaml file")
        remote_server_list = config.get("remote_servers", [])
        self.remote_servers = {
            remote_server["name"]: remote_server for remote_server in remote_server_list
        }
        self.server_name = config.get("server_name", "s4")
        exchange_server_config = config.get("exchange_server", {})
        host = exchange_server_config.get("host", "localhost")
        port = exchange_server_config.get("port", 5555)
        return websockets.serve(self.exchange_handler, host, port)


    async def connect_websocket(self, remote_server):
        while True:
            request_websocket = remote_server.get("request_websocket", None)
            request_ws_url = f"ws://{remote_server['host']}:{remote_server['port']}"
            # request_ws_url = f"wss://{remote_server['host']}"
            if not request_websocket or request_websocket.closed:
                try:
                    async with websockets.connect(request_ws_url) as request_websocket:
                        self.remote_servers[remote_server["name"]]["request_websocket"] = request_websocket
                        logger.info(f"Connection to {request_ws_url} successfully, sending attendance")
                        await request_websocket.send(attendance_json())
                        await self.exchange_handler(request_websocket, remote_server["name"])
                except websockets.WebSocketException as e:
                    logger.warn(f"Connection to {request_ws_url} failed: {e}")
                except ConnectionRefusedError as e:
                    logger.warn(f"Connection to {request_ws_url} failed: {e}")
                finally:
                    await asyncio.sleep(10)
            else:
                await asyncio.sleep(10)


    def connect_remote_servers(self):
        tasks = []
        for remote_server in self.remote_servers.values():
            tasks.append(self.connect_websocket(remote_server))
        return tasks

