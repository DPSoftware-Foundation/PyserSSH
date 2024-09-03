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

"""
note

ansi cursor arrow
up - \x1b[A
down - \x1b[B
left - \x1b[D
right - \x1b[C

https://en.wikipedia.org/wiki/ANSI_escape_code
"""
import os
import ctypes
import logging

from .interactive import *
from .server import Server
from .account import AccountManager
from .system.info import system_banner

if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

try:
    os.environ["pyserssh_systemmessage"]
except:
    os.environ["pyserssh_systemmessage"] = "YES"

try:
    os.environ["pyserssh_log"]
except:
    os.environ["pyserssh_log"] = "NO"

if os.environ["pyserssh_log"] == "NO":
    logging.basicConfig(level=logging.CRITICAL)
    logger = logging.getLogger("PyserSSH")
    #logger.disabled = False

if os.environ["pyserssh_systemmessage"] == "YES":
    print(system_banner)

# Server Managers

class ServerManager:
    def __init__(self):
        self.servers = {}

    def add_server(self, name, server):
        if name in self.servers:
            raise ValueError(f"Server with name '{name}' already exists.")
        self.servers[name] = server

    def remove_server(self, name):
        if name not in self.servers:
            raise ValueError(f"No server found with name '{name}'.")
        del self.servers[name]

    def get_server(self, name):
        return self.servers.get(name)

    def start_server(self, name, protocol="ssh", *args, **kwargs):
        server = self.get_server(name)
        if not server:
            raise ValueError(f"No server found with name '{name}'.")
        print(f"Starting server '{name}'...")
        server.run(*args, **kwargs)

    def stop_server(self, name):
        server = self.get_server(name)
        if not server:
            raise ValueError(f"No server found with name '{name}'.")
        print(f"Stopping server '{name}'...")
        server.stop_server()

    def start_all_servers(self, *args, **kwargs):
        for name, server in self.servers.items():
            print(f"Starting server '{name}'...")
            server.run(*args, **kwargs)

    def stop_all_servers(self):
        for name, server in self.servers.items():
            print(f"Stopping server '{name}'...")
            server.stop_server()