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
import re
import socket

from .system.sysfunc import replace_enter_with_crlf

def Send(client, string, ln=True, directchannel=False):
    if directchannel:
        channel = client
    else:
        channel = client["channel"]

    if ln:
        channel.send(replace_enter_with_crlf(str(string) + "\n"))
    else:
        channel.send(replace_enter_with_crlf(str(string)))

def NewSend(client, *astring, ln=True, end=b'\n', sep=b' ', directchannel=False):
    if directchannel:
        channel = client
    else:
        channel = client["channel"]

    if ln:
        if not b'\n' in end:
            end += b'\n'
    else:
        # Ensure that `end` does not contain `b'\n'` if `ln` is False
        end = end.replace(b'\n', b'')

    # Prepare the strings to be sent
    if astring:
        for i, s in enumerate(astring):
            # Convert `s` to bytes if it's a string
            if isinstance(s, str):
                s = s.encode('utf-8')
            # Use a hypothetical `replace_enter_with_crlf` function if needed
            channel.send(replace_enter_with_crlf(s))
            if i != len(astring) - 1:
                channel.send(sep)
        channel.send(end)

def Clear(client, oldclear=False, keep=False):
    sx, sy = client["windowsize"]["width"], client["windowsize"]["height"]

    if oldclear:
        for x in range(sy):
            Send(client, '\b \b' * sx, ln=False)  # Send newline after each line
    elif keep:
        Send(client, "\033[2J", ln=False)
        Send(client, "\033[H", ln=False)
    else:
        Send(client, "\033[3J", ln=False)
        Send(client, "\033[1J", ln=False)
        Send(client, "\033[H", ln=False)

def Title(client, title):
    Send(client, f"\033]0;{title}\007", ln=False)

def wait_input(client, prompt="", defaultvalue=None, cursor_scroll=False, echo=True, password=False, passwordmask=b"*", noabort=False, timeout=0):
    channel = client["channel"]

    channel.send(replace_enter_with_crlf(prompt))

    buffer = bytearray()
    cursor_position = 0

    if timeout != 0:
        channel.settimeout(timeout)

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

    except socket.timeout:
        channel.setblocking(False)
        channel.settimeout(None)
        channel.sendall(b'\r\n')
        output = ""
    except Exception:
        channel.setblocking(False)
        channel.settimeout(None)
        channel.sendall(b'\r\n')
        raise
    else:
        output = buffer.decode('utf-8')

    # Return default value if specified and no input given
    if defaultvalue is not None and not output.strip():
        return defaultvalue
    else:
        return output

def wait_inputkey(client, prompt="", raw=True, timeout=0):
    channel = client["channel"]

    if prompt != "":
        channel.send(replace_enter_with_crlf(prompt))

    if timeout != 0:
        channel.settimeout(timeout)

    try:
        byte = channel.recv(10)

        if not byte or byte == b'\x04':
            raise EOFError()

        if not raw:
            if bool(re.compile(b'\x1b\[[0-9;]*[mGK]').search(byte)):
                pass

            return byte.decode('utf-8') # only regular character

        else:
            return byte

    except socket.timeout:
        channel.setblocking(False)
        channel.settimeout(None)
        if prompt != "":
            channel.send("\r\n")
        return None
    except Exception:
        channel.setblocking(False)
        channel.settimeout(None)
        channel.send("\r\n")
        raise

def wait_inputmouse(client, timeout=0):
    channel = client["channel"]
    Send(client, "\033[?1000h", ln=False)

    if timeout != 0:
        channel.settimeout(timeout)

    try:
        byte = channel.recv(10)

        if not byte or byte == b'\x04':
            raise EOFError()

        if byte.startswith(b'\x1b[M'):
            # Parse mouse event
            if len(byte) < 6 or not byte.startswith(b'\x1b[M'):
                Send(client, "\033[?1000l", ln=False)
                return None, None, None

                # Extract button, x, y from the sequence
            button = byte[3] - 32
            x = byte[4] - 32
            y = byte[5] - 32

            Send(client, "\033[?1000l", ln=False)
            return button, x, y
        else:
            Send(client, "\033[?1000l", ln=False)
            return byte, None, None

    except socket.timeout:
        channel.setblocking(False)
        channel.settimeout(None)
        channel.send("\r\n")
        Send(client, "\033[?1000l", ln=False)
        return None, None, None
    except Exception:
        channel.setblocking(False)
        channel.settimeout(None)
        channel.send("\r\n")
        raise

def wait_choose(client, choose, prompt="", timeout=0):
    channel = client["channel"]

    chooseindex = 0
    chooselen = len(choose) - 1

    if timeout != 0:
        channel.settimeout(timeout)

    while True:
        try:
            tempchooselist = choose.copy()

            tempchooselist[chooseindex] = "[" + tempchooselist[chooseindex] + "]"

            exported = " ".join(tempchooselist)

            if prompt.strip() == "":
                Send(client, f'\r{exported}', ln=False)
            else:
                Send(client, f'\r{prompt}{exported}', ln=False)

            keyinput = wait_inputkey(client, raw=True)

            if keyinput == b'\r':  # Enter key
                Send(client, "\033[K")
                return chooseindex
            elif keyinput == b'\x03':  # ' ctrl+c' key for cancel
                Send(client, "\033[K")
                return 0
            elif keyinput == b'\x1b[D':  # Up arrow key
                chooseindex -= 1
                if chooseindex < 0:
                    chooseindex = 0
            elif keyinput == b'\x1b[C':  # Down arrow key
                chooseindex += 1
                if chooseindex > chooselen:
                    chooseindex = chooselen
        except socket.timeout:
            channel.setblocking(False)
            channel.settimeout(None)
            channel.send("\r\n")
            return chooseindex
        except Exception:
            channel.setblocking(False)
            channel.settimeout(None)
            channel.send("\r\n")
            raise