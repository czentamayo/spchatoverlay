import json
from dataclasses import dataclass
from typing import List

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
def presence_json(presence_list:List[Presence]) -> str:
    return json.dumps({
        "tag": "presence",
        "presence": presence_list
    })


# Json request for server presence list
def attendence_json() -> str:
    return json.dumps({
        "tag": "attendence"
    })


