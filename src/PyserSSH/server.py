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
from .system.info import __version__, system_banner
from .system.clientype import Client as Clientype

# paramiko.sftp_file.SFTPFile.MAX_REQUEST_SIZE = pow(2, 22)

sftpclient = ["WinSCP", "Xplore"]

logger = logging.getLogger("PyserSSH")

class Server:
    def __init__(self, accounts, system_message=True, disable_scroll_with_arrow=True, sftp=False, system_commands=True, compression=True, usexternalauth=False, history=True, inputsystem=True, XHandler=None, title=f"PyserSSH v{__version__}", inspeed=32768, enable_preauth_banner=False, enable_exec_system_command=True, enable_remote_status=False, inputsystem_echo=True):
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
        self.__serverisrunning = False
        self.__daemon = False

        if self.enasyscom:
            print("\033[33m!!Warning!! System commands is enable! \033[0m")

    def on_user(self, event_name):
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
        if not chandlers["channel"].get_transport().is_active():
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

    def handle_client(self, socketchannel, addr):
        self._handle_event("pressh", socketchannel)

        try:
            bh_session = paramiko.Transport(socketchannel)
        except OSError:
            return

        bh_session.add_server_key(self.private_key)

        bh_session.use_compression(self.compressena)

        bh_session.default_window_size = 2147483647
        bh_session.packetizer.REKEY_BYTES = pow(2, 40)
        bh_session.packetizer.REKEY_PACKETS = pow(2, 40)

        bh_session.default_max_packet_size = self.inspeed

        server = Sinterface(self)
        try:
            bh_session.start_server(server=server)
        except:
            return

        logger.info(bh_session.remote_version)

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
            if int(channel.out_window_size) != int(bh_session.default_window_size):
                logger.info("user is ssh")
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

                        while True:
                            expect(self, self.client_handlers[channel.getpeername()], echo)
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
        logger.info("Stopping the server...")
        try:
            for client_handler in self.client_handlers.values():
                channel = client_handler.channel
                if channel:
                    channel.close()
            self.__serverisrunning = False
            self.server.close()

            logger.info("Server stopped.")
        except Exception as e:
            logger.error(f"Error occurred while stopping the server: {e}")

    def _start_listening_thread(self):
        try:
            logger.info("Start Listening for connections...")
            while self.__serverisrunning:
                client, addr = self.server.accept()
                if self.__processmode == "thread":
                    client_thread = threading.Thread(target=self.handle_client, args=(client, addr), daemon=True)
                    client_thread.start()
                else:
                    self.handle_client(client, addr)
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_server()
        except Exception as e:
            logger.error(e)

    def run(self, private_key_path=None, host="0.0.0.0", port=2222, mode="thread", maxuser=0, daemon=False):
        """mode: single, thread
        protocol: ssh, telnet
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.server.bind((host, port))

        if private_key_path != None:
            self.private_key = paramiko.RSAKey(filename=private_key_path)
        else:
            raise ValueError("No private key")

        if maxuser == 0:
            self.server.listen()
        else:
            self.server.listen(maxuser)

        self.__processmode = mode.lower()
        self.__serverisrunning = True
        self.__daemon = daemon

        client_thread = threading.Thread(target=self._start_listening_thread, daemon=self.__daemon)
        client_thread.start()

