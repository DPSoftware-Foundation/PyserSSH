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

from .system.sysfunc import replace_enter_with_crlf

def Send(channel, string, ln=True):
    if ln:
        channel.send(replace_enter_with_crlf(string + "\n"))
    else:
        channel.send(replace_enter_with_crlf(string))

def Print(channel, string, start="", end="\n"):
    channel.send(replace_enter_with_crlf(start + string + end))

def Clear(client):
    channel = client["channel"]
    sx, sy = client["windowsize"]["width"], client["windowsize"]["height"]

    for x in range(sx):
        for y in range(sy):
            Send(channel, '\b \b', ln=False)  # Send newline after each line

def wait_input(channel, prompt="", defaultvalue=None, cursor_scroll=False, echo=True, password=False, passwordmask=b"*", noabort=False):
    channel.send(replace_enter_with_crlf(prompt))

    buffer = bytearray()
    cursor_position = 0

    try:
        while True:
            byte = channel.recv(1)

            if not byte or byte == b'\x04':
                raise EOFError()
            elif byte == b'\x03' and not noabort:
                break
            elif byte == b'\t':
                pass
            elif byte == b'\x7f' or byte == b'\x08':  # Backspace
                if cursor_position > 0:
                    # Move cursor back, erase character, move cursor back again
                    channel.sendall(b'\b \b')
                    buffer = buffer[:cursor_position - 1] + buffer[cursor_position:]
                    cursor_position -= 1
            elif byte == b'\x1b' and channel.recv(1) == b'[':  # Arrow keys
                arrow_key = channel.recv(1)
                if cursor_scroll:
                    if arrow_key == b'C':  # Right arrow key
                        if cursor_position < len(buffer):
                            channel.sendall(b'\x1b[C')
                            cursor_position += 1
                    elif arrow_key == b'D':  # Left arrow key
                        if cursor_position > 0:
                            channel.sendall(b'\x1b[D')
                            cursor_position -= 1
            elif byte in (b'\r', b'\n'):  # Enter key
                break
            else:  # Regular character
                buffer = buffer[:cursor_position] + byte + buffer[cursor_position:]
                cursor_position += 1
                if echo or password:
                    if password:
                        channel.sendall(passwordmask)
                    else:
                        channel.sendall(byte)

        channel.sendall(b'\r\n')

    except Exception:
        raise

    output = buffer.decode('utf-8')

    # Return default value if specified and no input given
    if defaultvalue is not None and not output.strip():
        return defaultvalue
    else:
        return output

def wait_inputkey(channel, prompt="", raw=False):
    if prompt != "":
        channel.send(replace_enter_with_crlf(prompt))

    try:
        byte = channel.recv(10)

        if not raw:
            if not byte or byte == b'\x04':
                raise EOFError()

            elif byte == b'\t':
                pass

            return byte.decode('utf-8')

        else:
            return byte

    except Exception:
        raise