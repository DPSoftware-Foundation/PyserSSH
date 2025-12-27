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
import ast
import threading

from .syscom import systemcommand
from .RemoteStatus import startremotestatus
from .KeyInteract import InteractiveAuthManager


def parse_exec_request(command_string):
    try:
        # Remove the leading 'b' and convert bytes to string
        command_string = command_string.decode('utf-8')

        # Split the string into precommand and env parts
        try:
            parts = command_string.split(', ')
        except:
            parts = command_string.split(',')

        precommand_str = None
        env_str = None
        user_str = None

        for part in parts:
            if part.startswith('precommand='):
                precommand_str = part.split('=', 1)[1].strip()
            elif part.startswith('env='):
                env_str = part.split('=', 1)[1].strip()
            elif part.startswith('user='):
                user_str = part.split('=', 1)[1].strip()

        # Parse precommand using ast.literal_eval if present
        precommand = ast.literal_eval(precommand_str) if precommand_str else None

        # Parse env using ast.literal_eval if present
        env = ast.literal_eval(env_str) if env_str else None

        user = ast.literal_eval(user_str) if user_str else None

        return precommand, env, user

    except (ValueError, SyntaxError, TypeError) as e:
        # Handle parsing errors here
        print(f"Error parsing SSH command string: {e}")
        return None, None, None

def parse_exec_request_kwargs(command_string):
    try:
        # Remove the leading 'b' and convert bytes to string
        command_string = command_string.decode('utf-8')

        # Split the string into key-value pairs
        try:
            parts = command_string.split(', ')
        except:
            parts = command_string.split(',')

        kwargs = {}

        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                try:
                    value = ast.literal_eval(value.strip())
                except (ValueError, SyntaxError):
                    # If literal_eval fails, treat value as string
                    value = value.strip()
                kwargs[key] = value

        return kwargs

    except (ValueError, SyntaxError, TypeError) as e:
        # Handle parsing errors here
        print(f"Error parsing command kwargs: {e}")
        return {}

class Sinterface(paramiko.ServerInterface):
    def __init__(self, serverself, addr):
        self.serverself = serverself
        self.addr = addr

        self.IAM = None

    def check_channel_request(self, kind, channel_id):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        return self.serverself.accounts.get_allowed_auths(username)

    def check_auth_password(self, username, password):
        data = {
            "username": username,
            "password": password,
            "auth_type": "password",
            "addr": self.addr
        }

        if self.serverself.accounts.validate_credentials(username, password) and not self.serverself.usexternalauth:
            return paramiko.AUTH_SUCCESSFUL
        else:
            if self.serverself._handle_event("auth", data):
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED

    def check_auth_none(self, username):
        data = {
            "username": username,
            "auth_type": "none",
            "addr": self.addr
        }

        if self.serverself.accounts.validate_credentials(username) and not self.serverself.usexternalauth:
            return paramiko.AUTH_SUCCESSFUL
        else:
            if self.serverself._handle_event("auth", data):
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        data = {
            "username": username,
            "public_key": key,
            "auth_type": "key",
            "addr": self.addr
        }

        if self.serverself.accounts.validate_credentials(username, public_key=key) and not self.serverself.usexternalauth:
            return paramiko.AUTH_SUCCESSFUL
        else:
            if self.serverself._handle_event("auth", data):
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED

    def get_banner(self):
        if self.serverself.enaloginbanner:
            try:
                banner, lang = self.serverself._handle_event("authbanner", None)
                return banner, lang
            except:
                return "", ""
        else:
            return "", ""

    def check_channel_exec_request(self, channel, execommand):
        if b"##Moba##" in execommand and self.serverself.enaremostatus:
            startremotestatus(self.serverself, channel)

        client = self.serverself.client_handlers[self.addr]

        if self.serverself.enasysexec:
            precommand, env, user = parse_exec_request(execommand)

            if env != None:
                client.env_variables = env

            if user != None:
                self.serverself._handle_event("exec", client, user)

            if precommand != None:
                client.isexeccommandrunning = True
                try:
                    if self.serverself.enasyscom:
                        sct = systemcommand(client, precommand, self.serverself)
                    else:
                        sct = False

                    if not sct:
                        if self.serverself.XHandler != None:
                            self.serverself._handle_event("beforexhandler", client, precommand)

                            self.serverself.XHandler.call(client, precommand)

                            self.serverself._handle_event("afterxhandler", client, precommand)
                        else:
                            self.serverself._handle_event("command", client, precommand)
                except Exception as e:
                    self.serverself._handle_event("error", client, e)

            client.isexeccommandrunning = False
        else:
            kwargs = parse_exec_request_kwargs(execommand)

            self.serverself._handle_event("exec", client, **kwargs)

        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        data = {
            "term": str(term),
            "width": width,
            "height": height,
            "pixelwidth": pixelwidth,
            "pixelheight": pixelheight,
            "modes": str(modes)
        }
        data2 = {
            "width": width,
            "height": height,
            "pixelwidth": pixelwidth,
            "pixelheight": pixelheight,
        }
        try:
            time.sleep(0.01) # fix waiting windowsize
            self.serverself.client_handlers[self.addr]["windowsize"] = data2
            self.serverself.client_handlers[self.addr]["terminal_type"] = term
            self.serverself._handle_event("connectpty", self.serverself.client_handlers[self.addr], data)
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
            self.serverself.client_handlers[self.addr]["x11"] = data
            self.serverself._handle_event("connectx11", self.serverself.client_handlers[self.addr], data)
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
        self.serverself.client_handlers[self.addr]["windowsize"] = data
        self.serverself._handle_event("resized", self.serverself.client_handlers[self.addr], data)

    def check_channel_forward_agent_request(self, channel):
        print(channel)
        return True

    def check_port_forward_request(self, address, port):
        print(address, port)
        return True

    def cancel_port_forward_request(self, address, port):
        print(address, port)
        return True

    def check_channel_direct_tcpip_request(self, chanid, origin, destination):
        print(chanid)
        print(f"Port forward request: {origin} -> {destination}")
        return True

    def check_channel_env_request(self, channel, name, value):
        client = self.serverself.client_handlers[self.addr]
        client.env_variables[name] = value

    def check_auth_interactive(self, username, submethods):
        self.IAM = InteractiveAuthManager("Interactive Auth", "Please enter prompt")

        threading.Thread(target=self.serverself._handle_event, args=("auth_interactive", username, self.IAM), daemon=True).start()

        self.IAM.wait_for_system()

        return self.IAM.generateIQ()

    def check_auth_interactive_response(self, responses):
        assert self.IAM is not None, "InteractiveAuthManager should initialized before."

        self.IAM.set_response(responses)

        self.IAM.wait_for_result()

        return self.IAM.result


    def check_global_request(self, kind, msg):
        print(f"Global request received: {kind}")