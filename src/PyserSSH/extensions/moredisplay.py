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

def clickable_url(url, link_text=""):
    """
    Creates a clickable URL in a terminal client with optional link text.

    Args:
        url (str): The URL to be linked.
        link_text (str, optional): The text to be displayed for the link. Defaults to an empty string, which will display the URL itself.

    Returns:
        str: A terminal escape sequence that makes the URL clickable with the provided link text.
    """
    return f"\033]8;;{url}\033\\{link_text}\033]8;;\033\\"

def Send_karaoke_effect(client, text, delay=0.1, ln=True):
    """
    Sends a text with a 'karaoke' effect where the text is printed one character at a time,
    with the remaining text dimmed until it is printed.

    Args:
        client (Client): The client to send the text to.
        text (str): The text to be printed with the karaoke effect.
        delay (float, optional): The delay in seconds between printing each character. Defaults to 0.1.
        ln (bool, optional): Whether to send a newline after the text is finished. Defaults to True.

    This function simulates a typing effect by printing the text character by character,
    while dimming the unprinted characters.
    """
    printed_text = ""
    for i, char in enumerate(text):
        # Print the already printed text normally
        Send(client, printed_text + char, ln=False)

        # Calculate the unprinted text and dim it
        not_printed_text = text[i + 1:]
        dimmed_text = ''.join([f"\033[2m{char}\033[0m" for char in not_printed_text])

        # Print the dimmed text for the remaining characters
        Send(client, dimmed_text, ln=False)

        # Wait before printing the next character
        time.sleep(delay)

        # Clear the line to update the text in the next iteration
        Send(client, '\r', ln=False)

        # Update the printed_text to include the current character
        printed_text += char

    if ln:
        Send(client, "")  # Send a newline after the entire text is printed
