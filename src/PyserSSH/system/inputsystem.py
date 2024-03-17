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

import time
import logging

from .sysfunc import replace_enter_with_crlf
from .syscom import systemcommand

logger = logging.getLogger("PyserSSH")
logger.disabled = True

def expect(self, chan, peername, echo=True):
    buffer = bytearray()
    cursor_position = 0
    history_index_position = 0  # Initialize history index position outside the loop
    currentuser = self.client_handlers[chan.getpeername()]
    try:
        while True:
            byte = chan.recv(1)
            self._handle_event("onrawtype", chan, byte, self.client_handlers[chan.getpeername()])

            if self.timeout != 0:
                self.client_handlers[chan.getpeername()]["last_activity_time"] = time.time()

            if not byte or byte == b'\x04':
                raise EOFError()
            elif byte == b'\x03':
                pass
            elif byte == b'\t':
                pass
            elif byte == b'\x7f' or byte == b'\x08':
                if cursor_position > 0:
                    buffer = buffer[:cursor_position - 1] + buffer[cursor_position:]
                    cursor_position -= 1
                    chan.sendall(b"\b \b")
            elif byte == b"\x1b" and chan.recv(1) == b'[':
                arrow_key = chan.recv(1)
                if not self.disable_scroll_with_arrow:
                    if arrow_key == b'C':
                        # Right arrow key, move cursor right if not at the end
                        if cursor_position < len(buffer):
                            chan.sendall(b'\x1b[C')
                            cursor_position += 1
                    elif arrow_key == b'D':
                        # Left arrow key, move cursor left if not at the beginning
                        if cursor_position > 0:
                            chan.sendall(b'\x1b[D')
                            cursor_position -= 1
                elif self.history:
                    if arrow_key == b'A':
                        if history_index_position == 0:
                            command = self.accounts.get_lastcommand(currentuser["current_user"])
                        else:
                            command = self.accounts.get_history(currentuser["current_user"], history_index_position)

                        # Clear the buffer
                        for i in range(cursor_position):
                            chan.send(b"\b \b")

                        # Update buffer and cursor position with the new command
                        buffer = bytearray(command.encode('utf-8'))
                        cursor_position = len(buffer)

                        # Print the updated buffer
                        chan.sendall(buffer)

                        history_index_position += 1

                    if arrow_key == b'B':
                        if history_index_position != -1:
                            if history_index_position == 0:
                                command = self.accounts.get_lastcommand(currentuser["current_user"])
                            else:
                                command = self.accounts.get_history(currentuser["current_user"], history_index_position)

                            # Clear the buffer
                            for i in range(cursor_position):
                                chan.send(b"\b \b")

                            # Update buffer and cursor position with the new command
                            buffer = bytearray(command.encode('utf-8'))
                            cursor_position = len(buffer)

                            # Print the updated buffer
                            chan.sendall(buffer)
                        else:
                            history_index_position = 0
                            for i in range(cursor_position):
                                chan.send(b"\b \b")

                            buffer.clear()
                            cursor_position = 0

                        history_index_position -= 1

            elif byte in (b'\r', b'\n'):
                break
            else:
                history_index_position = -1
                buffer = buffer[:cursor_position] + byte + buffer[cursor_position:]
                cursor_position += 1
                self._handle_event("ontype", chan, byte, self.client_handlers[chan.getpeername()])
                if echo:
                    chan.sendall(byte)

        if echo:
            chan.sendall(b'\r\n')

        command = str(buffer.decode('utf-8'))

        try:
            if self.enasyscom:
                systemcommand(currentuser, command)

            self._handle_event("command", chan, command, currentuser)
        except Exception as e:
            self._handle_event("error", chan, e, currentuser)

        if self.history and command.strip() != "" and self.accounts.get_lastcommand(currentuser["current_user"]) != command:
            self.accounts.add_history(currentuser["current_user"], command)

        try:
            chan.send(replace_enter_with_crlf(self.accounts.get_prompt(currentuser["current_user"]) + " ").encode('utf-8'))
        except:
            logger.error("Send error")

    except Exception as e:
        logger.error(str(e))
    finally:
        if not byte:
            logger.info(f"{peername} is disconnected")
            self._handle_event("disconnected", peername, self.client_handlers[peername]["current_user"])