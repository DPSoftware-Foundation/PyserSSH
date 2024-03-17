"""
PyserSSH - A SSH server. For more info visit https://github.com/damp11113/PyserSSH
Copyright (C) 2023-2024 damp11113 (MIT)

Visit https://github.com/damp11113/PyserSSH

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

import os
import time
import paramiko
import socket
import threading
from functools import wraps
import logging

from .system.SFTP import SSHSFTPServer
from .system.interface import Sinterface
from .interactive import *
from .system.inputsystem import expect
from .system.info import system_banner

try:
    os.environ["pyserssh_systemmessage"]
except:
    os.environ["pyserssh_systemmessage"] = "YES"

if os.environ["pyserssh_systemmessage"] == "YES":
    print(system_banner)

#paramiko.sftp_file.SFTPFile.MAX_REQUEST_SIZE = pow(2, 22)

sftpclient = ["WinSCP", "Xplore"]

logger = logging.getLogger("PyserSSH")
logger.disabled = True

class Server:
    def __init__(self, accounts, system_message=True, timeout=0, disable_scroll_with_arrow=True, sftp=True, sftproot=os.getcwd(), system_commands=False, compression=True, usexternalauth=False, history=True):
        """
         A simple SSH server
        """
        self._event_handlers = {}
        self.sysmess = system_message
        self.client_handlers = {}  # Dictionary to store event handlers for each client
        self.current_users = {}  # Dictionary to store current_user for each connected client
        self.accounts = accounts
        self.timeout = timeout
        self.disable_scroll_with_arrow = disable_scroll_with_arrow
        self.sftproot = sftproot
        self.sftpena = sftp
        self.enasyscom = system_commands
        self.compressena = compression
        self.usexternalauth = usexternalauth
        self.history = history

        self.system_banner = system_banner

        if self.enasyscom:
            print("\033[33m!!Warning!! System commands is enable! \033[0m")

    def on_user(self, event_name):
        def decorator(func):
            @wraps(func)
            def wrapper(channel, *args, **kwargs):
                # Ignore the third argument
                filtered_args = args[:2] + args[3:]
                return func(channel, *filtered_args, **kwargs)
            self._event_handlers[event_name] = wrapper
            return wrapper
        return decorator

    def handle_client_disconnection(self, peername, current_user):
        if peername in self.client_handlers:
            del self.client_handlers[peername]
            logger.info(f"User {current_user} disconnected")

    def _handle_event(self, event_name, *args, **kwargs):
        handler = self._event_handlers.get(event_name)
        if handler:
            handler(*args, **kwargs)
        if event_name == "disconnected":
            self.handle_client_disconnection(*args, **kwargs)

    def handle_client(self, client, addr):
        bh_session = paramiko.Transport(client)
        bh_session.add_server_key(self.private_key)

        if self.sftpena:
            SSHSFTPServer.ROOT = self.sftproot
            SSHSFTPServer.ACCOUNT = self.accounts
            SSHSFTPServer.CLIENTHANDELES = self.client_handlers
            bh_session.set_subsystem_handler('sftp', paramiko.SFTPServer, SSHSFTPServer)

        if self.compressena:
            bh_session.use_compression(True)
        else:
            bh_session.use_compression(False)

        bh_session.default_window_size = 2147483647
        bh_session.packetizer.REKEY_BYTES = pow(2, 40)
        bh_session.packetizer.REKEY_PACKETS = pow(2, 40)

        server = Sinterface(self)
        bh_session.start_server(server=server)

        logger.info(bh_session.remote_version)

        channel = bh_session.accept()

        if self.timeout != 0:
            channel.settimeout(self.timeout)

        if channel is None:
            logger.warning("no channel")

        try:
            logger.info("user authenticated")
            client_address = channel.getpeername()  # Get client's address to identify the user
            if client_address not in self.client_handlers:
                # Create a new event handler for this client if it doesn't exist
                self.client_handlers[client_address] = {
                    "event_handlers": {},
                    "current_user": None,
                    "channel": channel,  # Associate the channel with the client handler,
                    "last_activity_time": None,
                    "connecttype": None,
                    "last_login_time": None,
                    "windowsize": {}
                }
            client_handler = self.client_handlers[client_address]
            client_handler["current_user"] = server.current_user
            client_handler["channel"] = channel  # Update the channel attribute for the client handler
            client_handler["last_activity_time"] = time.time()
            client_handler["last_login_time"] = time.time()

            peername = channel.getpeername()


            #byte = channel.recv(1)
            #if byte == b'\x00':

            #if not any(bh_session.remote_version.split("-")[2].startswith(prefix) for prefix in sftpclient):
            if not channel.out_window_size == bh_session.default_window_size:
                if self.sysmess:
                    channel.sendall(replace_enter_with_crlf(self.system_banner))
                    channel.sendall(replace_enter_with_crlf("\n"))

                while self.client_handlers[channel.getpeername()]["windowsize"] == {}:
                    pass

                self._handle_event("connect", channel, self.client_handlers[channel.getpeername()])

                client_handler["connecttype"] = "ssh"
                try:
                    channel.send(replace_enter_with_crlf(self.accounts.get_prompt(self.client_handlers[channel.getpeername()]["current_user"]) + " ").encode('utf-8'))
                    while True:
                        expect(self, channel, peername)
                except KeyboardInterrupt:
                    channel.close()
                    bh_session.close()
                except Exception as e:
                    logger.error(e)
                finally:
                    channel.close()
            else:
                if self.sftpena:
                    if self.accounts.get_user_sftp_allow(self.client_handlers[channel.getpeername()]["current_user"]):
                        client_handler["connecttype"] = "sftp"
                        self._handle_event("connectsftp", channel, self.client_handlers[channel.getpeername()])
                    else:
                        del self.client_handlers[peername]
                        channel.close()
                else:
                    del self.client_handlers[peername]
                    channel.close()
        except:
            raise

    def stop_server(self):
        logger.info("Stopping the server...")
        try:
            for client_handler in self.client_handlers.values():
                channel = client_handler.get("channel")
                if channel:
                    channel.close()
            self.server.close()
            logger.info("Server stopped.")
        except Exception as e:
            logger.error(f"Error occurred while stopping the server: {e}")

    def _start_listening_thread(self):
        try:
            self.server.listen(10)
            logger.info("Start Listening for connections...")
            while True:
                client, addr = self.server.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client, addr))
                client_thread.start()

        except Exception as e:
            logger.error(e)

    def run(self, private_key_path, host="0.0.0.0", port=2222):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.server.bind((host, port))
        self.private_key = paramiko.RSAKey(filename=private_key_path)

        client_thread = threading.Thread(target=self._start_listening_thread)
        client_thread.start()

    def kickbyusername(self, username, reason=None):
        for peername, client_handler in list(self.client_handlers.items()):
            if client_handler["current_user"] == username:
                channel = client_handler.get("channel")
                if reason is None:
                    if channel:
                        channel.close()
                    del self.client_handlers[peername]
                    logger.info(f"User '{username}' has been kicked.")
                else:
                    if channel:
                        Send(channel, f"You have been disconnected for {reason}")
                        channel.close()
                    del self.client_handlers[peername]
                    logger.info(f"User '{username}' has been kicked by reason {reason}.")

    def kickbypeername(self, peername, reason=None):
        client_handler = self.client_handlers.get(peername)
        if client_handler:
            channel = client_handler.get("channel")
            if reason is None:
                if channel:
                    channel.close()
                del self.client_handlers[peername]
                logger.info(f"peername '{peername}' has been kicked.")
            else:
                if channel:
                    Send(channel, f"You have been disconnected for {reason}")
                    channel.close()
                del self.client_handlers[peername]
                logger.info(f"peername '{peername}' has been kicked by reason {reason}.")

    def kickall(self, reason=None):
        for peername, client_handler in self.client_handlers.items():
            channel = client_handler.get("channel")
            if reason is None:
                if channel:
                    channel.close()
            else:
                if channel:
                    Send(channel, f"You have been disconnected for {reason}")
                    channel.close()

        if reason is None:
            self.client_handlers.clear()
            logger.info("All users have been kicked.")
        else:
            logger.info(f"All users have been kicked by reason {reason}.")

    def broadcast(self, message):
        for client_handler in self.client_handlers.values():
            channel = client_handler.get("channel")
            if channel:
                try:
                    # Send the message to the client
                    Send(channel, message)
                except Exception as e:
                    logger.error(f"Error occurred while broadcasting message: {e}")

    def sendto(self, username, message):
        for client_handler in self.client_handlers.values():
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