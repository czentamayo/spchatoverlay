import json
from dataclasses import dataclass
import logging
from typing import List
import websockets
import asyncio
import yaml


@dataclass
class Presence:
    nickname: str
    jid: str
    pubickey: str


# Json wrapper for messsage
def message_json(sender: str, recipient: str, info: str) -> str:
    return json.dumps({"tag": "message", "from": sender, "to": recipient, "info": info})


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
    return json.dumps({"tag": "presence", "presence": presence_list})


# Json request for server presence list
def attendence_json() -> str:
    return json.dumps({"tag": "attendence"})


# Convert json string to dict
def parse_json(json_str: str) -> dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logging.warning("JSON parsing error")
        return {}


class ExchangeServer:

    def __init__(self):
        self.client_presence = {}

    def update_client_presence(self, client_jid: str, nickname: str, pubickey: str):
        self.client_presence[client_jid] = Presence(nickname, client_jid, pubickey)

    def remove_client_presence(self, client_jid: str):
        self.client_presence.pop(client_jid)

    def get_client_presence(self) -> dict:
        return self.client_presence

    async def exchange_handler(self, websocket: websockets.WebSocketServerProtocol):
        async for message in websocket:
            try:
                exchange = parse_json(str(message))
                exchange_type = exchange.get("tag", None)
                if exchange_type == "message":
                    pass
                elif exchange_type == "file":
                    pass
                elif exchange_type == "check":
                    await websocket.send(check_json(True))
                elif exchange_type == "attendence":
                    await websocket.send(
                        presence_json(list(self.client_presence.values()))
                    )
            except json.JSONDecodeError:
                logging.warn("incorrect json format")

    def start_server(self) -> websockets.serve:
        config = {}
        with open("server_config.yaml", "r") as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError:
                logging.error("unable to read config yaml file")
        exchange_server_config = config.get("exchange_server", {})
        host = exchange_server_config.get("host", "localhost")
        port = exchange_server_config.get("port", 5555)
        return websockets.serve(self.exchange_handler, host, port)

    def stop_server(self):
        pass
