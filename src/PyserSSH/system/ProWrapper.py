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

#import serial
import socket
import paramiko
from abc import ABC, abstractmethod
from typing import Union, Literal

from .interface import Sinterface
from ..interactive import Send, wait_input

class ITransport(ABC):
    @abstractmethod
    def enable_compression(self, enable: bool) -> None:
        """
        Enables or disables data compression for the transport.

        Args:
            enable (bool): If True, enable compression. If False, disable it.
        """
        pass

    @abstractmethod
    def max_packet_size(self, size: int) -> None:
        """
        Sets the maximum packet size for the transport.

        Args:
            size (int): The maximum packet size in bytes.
        """
        pass

    @abstractmethod
    def start_server(self) -> None:
        """
        Starts the server for the transport, allowing it to accept incoming connections.
        """
        pass

    @abstractmethod
    def accept(self, timeout: Union[int, None] = None) -> "IChannel":
        """
        Accepts an incoming connection and returns an IChannel instance for communication.

        Args:
            timeout (Union[int, None]): The time in seconds to wait for a connection.
                                          If None, waits indefinitely.

        Returns:
            IChannel: An instance of IChannel representing the connection.
        """
        pass

    @abstractmethod
    def set_subsystem_handler(self, name: str, handler: callable, *args: any, **kwargs: any) -> None:
        """
        Sets a handler for a specific subsystem in the transport.

        Args:
            name (str): The name of the subsystem.
            handler (callable): The handler function to be called for the subsystem.
            *args: Arguments to pass to the handler.
            **kwargs: Keyword arguments to pass to the handler.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Closes the transport connection, releasing any resources used.
        """
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Checks if the transport is authenticated.

        Returns:
            bool: True if the transport is authenticated, otherwise False.
        """
        pass

    @abstractmethod
    def getpeername(self) -> tuple[str, int]:  # (host, port)
        """
        Retrieves the peer's address and port.

        Returns:
            tuple[str, int]: The host and port of the peer.
        """
        pass

    @abstractmethod
    def get_username(self) -> str:
        """
        Retrieves the username associated with the transport.

        Returns:
            str: The username.
        """
        pass

    @abstractmethod
    def is_active(self) -> bool:
        """
        Checks if the transport is active.

        Returns:
            bool: True if the transport is active, otherwise False.
        """
        pass

    @abstractmethod
    def get_auth_method(self) -> str:
        """
        Retrieves the authentication method used for the transport.

        Returns:
            str: The authentication method (e.g., password, public key).
        """
        pass

    @abstractmethod
    def set_username(self, username: str) -> None:
        """
        Sets the username for the transport.

        Args:
            username (str): The username to be set.
        """
        pass

    @abstractmethod
    def get_default_window_size(self) -> int:
        """
        Retrieves the default window size for the transport.

        Returns:
            int: The default window size.
        """
        pass

    @abstractmethod
    def get_connection_type(self) -> str:
        """
        Retrieves the type of connection for the transport.

        Returns:
            str: The connection type (e.g., TCP, UDP).
        """
        pass

class IChannel(ABC):
    @abstractmethod
    def send(self, s: Union[bytes, bytearray]) -> None:
        """
        Sends data over the channel.

        Args:
            s (Union[bytes, bytearray]): The data to send.
        """
        pass

    @abstractmethod
    def sendall(self, s: Union[bytes, bytearray]) -> None:
        """
        Sends all data over the channel, blocking until all data is sent.

        Args:
            s (Union[bytes, bytearray]): The data to send.
        """
        pass

    @abstractmethod
    def getpeername(self) -> tuple[str, int]:
        """
        Retrieves the peer's address and port.

        Returns:
            tuple[str, int]: The host and port of the peer.
        """
        pass

    @abstractmethod
    def settimeout(self, timeout: Union[float, None]) -> None:
        """
        Sets the timeout for blocking operations on the channel.

        Args:
            timeout (Union[float, None]): The timeout in seconds. If None, the operation will block indefinitely.
        """
        pass

    @abstractmethod
    def setblocking(self, blocking: bool) -> None:
        """
        Sets whether the channel operates in blocking mode or non-blocking mode.

        Args:
            blocking (bool): If True, the channel operates in blocking mode. If False, non-blocking mode.
        """
        pass

    @abstractmethod
    def recv(self, nbytes: int) -> bytes:
        """
        Receives data from the channel.

        Args:
            nbytes (int): The number of bytes to receive.

        Returns:
            bytes: The received data.
        """
        pass

    @abstractmethod
    def get_id(self) -> int:
        """
        Retrieves the unique identifier for the channel.

        Returns:
            int: The channel's unique identifier.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Closes the channel and releases any resources used.
        """
        pass

    @abstractmethod
    def get_out_window_size(self) -> int:
        """
        Retrieves the output window size for the channel.

        Returns:
            int: The output window size.
        """
        pass

    @abstractmethod
    def get_specific_protocol_channel(self) -> Union[socket.socket, paramiko.Channel]:
        """
        Get real channel from protocol you are using.
        """
        pass

#--------------------------------------------------------------------------------------------

class SSHTransport(ITransport):
    def __init__(self, socketchannel: socket.socket, interface: Sinterface, key):
        self.socket: socket.socket = socketchannel
        self.interface: Sinterface = interface
        self.key = key

        self.bh_session = paramiko.Transport(self.socket)
        self.bh_session.add_server_key(self.key)
        self.bh_session.default_window_size = 2147483647

    def enable_compression(self, enable):
        self.bh_session.use_compression(enable)

    def max_packet_size(self, size):
        self.bh_session.default_max_packet_size = size
        self.bh_session.default_window_size = size * 2

    def start_server(self):
        self.bh_session.start_server(server=self.interface)

    def accept(self, timeout=None):
        return SSHChannel(self.bh_session.accept(timeout))

    def set_subsystem_handler(self, name, handler, *args, **kwargs):
        self.bh_session.set_subsystem_handler(name, handler, *args, **kwargs)

    def close(self):
        self.bh_session.close()

    def is_authenticated(self):
        return self.bh_session.is_authenticated()

    def getpeername(self):
        return self.bh_session.getpeername()

    def get_username(self):
        return self.bh_session.get_username()

    def is_active(self):
        return self.bh_session.is_active()

    def get_auth_method(self):
        return self.bh_session.auth_handler.auth_method

    def set_username(self, username):
        self.bh_session.auth_handler.username = username

    def get_default_window_size(self):
        return self.bh_session.default_window_size

    def get_connection_type(self):
        return "SSH"

class SSHChannel(IChannel):
    def __init__(self, channel: paramiko.Channel):
        self.channel: paramiko.Channel = channel

    def send(self, s):
        self.channel.send(s)

    def sendall(self, s):
        self.channel.sendall(s)

    def getpeername(self):
        return self.channel.getpeername()

    def settimeout(self, timeout):
        self.channel.settimeout(timeout)

    def setblocking(self, blocking):
        self.channel.setblocking(blocking)

    def recv(self, nbytes):
        return self.channel.recv(nbytes)

    def get_id(self):
        return self.channel.get_id()

    def close(self):
        self.channel.close()

    def get_out_window_size(self):
        return self.channel.out_window_size

    def get_specific_protocol_channel(self):
        return self.channel

#--------------------------------------------------------------------------------------------

# Telnet command and option codes
IAC = 255
DO = 253
WILL = 251
TTYPE = 24
ECHO = 1
SGA = 3  # Suppress Go Ahead

def send_telnet_command(sock, command, option):
    sock.send(bytes([IAC, command, option]))

class TelnetTransport(ITransport):
    def __init__(self, socketchannel: socket.socket, interface: Sinterface):
        self.socket: socket.socket = socketchannel
        self.interface: Sinterface = interface
        self.username = None
        self.isactive = True
        self.isauth = False
        self.auth_method = None

    def enable_compression(self, enable):
        pass

    def max_packet_size(self, size):
        pass

    def start_server(self):
        pass

    def set_subsystem_handler(self, name: str, handler: callable, *args: any, **kwargs: any) -> None:
        pass

    def negotiate_options(self):
        # Negotiating TTYPE (Terminal Type), ECHO, and SGA (Suppress Go Ahead)
        send_telnet_command(self.socket, DO, TTYPE)
        send_telnet_command(self.socket, WILL, ECHO)
        send_telnet_command(self.socket, WILL, SGA)

    def accept(self, timeout=None):
        # Perform Telnet negotiation
        self.negotiate_options()

        # Simple authentication prompt
        username = wait_input(self.socket, "Login as: ", directchannel=True)

        try:
            allowauth = self.interface.get_allowed_auths(username).split(',')
        except:
            allowauth = self.interface.get_allowed_auths(username)

        if allowauth[0] == "password":
            password = wait_input(self.socket, "Password", password=True, directchannel=True)
            result = self.interface.check_auth_password(username, password)

            if result == 0:
                self.isauth = True
                self.username = username
                self.auth_method = "password"
                return TelnetChannel(self.socket)
            else:
                Send(self.socket, "Access denied", directchannel=True)
                self.close()
        elif allowauth[0] == "public_key":
            Send(self.socket, "Public key isn't supported for telnet", directchannel=True)
            self.close()
        elif allowauth[0] == "none":
            result = self.interface.check_auth_none(username)

            if result == 0:
                self.username = username
                self.isauth = True
                self.auth_method = "none"
                return TelnetChannel(self.socket)
            else:
                Send(self.socket, "Access denied", directchannel=True)
                self.close()
        else:
            Send(self.socket, "Access denied", directchannel=True)

    def close(self):
        self.isactive = False
        self.socket.close()

    def is_authenticated(self):
        return self.isauth

    def getpeername(self):
        return self.socket.getpeername()

    def get_username(self):
        return self.username

    def is_active(self):
        return self.isactive

    def get_auth_method(self):
        return self.auth_method

    def set_username(self, username):
        self.username = username

    def get_default_window_size(self):
        return 0

    def get_connection_type(self):
        return "Telnet"


class TelnetChannel(IChannel):
    def __init__(self, channel: socket.socket):
        self.channel: socket.socket = channel

    def send(self, s):
        self.channel.send(s)

    def sendall(self, s):
        self.channel.sendall(s)

    def getpeername(self):
        return self.channel.getpeername()

    def settimeout(self, timeout):
        self.channel.settimeout(timeout)

    def setblocking(self, blocking):
        self.channel.setblocking(blocking)

    def recv(self, nbytes):
        return self.channel.recv(nbytes)

    def get_id(self):
        return 0

    def close(self) -> None:
        return self.channel.close()

    def get_out_window_size(self) -> int:
        return 0

    def get_specific_protocol_channel(self):
        return self.channel