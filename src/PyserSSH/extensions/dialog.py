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

import re

from ..interactive import Clear, Send, wait_inputkey
from ..system.sysfunc import text_centered_screen


class TextDialog:
    """
    A dialog that displays a simple text message with an optional title.

    Args:
        client (Client): The client to display the dialog to.
        content (str, optional): The content to be displayed in the dialog. Defaults to an empty string.
        title (str, optional): The title of the dialog. Defaults to an empty string.

    Methods:
        render(): Renders the dialog, displaying the title and content in the center of the screen.
        waituserenter(): Waits for the user to press the 'enter' key to close the dialog.
    """

    def __init__(self, client, content="", title="", exit_key=b'\r'):
        """
        if `exit_key` is None, it will default to any key
        """
        self.client = client

        self.windowsize = client["windowsize"]
        self.title = title
        self.content = content
        self.exit_key = exit_key

    def render(self):
        """
        Renders the dialog by displaying the title, content, and waiting for the user's input.
        """
        Clear(self.client)
        Send(self.client, self.title)
        Send(self.client, "-" * self.windowsize["width"])

        generatedwindow = text_centered_screen(self.content, self.windowsize["width"], self.windowsize["height"] - 3,
                                               " ")

        Send(self.client, generatedwindow)

        if self.exit_key is None:
            Send(self.client, "Press any key to close this dialog", ln=False)
        else:
            Send(self.client, f"Press '{self.exit_key.decode('utf-8')}' to close this dialog", ln=False)

        self.waituserenter()

    def waituserenter(self):
        """
        Waits for the user to press the 'enter' key to close the dialog.
        """
        while True:
            keyi = wait_inputkey(self.client, raw=True)

            if self.exit_key is None:
                Clear(self.client)
                break
            else:
                if keyi == self.exit_key:
                    Clear(self.client)
                    break
            pass


class MenuDialog:
    """
    A menu dialog that allows the user to choose from a list of options, with navigation and selection using arrow keys.

    Args:
        client (Client): The client to display the menu to.
        choose (list): A list of options to be displayed.
        title (str, optional): The title of the menu.
        desc (str, optional): A description to display above the menu options.

    Methods:
        render(): Renders the menu dialog and waits for user input.
        _waituserinput(): Handles user input for selecting options or canceling.
        output(): Returns the selected option index or `None` if canceled.
    """

    def __init__(self, client, choose: list, title="", desc=""):
        self.client = client

        self.title = title
        self.choose = choose
        self.desc = desc
        self.contentallindex = len(choose) - 1
        self.selectedindex = 0
        self.selectstatus = 0  # 0 none, 1 selected, 2 canceled

    def render(self):
        """
        Renders the menu dialog, displaying the options and allowing the user to navigate and select an option.
        """
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

        generatedwindow = text_centered_screen(contenttoshow, self.client["windowsize"]["width"],
                                               self.client["windowsize"]["height"] - 3, " ")

        Send(self.client, generatedwindow)

        Send(self.client, "Use arrow up/down key to choose and press 'enter' to select or 'c' to cancel", ln=False)

        self._waituserinput()

    def _waituserinput(self):
        """
        Waits for user input and updates the selection based on key presses.
        """
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
        """
        Returns the selected option index or `None` if the action was canceled.
        """
        if self.selectstatus == 2:
            return None
        elif self.selectstatus == 1:
            return self.selectedindex


class TextInputDialog:
    """
    A text input dialog that allows the user to input text with optional password masking.

    Args:
        client (Client): The client to display the dialog to.
        title (str, optional): The title of the input dialog.
        inputtitle (str, optional): The prompt text for the user input.
        password (bool, optional): If `True`, the input will be masked as a password. Defaults to `False`.

    Methods:
        render(): Renders the input dialog, displaying the prompt and capturing user input.
        _waituserinput(): Handles user input, including text input and special keys.
        output(): Returns the input text if selected, or `None` if canceled.
    """

    def __init__(self, client, title="", inputtitle="Input Here", password=False):
        self.client = client

        self.title = title
        self.inputtitle = inputtitle
        self.ispassword = password

        self.inputstatus = 0  # 0 none, 1 selected, 2 canceled
        self.buffer = bytearray()
        self.cursor_position = 0

    def render(self):
        """
        Renders the text input dialog and waits for user input.
        """
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

        generatedwindow = text_centered_screen(texts, self.client["windowsize"]["width"],
                                               self.client["windowsize"]["height"] - 3, " ")

        Send(self.client, generatedwindow)

        Send(self.client, "Press 'enter' to select or 'ctrl+c' to cancel", ln=False)

        self._waituserinput()

    def _waituserinput(self):
        """
        Waits for the user to input text or special commands (backspace, cancel, enter).
        """
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
                pass  # Ignore ANSI escape codes
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
        """
        Returns the input text if the input was selected, or `None` if canceled.
        """
        if self.inputstatus == 2:
            return None
        elif self.inputstatus == 1:
            return self.buffer.decode('utf-8')
