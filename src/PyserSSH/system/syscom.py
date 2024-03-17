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

from ..interactive import *
from .info import version

try:
    from damp11113.info import pyofetch
    from damp11113.utils import TextFormatter
    damp11113lib = True
except:
    damp11113lib = False

def systemcommand(client, command):
    channel = client["channel"]

    if command == "info":
        if damp11113lib:
            Send(channel, "Please wait...", ln=False)
            pyf = pyofetch().info(f"{TextFormatter.format_text('PyserSSH Version', color='yellow')}: {TextFormatter.format_text(version, color='cyan')}")
            Send(channel, "              \r", ln=False)
            for i in pyf:
                Send(channel, i)
        else:
            Send(channel, "damp11113-library not available for use this command")
    elif command == "whoami":
        Send(channel, client["current_user"])
    elif command == "exit":
        channel.close()
    elif command == "clear":
        Clear(client)
    elif command == "fullscreentest":
        Clear(client)
        sx, sy = client["windowsize"]["width"], client["windowsize"]["height"]

        for x in range(sx):
            for y in range(sy):
                Send(channel, 'H', ln=False)  # Send newline after each line
    else:
        return False