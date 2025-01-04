"""
PyserSSH - A Scriptable SSH server. For more info visit https://github.com/DPSoftware-Foundation/PyserSSH
Copyright (C) 2023-present DPSoftware Foundation (MIT)

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

import time
import paramiko
import threading
from functools import wraps
import logging
import socket
import random
import traceback

from .system.SFTP import SSHSFTPServer
from .system.sysfunc import replace_enter_with_crlf
from .system.interface import Sinterface
from .system.inputsystem import expect
from .system.info import version, system_banner
from .system.clientype import Client as Clientype
from .system.ProWrapper import SSHTransport, TelnetTransport, ITransport

# paramiko.sftp_file.SFTPFile.MAX_REQUEST_SIZE = pow(2, 22)

sftpclient = ["WinSCP", "Xplore"]

logger = logging.getLogger("PyserSSH.Server")

class Server:
    def __init__(self, accounts, system_message=True, disable_scroll_with_arrow=True, sftp=False, system_commands=True, compression=True, usexternalauth=False, history=True, inputsystem=True, XHandler=None, title=f"PyserSSH v{version}", inspeed=32768, enable_preauth_banner=False, enable_exec_system_command=True, enable_remote_status=False, inputsystem_echo=True):
        """
        system_message set to False to disable welcome message from system
        disable_scroll_with_arrow set to False to enable seek text with arrow (Beta)
        sftp set to True to enable SFTP server
        system_commands set to False to disable system commmands
        compression set to False to disable SSH compression
        enable_remote_status set to True to enable mobaxterm remote monitor (Beta)
        """
        self.sysmess = system_message
        self.accounts = accounts
        self.disable_scroll_with_arrow = disable_scroll_with_arrow
        self.sftpena = sftp
        self.enasyscom = system_commands
        self.compressena = compression
        self.usexternalauth = usexternalauth
        self.history = history
        self.enainputsystem = inputsystem
        self.XHandler = XHandler
        self.title = title
        self.inspeed = inspeed
        self.enaloginbanner = enable_preauth_banner
        self.enasysexec = enable_exec_system_command
        self.enaremostatus = enable_remote_status
        self.inputsysecho = inputsystem_echo

        if self.XHandler != None:
            self.XHandler.serverself = self

        self._event_handlers = {}
        self.client_handlers = {}  # Dictionary to store event handlers for each client
        self.__processmode = None
        self.isrunning = False
        self.__daemon = False
        self.private_key = ""
        self.__custom_server_args = ()
        self.__custom_server = None
        self.__protocol = "ssh"

        if self.enasyscom:
            print("\033[33m!!Warning!! System commands is enable! \033[0m")

    def on_user(self, event_name):
        """Handle event"""
        def decorator(func):
            @wraps(func)
            def wrapper(client, *args, **kwargs):
                # Ignore the third argument
                filtered_args = args[:2] + args[3:]
                return func(client, *filtered_args, **kwargs)
            self._event_handlers[event_name] = wrapper
            return wrapper
        return decorator

    def handle_client_disconnection(self, handler, chandlers):
        if not chandlers["transport"].is_active():
            if handler:
                handler(chandlers)
            del self.client_handlers[chandlers["peername"]]

    def _handle_event(self, event_name, *args, **kwargs):
        handler = self._event_handlers.get(event_name)
        if event_name == "error" and isinstance(args[0], Clientype):
            args[0].last_error = traceback.format_exc()

        if event_name == "disconnected":
            self.handle_client_disconnection(handler, *args, **kwargs)
        elif handler:
            return handler(*args, **kwargs)

    def _handle_client(self, socketchannel, addr):
        self._handle_event("preserver", socketchannel)

        logger.info("Starting session...")
        server = Sinterface(self)

        if not self.__custom_server:
            if self.__protocol.lower() == "telnet":
                bh_session = TelnetTransport(socketchannel, server) # Telnet server
            else:
                bh_session = SSHTransport(socketchannel, server, self.private_key) # SSH server
        else:
            bh_session = self.__custom_server(socketchannel, server, *self.__custom_server_args) # custom server

        bh_session.enable_compression(self.compressena)

        bh_session.max_packet_size(self.inspeed)

        try:
            bh_session.start_server()
        except:
            return

        channel = bh_session.accept()

        if self.sftpena:
            bh_session.set_subsystem_handler('sftp', paramiko.SFTPServer, SSHSFTPServer, channel, self.accounts, self.client_handlers)

        if not bh_session.is_authenticated():
            logger.warning("user not authenticated")
            bh_session.close()
            return

        if channel is None:
            logger.warning("no channel")
            bh_session.close()
            return

        try:
            logger.info("user authenticated")
            peername = bh_session.getpeername()
            if peername not in self.client_handlers:
                # Create a new event handler for this client if it doesn't exist
                self.client_handlers[peername] = Clientype(channel, bh_session, peername)

            client_handler = self.client_handlers[peername]
            client_handler["current_user"] = bh_session.get_username()
            client_handler["channel"] = channel  # Update the channel attribute for the client handler
            client_handler["transport"] = bh_session  # Update the channel attribute for the client handler
            client_handler["last_activity_time"] = time.time()
            client_handler["last_login_time"] = time.time()
            client_handler["prompt"] = self.accounts.get_prompt(bh_session.get_username())
            client_handler["session_id"] = random.randint(10000, 99999) + int(time.time() * 1000)

            self.accounts.set_user_last_login(self.client_handlers[channel.getpeername()]["current_user"], peername[0])

            logger.info("saved user data to client handlers")

            #if not any(bh_session.remote_version.split("-")[2].startswith(prefix) for prefix in sftpclient):
            if not (int(channel.get_out_window_size()) == int(bh_session.get_default_window_size()) and bh_session.get_connection_type() == "SSH"):
                #timeout for waiting 10 sec
                for i in range(100):
                    if self.client_handlers[channel.getpeername()]["windowsize"]:
                        break
                    time.sleep(0.1)

                if self.client_handlers[channel.getpeername()]["windowsize"] == {}:
                    logger.info("timeout for waiting window size in 10 sec")
                    self.client_handlers[channel.getpeername()]["windowsize"] = {
                        "width": 80,
                        "height": 24,
                        "pixelwidth": 0,
                        "pixelheight": 0
                    }

                try:
                    self._handle_event("pre-shell", self.client_handlers[channel.getpeername()])
                except Exception as e:
                    self._handle_event("error", self.client_handlers[channel.getpeername()], e)

                while self.client_handlers[channel.getpeername()]["isexeccommandrunning"]:
                    time.sleep(0.1)

                userbanner = self.accounts.get_banner(self.client_handlers[channel.getpeername()]["current_user"])

                if self.accounts.get_user_enable_inputsystem_echo(self.client_handlers[channel.getpeername()]["current_user"]) and self.inputsysecho:
                    echo = True
                else:
                    echo = False

                if echo:
                    if self.title.strip() != "":
                        channel.send(f"\033]0;{self.title}\007".encode())

                    if self.sysmess or userbanner != None:
                        if userbanner is None and self.sysmess:
                            channel.sendall(replace_enter_with_crlf(system_banner))
                        elif userbanner != None and self.sysmess:
                            channel.sendall(replace_enter_with_crlf(system_banner))
                            channel.sendall(replace_enter_with_crlf(userbanner))
                        elif userbanner != None and not self.sysmess:
                            channel.sendall(replace_enter_with_crlf(userbanner))

                        channel.sendall(replace_enter_with_crlf("\n"))

                client_handler["connecttype"] = "ssh"

                try:
                    self._handle_event("connect", self.client_handlers[channel.getpeername()])
                except Exception as e:
                    self._handle_event("error", self.client_handlers[channel.getpeername()], e)

                if self.enainputsystem and self.accounts.get_user_enable_inputsystem(self.client_handlers[channel.getpeername()]["current_user"]):
                    try:
                        if self.accounts.get_user_timeout(self.client_handlers[channel.getpeername()]["current_user"]) != None:
                            channel.setblocking(False)
                            channel.settimeout(self.accounts.get_user_timeout(self.client_handlers[channel.getpeername()]["current_user"]))

                        if echo:
                            channel.send(replace_enter_with_crlf(self.client_handlers[channel.getpeername()]["prompt"] + " "))

                        isConnect = True

                        while isConnect:
                            isConnect = expect(self, self.client_handlers[channel.getpeername()], echo)

                        self._handle_event("disconnected", self.client_handlers[peername])
                        channel.close()
                        bh_session.close()
                    except KeyboardInterrupt:
                        self._handle_event("disconnected", self.client_handlers[peername])
                        channel.close()
                        bh_session.close()
                    except Exception as e:
                        self._handle_event("error", client_handler, e)
                        logger.error(e)
                    finally:
                        self._handle_event("disconnected", self.client_handlers[peername])
                        channel.close()
                        bh_session.close()
            else:
                if self.sftpena:
                    logger.info("user is sftp")
                    if self.accounts.get_user_sftp_allow(self.client_handlers[channel.getpeername()]["current_user"]):
                        client_handler["connecttype"] = "sftp"
                        self._handle_event("connectsftp", self.client_handlers[channel.getpeername()])
                        while bh_session.is_active():
                            time.sleep(0.1)

                        self._handle_event("disconnected", self.client_handlers[peername])
                    else:
                        self._handle_event("disconnected", self.client_handlers[peername])
                        channel.close()
                else:
                    self._handle_event("disconnected", self.client_handlers[peername])
                    channel.close()
        except:
            bh_session.close()

    def stop_server(self):
        """Stop server"""
        logger.info("Stopping the server...")
        try:
            for client_handler in self.client_handlers.values():
                channel = client_handler.channel
                if channel:
                    channel.close()
            self.isrunning = False
            self.server.close()

            logger.info("Server stopped.")
        except Exception as e:
            logger.error(f"Error occurred while stopping the server: {e}")

    def _start_listening_thread(self):
        try:
            self.isrunning = True
            try:
                logger.info("Listening for connections...")
                while self.isrunning:
                    client, addr = self.server.accept()
                    if self.__processmode == "thread":
                        logger.info(f"Starting client thread for connection {addr}")
                        client_thread = threading.Thread(target=self._handle_client, args=(client, addr), daemon=True)
                        client_thread.start()
                    else:
                        logger.info(f"Starting client for connection {addr}")
                        self._handle_client(client, addr)
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_server()
        except Exception as e:
            logger.error(e)

    def run(self, private_key_path=None, host="0.0.0.0", port=2222, waiting_mode="thread", maxuser=0, daemon=False, listen_thread=True, protocol="ssh", custom_server: ITransport = None, custom_server_args: tuple = None, custom_server_require_socket=True):
        """mode: single, thread,
        protocol: ssh, telnet (beta), serial, custom
        For serial need to set serial port at host (ex. host="com3") and set baudrate at port (ex. port=9600) and change listen_mode to "single".
        """
        if protocol.lower() == "ssh":
            if private_key_path != None:
                logger.info("Loading private key")
                self.private_key = paramiko.RSAKey(filename=private_key_path)
            else:
                raise ValueError("No private key")

        self.__processmode = waiting_mode.lower()
        self.__daemon = daemon

        if custom_server:
            self.__custom_server = custom_server
            self.__custom_server_args = custom_server_args

        if ((custom_server and protocol.lower() == "custom") and custom_server_require_socket) or protocol.lower() in ["ssh", "telnet"]:
            logger.info("Creating server...")
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.server.bind((host, port))

            logger.info("Set listen limit")
            if maxuser == 0:
                self.server.listen()
            else:
                self.server.listen(maxuser)

            if listen_thread:
                logger.info("Starting listening in threading")
                client_thread = threading.Thread(target=self._start_listening_thread, daemon=self.__daemon)
                client_thread.start()
            else:
                print(f"\033[32mServer is running on {host}:{port}\033[0m")
                self._start_listening_thread()
        else:
            client_thread = threading.Thread(target=self._handle_client, args=(None, None), daemon=True)
            client_thread.start()

        print(f"\033[32mServer is running on {host}:{port}\033[0m")