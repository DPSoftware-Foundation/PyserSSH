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

from .system.ProWrapper.SSHWrapper import SSHTransport
from .system.ProWrapper.TelnetWrapper import TelnetTransport
from .system.SFTP import SSHSFTPServer
from .system.sysfunc import replace_enter_with_crlf
from .system.interface import Sinterface
from .system.inputsystem import expect
from .system.info import version, system_banner
from .system.clientype import Client as Clientype
from .system.ProWrapper.PWInterface import ITransport
from .account.AMInterface import IAccountManager
from .system.ProWrapper.TTYWrapper import TTYTransport

logger = logging.getLogger("PyserSSH.Server")

class Server:
    def __init__(self, accounts: IAccountManager, system_message=True, sftp=False, system_commands=True, compression=True, usexternalauth=False, history=True, inputsystem=True, XHandler=None, title=f"PyserSSH v{version}", max_bandwidth=65536, enable_preauth_banner=False, enable_exec_system_command=True, enable_remote_status=False, inputsystem_echo=True, hostname="PyserSSH"):
        """
        system_message set to False to disable welcome message from system
        sftp set to True to enable SFTP server
        system_commands set to False to disable system commmands
        compression set to False to disable SSH compression
        enable_remote_status set to True to enable mobaxterm remote monitor (Beta)
        """
        self.sysmess = system_message
        self.accounts = accounts
        self.sftpena = sftp
        self.enasyscom = system_commands
        self.compressena = compression
        self.usexternalauth = usexternalauth
        self.history = history
        self.enainputsystem = inputsystem
        self.XHandler = XHandler
        self.title = title
        self.max_bandwidth = max_bandwidth
        self.enaloginbanner = enable_preauth_banner
        self.enasysexec = enable_exec_system_command
        self.enaremostatus = enable_remote_status
        self.inputsysecho = inputsystem_echo
        self.hostname = hostname

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
        self._protocol = "ssh"
        self.__lastclient_exit = None
        self.__is_tty_connected = False
        self.startuptime = 0
        self.client_threads = {}  # Dictionary to store threads by peername
        self.thread_lock = threading.Lock()  # Lock for thread-safe operations

        if self.enasyscom:
            print("\033[33m!!Warning!! System commands is enable! \033[0m")

    def _register_client_thread(self, peername, thread):
        """Register a client thread for management"""
        with self.thread_lock:
            self.client_threads[peername] = {
                'thread': thread,
                'start_time': time.time(),
                'is_alive': True
            }

    def _unregister_client_thread(self, peername):
        """Unregister a client thread"""
        with self.thread_lock:
            if peername in self.client_threads:
                self.client_threads[peername]['is_alive'] = False
                del self.client_threads[peername]

    def get_active_threads(self):
        """Get list of active client threads"""
        with self.thread_lock:
            return {
                peername: {
                    'thread_id': data['thread'].ident,
                    'start_time': data['start_time'],
                    'username': self.client_handlers[peername]['current_user']
                    if peername in self.client_handlers else None
                }
                for peername, data in self.client_threads.items()
                if data['thread'].is_alive()
            }

    def kill_client_thread(self, peername):
        """Kill a specific client thread by closing its connection"""
        with self.thread_lock:
            if peername in self.client_handlers:
                client_handler = self.client_handlers[peername]
                try:
                    client_handler.close()

                    logger.info(f"Killed client thread for {peername}")
                    return True
                except Exception as e:
                    logger.error(f"Error killing thread for {peername}: {e}")
                    return False
            return False

    def kill_user_threads(self, username):
        """Kill all threads for a specific username"""
        killed_count = 0
        with self.thread_lock:
            peers_to_kill = [
                peername for peername, handler in self.client_handlers.items()
                if handler.get('current_user') == username
            ]

        for peername in peers_to_kill:
            if self.kill_client_thread(peername):
                killed_count += 1

        return killed_count

    def kill_all_client_threads(self):
        """Kill all active client threads"""
        with self.thread_lock:
            peers = list(self.client_threads.keys())

        killed_count = 0
        for peername in peers:
            if self.kill_client_thread(peername):
                killed_count += 1

        return killed_count

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
            chandlers["is_active"] = False

            if handler:
                handler(chandlers)

            peername = chandlers["peername"]

            # Unregister thread
            self._unregister_client_thread(peername)

            # Remove from client handlers
            if peername in self.client_handlers:
                del self.client_handlers[peername]

    def _handle_event(self, event_name, *args, **kwargs):
        handler = self._event_handlers.get(event_name)
        if event_name == "error" and isinstance(args[0], Clientype):
            args[0].last_error = traceback.format_exc()

        if event_name == "disconnected":
            self.handle_client_disconnection(handler, *args, **kwargs)
        elif handler:
            return handler(*args, **kwargs)

    def _create_session(self, socketchannel, addr):
        self._handle_event("preserver", socketchannel)

        logger.info("Starting session...")
        server = Sinterface(self, addr)

        if not self.__custom_server:
            if self._protocol.lower() == "telnet":
                bh_session = TelnetTransport(socketchannel, server)  # Telnet server
            else:
                bh_session = SSHTransport(socketchannel, server, self.private_key)  # SSH server
        else:
            bh_session = self.__custom_server(socketchannel, server, *self.__custom_server_args)  # custom server

        # Register the current thread
        current_thread = threading.current_thread()
        self._register_client_thread(addr, current_thread)

        try:
            self._handle_client(bh_session)
        finally:
            # Unregister when done
            self._unregister_client_thread(addr)

    def _handle_client(self, bh_session: ITransport, session_type="pty"):
        bh_session.enable_compression(self.compressena)

        bh_session.max_packet_size(self.max_bandwidth)

        try:
            bh_session.start_server()
        except:
            return

        channel = bh_session.accept()

        if self.sftpena and session_type != "tty":
            bh_session.set_subsystem_handler('sftp', paramiko.SFTPServer, SSHSFTPServer, channel, self.accounts, self.client_handlers)

        if not bh_session.is_authenticated():
            logger.warning("user not authenticated")
            bh_session.close()

            if session_type == "tty":
                self.__is_tty_connected = False
            return

        if channel is None:
            logger.warning("no channel")
            bh_session.close()

            if session_type == "tty":
                self.__is_tty_connected = False
            return

        try:
            logger.info("user authenticated")
            peername = bh_session.getpeername()
            if peername not in self.client_handlers:
                # Create a new event handler for this client if it doesn't exist
                self.client_handlers[peername] = Clientype(channel, bh_session, peername, self)

            client_handler = self.client_handlers[peername]
            client_handler["current_user"] = bh_session.get_username()
            client_handler["channel"] = channel  # Update the channel attribute for the client handler
            client_handler["transport"] = bh_session  # Update the channel attribute for the client handler
            client_handler["last_activity_time"] = time.time()
            client_handler["last_login_time"] = time.time()
            client_handler["prompt"] = self.accounts.get_prompt(bh_session.get_username())
            client_handler["session_id"] = random.randint(10000, 99999) + int(time.time() * 1000)
            client_handler["is_active"] = True

            self.accounts.set_user_last_login(client_handler["current_user"], peername[0])

            if session_type == "tty":
                client_handler["windowsize"] = {
                    "width": 80,
                    "height": 24,
                    "pixelwidth": 0,
                    "pixelheight": 0
                }

            logger.info("saved user data to client handlers")
            # timeout for waiting 0.1 sec for SFTP
            if self.sftpena and session_type != "tty":
                logger.info("waiting connection type...")
                time.sleep(0.1)

            if client_handler["connecttype"] != "SFTP":
                client_handler["session_type"] = session_type
                logger.info("use shell session")
                #timeout for waiting 10 sec
                for i in range(100):
                    if client_handler["windowsize"]:
                        break
                    time.sleep(0.1)

                if client_handler["windowsize"] == {} and session_type != "tty":
                    logger.info("timeout for waiting window size in 10 sec")
                    client_handler["windowsize"] = {
                        "width": 80,
                        "height": 24,
                        "pixelwidth": 0,
                        "pixelheight": 0
                    }

                try:
                    self._handle_event("pre-shell", client_handler)
                except Exception as e:
                    self._handle_event("error", client_handler, e)
                finally:
                    # check if still connect
                    if not client_handler.transport.is_active():
                        self._handle_event("disconnected", client_handler)
                        channel.close()
                        bh_session.close()

                while client_handler["isexeccommandrunning"]:
                    time.sleep(0.1)

                userbanner = self.accounts.get_banner(client_handler["current_user"])

                if self.accounts.get_user_enable_inputsystem_echo(client_handler["current_user"]) and self.inputsysecho:
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

                client_handler["connecttype"] = bh_session.get_connection_type()

                try:
                    self._handle_event("connect", client_handler)
                except Exception as e:
                    self._handle_event("error", client_handler, e)

                if self.enainputsystem and self.accounts.get_user_enable_inputsystem(client_handler["current_user"]):
                    try:
                        if self.accounts.get_user_timeout(client_handler["current_user"]) != None:
                            channel.setblocking(False)
                            channel.settimeout(self.accounts.get_user_timeout(client_handler["current_user"]))

                        if echo:
                            channel.send(replace_enter_with_crlf(client_handler["prompt"] + " "))

                        isConnect = True

                        while isConnect:
                            isConnect = expect(self, client_handler, echo)

                        #self._handle_event("disconnected", client_handler)
                        channel.close()
                        bh_session.close()

                        if session_type == "tty":
                            self.__is_tty_connected = False
                    except KeyboardInterrupt:
                        self._handle_event("disconnected", client_handler)
                        channel.close()
                        bh_session.close()
                    except Exception as e:
                        self._handle_event("error", client_handler, e)
                        logger.error(e)
                    finally:
                        self._handle_event("disconnected", client_handler)
                        channel.close()
                        bh_session.close()
            else:
                if self.sftpena:
                    client_handler["session_type"] = "sftp"
                    logger.info("user is sftp")
                    if self.accounts.get_user_sftp_allow(client_handler["current_user"]):
                        self._handle_event("connectsftp", client_handler)
                        while bh_session.is_active():
                            time.sleep(0.1)

                        self._handle_event("disconnected", client_handler)
                    else:
                        self._handle_event("disconnected", client_handler)
                        channel.close()
                else:
                    self._handle_event("disconnected", client_handler)
                    channel.close()
        except:
            bh_session.close()

    def stop_server(self):
        """Stop server"""
        logger.info("Stopping the server...")
        try:
            self.isrunning = False
            self.kill_all_client_threads()

            self.server.close()

            logger.info("Server stopped.")
        except Exception as e:
            logger.error(f"Error occurred while stopping the server: {e}")

    def _start_listening_thread(self):
        try:
            self.isrunning = True
            logger.info("Listening for connections...")
            while self.isrunning:
                try:
                    client, addr = self.server.accept()
                    if self.__processmode == "thread":
                        logger.info(f"Starting client thread for connection {addr}")
                        client_thread = threading.Thread(target=self._create_session, args=(client, addr), daemon=True)
                        client_thread.start()
                    else:
                        logger.info(f"Starting client for connection {addr}")
                        self._create_session(client, addr)
                except KeyboardInterrupt:
                    self.stop_server()
                    break
        except Exception as e:
            logger.error(e)

    def tty(self, stdin=None, stdout=None, stderr=None, thread=True, daemon=True):
        """Create TTY session"""
        if self.__is_tty_connected:
            raise ConnectionError("TTY session is already connected")

        logger.info("Starting TTY session...")
        server = Sinterface(self, ("TTY", 0))
        session = TTYTransport(None, server, self.hostname)
        if stdin:
            session.socket.stdin = stdin
        if stdout:
            session.socket.stdout = stdout
        if stderr:
            session.socket.stderr = stderr

        if thread:
            client_thread = threading.Thread(target=self._handle_client, args=(session, "tty"), daemon=daemon)
            client_thread.start()
        else:
            self._handle_client(session, "tty")

        self.__is_tty_connected = True

        if not self.isrunning:
            self.isrunning = True

    def run(self, private_key_path=None, host="0.0.0.0", port=2222, ipv6=False, allow_ipv4_in_ipv6=True, waiting_mode="thread", maxuser=0, daemon=False, listen_thread=True, protocol="ssh", custom_server: ITransport = None, custom_server_args: tuple = (), custom_server_require_socket=True):
        """mode: single, thread,
        protocol: ssh, telnet (beta), serial, custom

        * enable IPv6 can improve connection speed. Use "::" at host if enable IPv6
        """
        if protocol.lower() == "ssh":
            if private_key_path != None:
                logger.info("Loading private key")
                self.private_key = paramiko.RSAKey(filename=private_key_path)
            else:
                raise ValueError("No private key")

        self.__processmode = waiting_mode.lower()
        self._protocol = protocol.lower()
        self.__daemon = daemon

        if custom_server:
            self.__custom_server = custom_server
            self.__custom_server_args = custom_server_args

        self.startuptime = time.time()

        if ((custom_server and protocol.lower() == "custom") and custom_server_require_socket) or protocol.lower() in ["ssh", "telnet"]:
            logger.info("Creating server...")
            if ipv6:
                self.server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                if allow_ipv4_in_ipv6:
                    self.server.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
            else:
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
