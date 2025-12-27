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

from .PWInterface import ITransport, IChannel
from ..interface import Sinterface
from ...interactive import wait_input, Send, wait_input_old

# Telnet command codes (RFC 854)
IAC = 255  # Interpret As Command
DONT = 254  # Don't perform option
DO = 253  # Do perform option
WONT = 252  # Won't perform option
WILL = 251  # Will perform option
SB = 250  # Subnegotiation begin
SE = 240  # Subnegotiation end
NOP = 241  # No operation
DM = 242  # Data Mark
BRK = 243  # Break
IP = 244  # Interrupt Process
AO = 245  # Abort Output
AYT = 246  # Are You There
EC = 247  # Erase Character
EL = 248  # Erase Line
GA = 249  # Go Ahead

# Telnet option codes (RFC 855 and others)
ECHO = 1  # RFC 857
SGA = 3  # Suppress Go Ahead - RFC 858
STATUS = 5  # RFC 859
TTYPE = 24  # Terminal Type - RFC 1091
NAWS = 31  # Negotiate About Window Size - RFC 1073
LINEMODE = 34  # RFC 1184
ENVIRON = 36  # RFC 1408

def send_telnet_command(sock, command, option):
    """Send a Telnet command with option"""
    try:
        sock.send(bytes([IAC, command, option]))
    except:
        pass

def send_telnet_subnegotiation(sock, option, data):
    """Send a Telnet subnegotiation"""
    try:
        sock.send(bytes([IAC, SB, option]) + data + bytes([IAC, SE]))
    except:
        pass

class TelnetTransport(ITransport):
    def __init__(self, socketchannel: socket.socket, interface: Sinterface):
        self.socket: socket.socket = socketchannel
        self.interface: Sinterface = interface
        self.username = None
        self.isactive = True
        self.isauth = False
        self.auth_method = None
        self.terminal_type = "UNKNOWN"
        self.options_negotiated = False
        self.term_size = (80, 24)  # Default terminal size (cols, rows)

        # Track negotiated options
        self.local_options = {}  # Options we've agreed to WILL
        self.remote_options = {}  # Options client has agreed to DO

    def enable_compression(self, enable):
        pass

    def max_packet_size(self, size):
        pass

    def start_server(self):
        pass

    def set_subsystem_handler(self, name: str, handler: callable, *args: any, **kwargs: any) -> None:
        pass

    def negotiate_options(self):
        """Negotiate Telnet options with the client"""
        # Tell client we WILL ECHO (server handles echoing)
        send_telnet_command(self.socket, WILL, ECHO)
        self.local_options[ECHO] = True

        # Tell client we WILL suppress go-ahead
        send_telnet_command(self.socket, WILL, SGA)
        self.local_options[SGA] = True

        # Ask client to DO terminal type negotiation
        send_telnet_command(self.socket, DO, TTYPE)

        # Ask client to DO window size negotiation
        send_telnet_command(self.socket, DO, NAWS)

        # Process initial responses with timeout
        self.socket.settimeout(2.0)
        self._process_telnet_negotiation()
        self.socket.settimeout(None)

        self.options_negotiated = True

    def _process_telnet_negotiation(self):
        """Process Telnet negotiation responses"""
        buffer = b''
        try:
            while True:
                data = self.socket.recv(1024)
                if not data:
                    break
                buffer += data

                # Process all complete commands in buffer
                while len(buffer) >= 3 and buffer[0] == IAC:
                    if buffer[1] in [WILL, WONT, DO, DONT]:
                        # Simple negotiation command
                        self._handle_negotiation(buffer[1], buffer[2])
                        buffer = buffer[3:]
                    elif buffer[1] == SB:
                        # Subnegotiation - find the end
                        se_pos = buffer.find(bytes([IAC, SE]))
                        if se_pos != -1:
                            self._handle_subnegotiation(buffer[2:se_pos])
                            buffer = buffer[se_pos + 2:]
                        else:
                            break  # Incomplete subnegotiation
                    else:
                        # Other commands - just skip
                        buffer = buffer[2:]

                # If buffer doesn't start with IAC, we're done negotiating
                if buffer and buffer[0] != IAC:
                    break

        except socket.timeout:
            pass  # Normal - negotiation timeout
        except:
            pass

    def _handle_negotiation(self, command, option):
        """Handle WILL, WONT, DO, DONT commands"""
        if command == WILL:
            # Client agrees to enable an option
            if option == TTYPE:
                send_telnet_command(self.socket, DO, TTYPE)
                self.remote_options[TTYPE] = True
                # Request terminal type
                send_telnet_subnegotiation(self.socket, TTYPE, bytes([1]))  # SEND
            elif option == NAWS:
                send_telnet_command(self.socket, DO, NAWS)
                self.remote_options[NAWS] = True
            else:
                # Accept other options
                send_telnet_command(self.socket, DO, option)
                self.remote_options[option] = True

        elif command == WONT:
            # Client refuses to enable an option
            if option in self.remote_options:
                del self.remote_options[option]
            send_telnet_command(self.socket, DONT, option)

        elif command == DO:
            # Client wants us to enable an option
            if option in [ECHO, SGA]:
                # We already agreed to these
                send_telnet_command(self.socket, WILL, option)
            else:
                # Refuse other options
                send_telnet_command(self.socket, WONT, option)

        elif command == DONT:
            # Client doesn't want us to enable an option
            if option in self.local_options:
                del self.local_options[option]
            send_telnet_command(self.socket, WONT, option)

    def _handle_subnegotiation(self, data):
        """Handle subnegotiation data"""
        if len(data) < 2:
            return

        option = data[0]
        subdata = data[1:]

        if option == TTYPE and len(subdata) >= 2:
            # Terminal type response: IS (0) followed by type name
            if subdata[0] == 0:
                self.terminal_type = subdata[1:].decode('ascii', errors='ignore')

        elif option == NAWS and len(subdata) == 4:
            # Window size: 2 bytes width, 2 bytes height
            width = (subdata[0] << 8) | subdata[1]
            height = (subdata[2] << 8) | subdata[3]
            self.term_size = (width, height)


    def accept(self, timeout=None):
        """Accept and authenticate a Telnet connection"""
        # Perform Telnet negotiation
        self.negotiate_options()

        channel = TelnetChannel(self.socket, self)

        # Simple authentication prompt
        username = wait_input(channel, "Login as: ", directchannel=True)

        try:
            allowauth = self.interface.get_allowed_auths(username).split(',')
        except:
            allowauth = self.interface.get_allowed_auths(username)

        if allowauth[0] == "password":
            password = wait_input_old(channel, "Password", password=True, directchannel=True)
            result = self.interface.check_auth_password(username, password)

            if result == 0:
                self.isauth = True
                self.username = username
                self.auth_method = "password"
                self.interface.check_channel_pty_request(TelnetChannel(self.socket, self), self.terminal_type.encode("UTF-8"), self.term_size[0], self.term_size[1], 0, 0, b'tn')
                return channel
            else:
                Send(channel, "Access denied\r\n", directchannel=True)
                self.close()
        elif allowauth[0] == "public_key":
            Send(channel, "Public key isn't supported for telnet\r\n", directchannel=True)
            self.close()
        elif allowauth[0] == "none":
            result = self.interface.check_auth_none(username)

            if result == 0:
                self.username = username
                self.isauth = True
                self.auth_method = "none"
                self.interface.check_channel_pty_request(TelnetChannel(self.socket, self), self.terminal_type.encode("UTF-8"), self.term_size[0], self.term_size[1], 0, 0, b'tn')
                return channel
            else:
                Send(channel, "Access denied\r\n", directchannel=True)
                self.close()
        else:
            Send(channel, "Access denied\r\n", directchannel=True)

    def close(self):
        """Close the transport"""
        self.isactive = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self.socket.close()
        except:
            pass

    def is_authenticated(self):
        return self.isauth

    def getpeername(self):
        try:
            return self.socket.getpeername()
        except:
            return ("unknown", 0)

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

    def get_interface(self):
        return self.interface

class TelnetChannel(IChannel):
    def __init__(self, channel: socket.socket, transport: TelnetTransport = None):
        self.channel: socket.socket = channel
        self.transport = transport
        self.recv_buffer = b''

    def _filter_telnet_commands(self, data):
        """Filter out Telnet commands from received data"""
        result = b''
        i = 0
        while i < len(data):
            if data[i] == IAC and i + 1 < len(data):
                if data[i + 1] == IAC:
                    # Escaped IAC - add single IAC to result
                    result += bytes([IAC])
                    i += 2
                elif data[i + 1] in [WILL, WONT, DO, DONT]:
                    # Skip 3-byte negotiation
                    if self.transport:
                        self.transport._handle_negotiation(data[i + 1], data[i + 2])
                    i += 3
                elif data[i + 1] == SB:
                    # Skip subnegotiation
                    se_pos = data.find(bytes([IAC, SE]), i)
                    if se_pos != -1:
                        if self.transport:
                            self.transport._handle_subnegotiation(data[i + 2:se_pos])
                        i = se_pos + 2
                    else:
                        i += 2
                else:
                    # Skip 2-byte command
                    i += 2
            else:
                result += bytes([data[i]])
                i += 1
        return result

    def send(self, s):
        """Send data, escaping IAC bytes"""
        if isinstance(s, str):
            s = s.encode('utf-8')
        # Escape IAC bytes by doubling them
        s = s.replace(bytes([IAC]), bytes([IAC, IAC]))
        return self.channel.send(s)

    def sendall(self, s):
        """Send all data, escaping IAC bytes"""
        if isinstance(s, str):
            s = s.encode('utf-8')
        # Escape IAC bytes by doubling them
        s = s.replace(bytes([IAC]), bytes([IAC, IAC]))
        self.channel.sendall(s)

    def getpeername(self):
        try:
            return self.channel.getpeername()
        except:
            return ("unknown", 0)

    def settimeout(self, timeout):
        self.channel.settimeout(timeout)

    def setblocking(self, blocking):
        self.channel.setblocking(blocking)

    def recv(self, nbytes):
        """Receive data and filter out Telnet commands"""
        data = self.channel.recv(nbytes)
        if not data:
            return data

        # Add to buffer and filter
        self.recv_buffer += data
        filtered = self._filter_telnet_commands(self.recv_buffer)
        self.recv_buffer = b''  # Clear buffer after filtering

        return filtered

    def get_id(self):
        return 0

    def close(self) -> None:
        try:
            self.channel.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            return self.channel.close()
        except:
            pass

    def get_out_window_size(self) -> int:
        return 0

    def get_specific_protocol_channel(self):
        return self.channel