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

from ..interactive import Send
from .ProWrapper import IChannel, ITransport

class Client:
    def __init__(self, channel, transport, peername):
        """
        Initializes a new client instance.

        Args:
            channel (IChannel): The communication channel for the client.
            transport (ITransport): The transport layer for the client.
            peername (tuple): The peer's address and port (host, port).
        """
        self.current_user = None
        self.transport: ITransport = transport
        self.channel: IChannel = channel
        self.subchannel = {}
        self.connecttype = None
        self.last_activity_time = None
        self.last_login_time = None
        self.windowsize = {}
        self.x11 = {}
        self.prompt = None
        self.inputbuffer = None
        self.peername = peername
        self.auth_method = self.transport.get_auth_method()
        self.session_id = None
        self.terminal_type = None
        self.env_variables = {}
        self.last_error = None
        self.last_command = None
        self.isexeccommandrunning = False

    def get_id(self):
        """
        Retrieves the client's session ID.

        Returns:
            str or None: The session ID of the client.
        """
        return self.session_id

    def get_name(self):
        """
        Retrieves the current username of the client.

        Returns:
            str: The current username of the client.
        """
        return self.current_user

    def get_peername(self):
        """
        Retrieves the peer's address (host, port) for the client.

        Returns:
            tuple: The peer's address (host, port).
        """
        return self.peername

    def get_prompt(self):
        """
        Retrieves the prompt string for the client.

        Returns:
            str: The prompt string for the client.
        """
        return self.prompt

    def get_channel(self):
        """
        Retrieves the communication channel for the client.

        Returns:
            IChannel: The channel instance for the client.
        """
        return self.channel

    def get_prompt_buffer(self):
        """
        Retrieves the current input buffer for the client as a string.

        Returns:
            str: The input buffer as a string.
        """
        return str(self.inputbuffer)

    def get_terminal_size(self):
        """
        Retrieves the terminal size (width, height) for the client.

        Returns:
            tuple[int, int]: The terminal's width and height.
        """
        return self.windowsize["width"], self.windowsize["height"]

    def get_connection_type(self):
        """
        Retrieves the connection type for the client.

        Returns:
            str: The connection type (e.g., TCP, UDP).
        """
        return self.connecttype

    def get_auth_with(self):
        """
        Retrieves the authentication method used for the client.

        Returns:
            str: The authentication method (e.g., password, public key).
        """
        return self.auth_method

    def get_session_duration(self):
        """
        Calculates the duration of the current session for the client.

        Returns:
            float: The duration of the session in seconds.
        """
        return time.time() - self.last_login_time

    def get_environment(self, variable):
        """
        Retrieves the value of an environment variable for the client.

        Args:
            variable (str): The name of the environment variable.

        Returns:
            str: The value of the environment variable.
        """
        return self.env_variables.get(variable)

    def get_last_error(self):
        """
        Retrieves the last error message encountered by the client.

        Returns:
            str: The last error message, or None if no error occurred.
        """
        return self.last_error

    def get_last_command(self):
        """
        Retrieves the last command executed by the client.

        Returns:
            str: The last command executed.
        """
        return self.last_command

    def set_name(self, name):
        """
        Sets the current username for the client.

        Args:
            name (str): The username to set for the client.
        """
        self.current_user = name

    def set_prompt(self, prompt):
        """
        Sets the prompt string for the client.

        Args:
            prompt (str): The prompt string to set for the client.
        """
        self.prompt = prompt

    def set_environment(self, variable, value):
        """
        Sets the value of an environment variable for the client.

        Args:
            variable (str): The name of the environment variable.
            value (str): The value to set for the environment variable.
        """
        self.env_variables[variable] = value

    def open_new_subchannel(self, timeout=None):
        """
        Opens a new subchannel for communication with the client.

        Args:
            timeout (Union[int, None]): The timeout duration in seconds.
                                         If None, the operation waits indefinitely.

        Returns:
            tuple: A tuple containing the subchannel ID and the new subchannel
                   (IChannel). If an error occurs, returns (None, None).
        """
        try:
            channel = self.transport.accept(timeout)
            id = channel.get_id()
        except:
            return None, None

        self.subchannel[id] = channel
        return id, channel

    def get_subchannel(self, id):
        """
        Retrieves a subchannel by its ID.

        Args:
            id (int): The ID of the subchannel to retrieve.

        Returns:
            IChannel: The subchannel instance.
        """
        return self.subchannel.get(id)

    def switch_user(self, user):
        """
        Switches the current user for the client.

        Args:
            user (str): The new username to switch to.
        """
        self.current_user = user
        self.transport.set_username(user)

    def close_subchannel(self, id):
        """
        Closes a specific subchannel by its ID.

        Args:
            id (int): The ID of the subchannel to close.
        """
        self.subchannel[id].close()

    def close(self):
        """
        Closes the main communication channel for the client.
        """
        self.channel.close()

    def send(self, data):
        """
        Sends data over the main communication channel.

        Args:
            data (str): The data to send.
        """
        Send(self.channel, data, directchannel=True, ln=False)

    def sendln(self, data):
        """
        Sends data over the main communication channel.

        Args:
            data (str): The data to send.
        """
        Send(self.channel, data, directchannel=True)

    def __str__(self):
        return f"client id: {self.session_id}"

    def __repr__(self):
        attrs = vars(self)  # or self.__dict__

        non_none_attrs = {key: value for key, value in attrs.items() if value is not None}

        attrs_repr = ', '.join(f"{key}={value!r}" for key, value in non_none_attrs.items())
        return f"Client({attrs_repr})"

    # for backward compatibility only
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)
