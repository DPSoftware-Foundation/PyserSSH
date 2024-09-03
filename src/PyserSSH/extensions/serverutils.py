"""
PyserSSH - A Scriptable SSH server. For more info visit https://github.com/DPSoftware-Foundation/PyserSSH
Copyright (C) 2023-2024 DPSoftware Foundation (MIT)

Visit https://github.com/DPSoftware-Foundation/PyserSSH

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import logging

from ..interactive import Send

logger = logging.getLogger("PyserSSH")

def kickbyusername(server, username, reason=None):
    for peername, client_handler in list(server.client_handlers.items()):
        if client_handler["current_user"] == username:
            channel = client_handler.get("channel")
            server._handle_event("disconnected", channel.getpeername(), server.client_handlers[channel.getpeername()]["current_user"])
            if reason is None:
                if channel:
                    channel.close()
                logger.info(f"User '{username}' has been kicked.")
            else:
                if channel:
                    Send(channel, f"You have been disconnected for {reason}")
                    channel.close()
                logger.info(f"User '{username}' has been kicked by reason {reason}.")

def kickbypeername(server, peername, reason=None):
    client_handler = server.client_handlers.get(peername)
    if client_handler:
        channel = client_handler.get("channel")
        server._handle_event("disconnected", channel.getpeername(), server.client_handlers[channel.getpeername()]["current_user"])
        if reason is None:
            if channel:
                channel.close()
            logger.info(f"peername '{peername}' has been kicked.")
        else:
            if channel:
                Send(channel, f"You have been disconnected for {reason}")
                channel.close()
            logger.info(f"peername '{peername}' has been kicked by reason {reason}.")

def kickall(server, reason=None):
    for peername, client_handler in server.client_handlers.items():
        channel = client_handler.get("channel")
        server._handle_event("disconnected", channel.getpeername(), server.client_handlers[channel.getpeername()]["current_user"])
        if reason is None:
            if channel:
                channel.close()
        else:
            if channel:
                Send(channel, f"You have been disconnected for {reason}")
                channel.close()
    if reason is None:
        server.client_handlers.clear()
        logger.info("All users have been kicked.")
    else:
        logger.info(f"All users have been kicked by reason {reason}.")

def broadcast(server, message):
    for client_handler in server.client_handlers.values():
        channel = client_handler.get("channel")
        if channel:
            try:
                # Send the message to the client
                Send(channel, message)
            except Exception as e:
                logger.error(f"Error occurred while broadcasting message: {e}")

def sendto(server, username, message):
    for client_handler in server.client_handlers.values():
        if client_handler.get("current_user") == username:
            channel = client_handler.get("channel")
            if channel:
                try:
                    # Send the message to the specific client
                    Send(channel, message)
                except Exception as e:
                    logger.error(f"Error occurred while sending message to {username}: {e}")
                break
    else:
        logger.warning(f"User '{username}' not found.")
