"""
PyserSSH - A SSH server. For more info visit https://github.com/damp11113/PyserSSH
Copyright (C) 2023-2024 damp11113 (MIT)

Visit https://github.com/damp11113/PyserSSH

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

import paramiko

class Sinterface(paramiko.ServerInterface):
    def __init__(self, serverself):
        self.current_user = None
        self.serverself = serverself

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        data = {
            "username": username,
            "password": password,
        }

        if self.serverself.accounts.validate_credentials(username, password) and not self.serverself.usexternalauth:
            self.current_user = username  # Store the current user upon successful authentication
            return paramiko.AUTH_SUCCESSFUL
        else:
            if self.serverself._handle_event("auth", data):
                self.current_user = username  # Store the current user upon successful authentication
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        data = {
            "term": term,
            "width": width,
            "height": height,
            "pixelwidth": pixelwidth,
            "pixelheight": pixelheight,
            "modes": modes
        }
        data2 = {
            "width": width,
            "height": height,
            "pixelwidth": pixelwidth,
            "pixelheight": pixelheight,
        }
        try:
            self.serverself.client_handlers[channel.getpeername()]["windowsize"] = data2
            self.serverself._handle_event("connectpty", self.serverself.client_handlers[channel.getpeername()], data)
        except:
            pass

        return True

    def check_channel_shell_request(self, channel):
        return True

    def check_channel_x11_request(self, channel, single_connection, auth_protocol, auth_cookie, screen_number):
        data = {
            "single_connection": single_connection,
            "auth_protocol": auth_protocol,
            "auth_cookie": auth_cookie,
            "screen_number": screen_number
        }
        try:
            self.serverself.client_handlers[channel.getpeername()]["x11"] = data
            self.serverself._handle_event("connectx11", self.serverself.client_handlers[channel.getpeername()], data)
        except:
            pass

        return True

    def check_channel_window_change_request(self, channel, width: int, height: int, pixelwidth: int, pixelheight: int):
        data = {
            "width": width,
            "height": height,
            "pixelwidth": pixelwidth,
            "pixelheight": pixelheight
        }
        self.serverself.client_handlers[channel.getpeername()]["windowsize"] = data
        self.serverself._handle_event("resized", self.serverself.client_handlers[channel.getpeername()], data)
