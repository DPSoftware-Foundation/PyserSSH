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

import re

from ..interactive import Clear, Send, wait_inputkey
from ..system.sysfunc import text_centered_screen

class TextDialog:
    def __init__(self, client, title="", content=""):
        self.client = client

        self.windowsize = client["windowsize"]
        self.title = title
        self.content = content

    def render(self):
        Clear(self.client)
        Send(self.client, self.title)
        Send(self.client, "-" * self.windowsize["width"])

        generatedwindow = text_centered_screen(self.content, self.windowsize["width"], self.windowsize["height"]-3, " ")

        Send(self.client, generatedwindow)

        Send(self.client, "Press 'enter' to continue", ln=False)

        self.waituserenter()

    def waituserenter(self):
        while True:
            if wait_inputkey(self.client, raw=True) == b'\r':
                Clear(self.client)
                break
            pass

class MenuDialog:
    def __init__(self, client, choose: list, title="", desc=""):
        self.client = client

        self.title = title
        self.choose = choose
        self.desc = desc
        self.contentallindex = len(choose) - 1
        self.selectedindex = 0
        self.selectstatus = 0 # 0 none 1 selected 2 cancel

    def render(self):
        tempcontentlist = self.choose.copy()

        Clear(self.client)
        Send(self.client, self.title)
        Send(self.client, "-" * self.client["windowsize"]["width"])

        tempcontentlist[self.selectedindex] = "> " + tempcontentlist[self.selectedindex]

        exported = "\n".join(tempcontentlist)

        if not self.desc.strip() == "":
            contenttoshow = (
                f"{self.desc}\n\n"
                f"{exported}"
            )
        else:
            contenttoshow = (
                f"{exported}"
            )

        generatedwindow = text_centered_screen(contenttoshow, self.client["windowsize"]["width"], self.client["windowsize"]["height"]-3, " ")

        Send(self.client, generatedwindow)

        Send(self.client, "Use arrow up/down key to choose and press 'enter' to select or 'c' to cancel", ln=False)

        self._waituserinput()

    def _waituserinput(self):
        keyinput = wait_inputkey(self.client, raw=True)

        if keyinput == b'\r':  # Enter key
            Clear(self.client)
            self.selectstatus = 1
        elif keyinput == b'c':  # 'c' key for cancel
            Clear(self.client)
            self.selectstatus = 2
        elif keyinput == b'\x1b[A':  # Up arrow key
            self.selectedindex -= 1
            if self.selectedindex < 0:
                self.selectedindex = 0
        elif keyinput == b'\x1b[B':  # Down arrow key
            self.selectedindex += 1
            if self.selectedindex > self.contentallindex:
                self.selectedindex = self.contentallindex

        if self.selectstatus == 2:
            self.output()
        elif self.selectstatus == 1:
            self.output()
        else:
            self.render()

    def output(self):
        if self.selectstatus == 2:
            return None
        elif self.selectstatus == 1:
            return self.selectedindex

class TextInputDialog:
    def __init__(self, client, title="", inputtitle="Input Here", password=False):
        self.client = client

        self.title = title
        self.inputtitle = inputtitle
        self.ispassword = password

        self.inputstatus = 0 # 0 none 1 selected 2 cancel
        self.buffer = bytearray()
        self.cursor_position = 0

    def render(self):
        Clear(self.client)
        Send(self.client, self.title)
        Send(self.client, "-" * self.client["windowsize"]["width"])

        if self.ispassword:
            texts = (
                f"{self.inputtitle}\n\n"
                "> " + ("*" * len(self.buffer.decode('utf-8')))
            )
        else:
            texts = (
                f"{self.inputtitle}\n\n"
                "> " + self.buffer.decode('utf-8')
            )

        generatedwindow = text_centered_screen(texts, self.client["windowsize"]["width"], self.client["windowsize"]["height"]-3, " ")

        Send(self.client, generatedwindow)

        Send(self.client, "Press 'enter' to select or 'ctrl+c' to cancel", ln=False)

        self._waituserinput()

    def _waituserinput(self):
        keyinput = wait_inputkey(self.client, raw=True)

        if keyinput == b'\r':  # Enter key
            Clear(self.client)
            self.inputstatus = 1
        elif keyinput == b'\x03':  # 'ctrl + c' key for cancel
            Clear(self.client)
            self.inputstatus = 2

        try:
            if keyinput == b'\x7f' or keyinput == b'\x08':  # Backspace
                if self.cursor_position > 0:
                    # Move cursor back, erase character, move cursor back again
                    self.buffer = self.buffer[:self.cursor_position - 1] + self.buffer[self.cursor_position:]
                    self.cursor_position -= 1
            elif bool(re.compile(b'\x1b\[[0-9;]*[mGK]').search(keyinput)):
                pass
            else:  # Regular character
                self.buffer = self.buffer[:self.cursor_position] + keyinput + self.buffer[self.cursor_position:]
                self.cursor_position += 1
        except Exception:
            raise

        if self.inputstatus == 2:
            self.output()
        elif self.inputstatus == 1:
            self.output()
        else:
            self.render()

    def output(self):
        if self.inputstatus == 2:
            return None
        elif self.inputstatus == 1:
            return self.buffer.decode('utf-8')
