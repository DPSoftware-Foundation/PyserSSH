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

from ..interactive import Send

def clickable_url(url, link_text=""):
    return f"\033]8;;{url}\033\\{link_text}\033]8;;\033\\"

def Send_karaoke_effect(client, text, delay=0.1, ln=True):
    printed_text = ""
    for i, char in enumerate(text):
        # Print already printed text normally
        Send(client, printed_text + char, ln=False)

        # Calculate not yet printed text to dim
        not_printed_text = text[i + 1:]
        dimmed_text = ''.join([f"\033[2m{char}\033[0m" for char in not_printed_text])

        # Print dimmed text
        Send(client, dimmed_text, ln=False)

        # Wait before printing the next character
        time.sleep(delay)

        # Clear the line for the next iteration
        Send(client, '\r' ,ln=False)

        # Prepare the updated printed_text for the next iteration
        printed_text += char

    if ln:
        Send(client, "") # new line

