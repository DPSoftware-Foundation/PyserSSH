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
from paramiko.transport import Transport
from paramiko.channel import Channel

class Client:
    def __init__(self, channel, transport, peername):
        self.current_user = None
        self.transport: Transport = transport
        self.channel: Channel = channel
        self.subchannel = {}
        self.connecttype = None
        self.last_activity_time = None
        self.last_login_time = None
        self.windowsize = {}
        self.x11 = {}
        self.prompt = None
        self.inputbuffer = None
        self.peername = peername
        self.auth_method = self.transport.auth_handler.auth_method
        self.session_id = None
        self.terminal_type = None
        self.env_variables = {}
        self.last_error = None
        self.last_command = None
        self.isexeccommandrunning = False

    def get_id(self):
        return self.session_id

    def get_name(self):
        return self.current_user

    def get_peername(self):
        return self.current_user

    def get_prompt(self):
        return self.prompt

    def get_channel(self):
        return self.channel

    def get_prompt_buffer(self):
        return str(self.inputbuffer)

    def get_terminal_size(self):
        return self.windowsize["width"], self.windowsize["height"]

    def get_connection_type(self):
        return self.connecttype

    def get_auth_with(self):
        return self.auth_method

    def get_session_duration(self):
        return time.time() - self.last_login_time

    def get_environment(self, variable):
        return self.env_variables[variable]

    def get_last_error(self):
        return self.last_error

    def get_last_command(self):
        return self.last_command

    def set_name(self, name):
        self.current_user = name

    def set_prompt(self, prompt):
        self.prompt = prompt

    def set_environment(self, variable, value):
        self.env_variables[variable] = value

    def open_new_subchannel(self, timeout=None):
        try:
            channel = self.transport.accept(timeout)
            id = channel.get_id()
        except:
            return None, None

        self.subchannel[id] = channel
        return id, channel

    def get_subchannel(self, id):
        return self.subchannel[id]

    def switch_user(self, user):
        self.current_user = user
        self.transport.auth_handler.username = user

    def close_subchannel(self, id):
        self.subchannel[id].close()

    def close(self):
        self.channel.close()

    # for backward compatibility only
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __str__(self):
        return f"client id: {self.session_id}"

    def __repr__(self):
        # Get the dictionary of instance attributes
        attrs = vars(self)  # or self.__dict__

        # Filter out attributes that are None
        non_none_attrs = {key: value for key, value in attrs.items() if value is not None}

        # Build a string representation
        attrs_repr = ', '.join(f"{key}={value!r}" for key, value in non_none_attrs.items())
        return f"Client({attrs_repr})"