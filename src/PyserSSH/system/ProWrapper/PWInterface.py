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

import socket
import paramiko
from abc import ABC, abstractmethod
from typing import Union

from PyserSSH.system.interface import Sinterface


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

    @abstractmethod
    def get_interface(self) -> "Sinterface":
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