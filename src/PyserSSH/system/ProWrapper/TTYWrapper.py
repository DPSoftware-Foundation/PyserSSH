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
import random
import sys
import os
import platform
import time

# Platform-specific imports
if platform.system() != 'Windows':
    import select
    import tty
    import termios
else:
    import msvcrt

from .PWInterface import ITransport, IChannel
from ..interface import Sinterface
from ...interactive import wait_input, Send


class stdsocket:
    def __init__(self):
        self.stdin = sys.stdin.buffer
        self.stdout = sys.stdout.buffer
        self.stderr = sys.stderr.buffer
        self.timeout = None
        self.blocking = True
        self.is_windows = platform.system() == 'Windows'
        self.is_closed = False
        self.peername = ("TTY", random.randint(10000, 99999))

        # Save original terminal settings (Unix only)
        if not self.is_windows:
            self.is_tty = os.isatty(sys.stdin.fileno())
            if self.is_tty:
                self.old_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())
        else:
            self.is_tty = True

    def send(self, s):
        if self.is_closed:
            raise OSError("Socket is closed")

        if isinstance(s, str):
            s = s.encode('utf-8')
        self.stdout.write(s)
        self.stdout.flush()

    def sendall(self, s):
        if self.is_closed:
            raise OSError("Socket is closed")

        if isinstance(s, str):
            s = s.encode('utf-8')
        self.stdout.write(s)
        self.stdout.flush()

    def _recv_unix(self, nbytes):
        """Unix/Linux/Mac implementation using select"""
        if not self.blocking:
            timeout = 0
        else:
            timeout = self.timeout

        try:
            ready, _, _ = select.select([self.stdin], [], [], timeout)

            if ready:
                data = self.stdin.read(nbytes)
                return data if isinstance(data, bytes) else data.encode('utf-8')
            else:
                if not self.blocking:
                    return b''
                else:
                    raise TimeoutError("Socket timeout during recv()")
        except (AttributeError, OSError):
            data = self.stdin.read(nbytes)
            return data if isinstance(data, bytes) else data.encode('utf-8')

    def _recv_windows(self, nbytes):
        """Windows implementation using msvcrt"""
        result = b""
        start_time = time.time()

        while len(result) < nbytes:
            # Check for timeout
            if self.timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    if not self.blocking or len(result) == 0:
                        if self.blocking:
                            raise TimeoutError("Socket timeout during recv()")
                        return result

            # Check if key is available
            if msvcrt.kbhit():
                char = msvcrt.getch()
                result += char

                # If we got all requested bytes, return
                if len(result) >= nbytes:
                    return result
            else:
                # No key available
                if not self.blocking:
                    return result
                # In blocking mode, sleep briefly to avoid busy waiting
                time.sleep(0.01)

        return result

    def recv(self, nbytes):
        """
        Receive up to nbytes from stdin.
        Respects timeout and blocking settings.
        Returns bytes.
        """
        if self.is_closed:
            raise OSError("Socket is closed")

        if self.is_windows:
            return self._recv_windows(nbytes)
        else:
            return self._recv_unix(nbytes)

    def settimeout(self, timeout):
        """
        Set timeout for blocking operations.

        Args:
            timeout: Float (seconds), None (blocking), or 0 (non-blocking)
        """
        if self.is_closed:
            raise OSError("Socket is closed")

        if timeout is None:
            self.blocking = True
            self.timeout = None
        elif timeout == 0:
            self.blocking = False
            self.timeout = 0
        else:
            self.blocking = True
            self.timeout = float(timeout)

    def setblocking(self, blocking):
        """
        Set blocking mode.

        Args:
            blocking: True for blocking, False for non-blocking
        """
        if self.is_closed:
            raise OSError("Socket is closed")

        self.blocking = bool(blocking)
        if not blocking:
            self.timeout = 0
        elif self.timeout == 0:
            self.timeout = None

    def close(self):
        """
        Close the socket and restore terminal settings.
        """
        if not self.is_windows and self.is_tty and hasattr(self, 'old_settings'):
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

        self.is_closed = True

    def get_peername(self):
        if self.is_closed:
            raise OSError("Socket is closed")

        return self.peername

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

class TTYTransport(ITransport):
    def __init__(self, _, interface: Sinterface, hostname=None):
        self.socket = stdsocket()
        self.interface: Sinterface = interface
        self.username = None
        self.isactive = True
        self.isauth = False
        self.auth_method = None
        self.hostname = hostname

    def enable_compression(self, enable):
        pass

    def max_packet_size(self, size):
        pass

    def start_server(self):
        pass

    def set_subsystem_handler(self, name: str, handler: callable, *args: any, **kwargs: any) -> None:
        pass

    def accept(self, timeout=None):
        # Simple authentication prompt
        while True:
            username = wait_input(self.socket, f"{self.hostname} login: ", directchannel=True)

            if username:
                break

        try:
            allowauth = self.interface.get_allowed_auths(username).split(',')
        except:
            allowauth = self.interface.get_allowed_auths(username)

        if allowauth[0] == "password":
            password = wait_input(self.socket, "Password: ", password=True, directchannel=True)
            result = self.interface.check_auth_password(username, password)

            if result == 0:
                self.isauth = True
                self.username = username
                self.auth_method = "password"
                return TTYChannel(self.socket)
            else:
                Send(self.socket, "Access denied", directchannel=True)
                self.close()
        elif allowauth[0] == "public_key":
            Send(self.socket, "Public key isn't supported for tty", directchannel=True)
            self.close()
        elif allowauth[0] == "none":
            result = self.interface.check_auth_none(username)

            if result == 0:
                self.username = username
                self.isauth = True
                self.auth_method = "none"
                return TTYChannel(self.socket)
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
        return self.socket.get_peername()

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
        return "TTY"

    def get_interface(self):
        return self.interface

class TTYChannel(IChannel):
    def __init__(self, channel: stdsocket):
        self.channel = channel

    def send(self, s):
        self.channel.send(s)

    def sendall(self, s):
        self.channel.sendall(s)

    def getpeername(self):
        return self.channel.get_peername()

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