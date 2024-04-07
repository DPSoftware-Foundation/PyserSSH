"""
PyserSSH - A Scriptable SSH server. For more info visit https://github.com/damp11113/PyserSSH
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
import logging

from .interactive import *
from .server import Server
from .account import AccountManager
from .system.info import system_banner


try:
    os.environ["pyserssh_systemmessage"]
except:
    os.environ["pyserssh_systemmessage"] = "YES"

try:
    os.environ["pyserssh_enable_damp11113"]
except:
    os.environ["pyserssh_enable_damp11113"] = "YES"

try:
    os.environ["pyserssh_log"]
except:
    os.environ["pyserssh_log"] = "NO"

if os.environ["pyserssh_log"] == "NO":
    logger = logging.getLogger("PyserSSH")
    logger.disabled = True

if os.environ["pyserssh_systemmessage"] == "YES":
    print(system_banner)
