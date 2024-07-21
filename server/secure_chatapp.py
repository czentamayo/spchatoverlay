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

from chat_server import ChatServer
from exchange_server import ExchangeServer

import asyncio


async def main():
    # connection with peer server
    exchange_server = ExchangeServer()
    # client interaction handling server
    chat_server = ChatServer()
    exchange_server.set_chat_server(chat_server)
    chat_server.set_exchange_server(exchange_server)
    await asyncio.gather(
        exchange_server.start_server(),
        chat_server.start_server(),
        *exchange_server.connect_remote_servers()
    )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
    loop.close()
