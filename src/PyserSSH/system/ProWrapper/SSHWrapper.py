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

from .PWInterface import ITransport, IChannel
from ..interface import Sinterface

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

    def get_interface(self):
        return self.interface

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