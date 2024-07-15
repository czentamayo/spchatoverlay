import json
from dataclasses import dataclass
import logging
from typing import List
import websockets
import asyncio
from websockets.server import serve


@dataclass
class Presence:
    nickname: str
    jid: str
    pubickey: str


# Json wrapper for messsage
def message_json(sender: str, recipient: str, info: str) -> str:
    return json.dumps({"tag": "message", "from": sender, "to": recipient, "info": info})


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
                elif exchange_type == "check":
                    await websocket.send(check_json(True))
                elif exchange_type == "attendence":
                    await websocket.send(presence_json(list(self.client_presence.values())))
            except json.JSONDecodeError:
                logging.warn('incorrect json format')



    async def start_server(self):
        async with serve(self.exchange_handler, "localhost", 5555):
            await asyncio.Future()

    def stop_server(self):
        pass
