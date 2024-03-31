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
import socket
import time
import logging
import shlex
import traceback

from .sysfunc import replace_enter_with_crlf
from .syscom import systemcommand

logger = logging.getLogger("PyserSSH")

def expect(self, chan, peername, echo=True):
    buffer = bytearray()
    cursor_position = 0
    outindexall = 0
    history_index_position = 0  # Initialize history index position outside the loop
    currentuser = self.client_handlers[chan.getpeername()]
    try:
        while True:
            byte = chan.recv(1)
            self._handle_event("onrawtype", self.client_handlers[chan.getpeername()], byte)

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
                    outindexall -= 1
                    chan.sendall(b"\b \b")
                else:
                    chan.sendall(b"\x07")
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
                        outindexall = cursor_position

                        # Print the updated buffer
                        chan.sendall(buffer)

                        history_index_position += 1
                    elif arrow_key == b'B':
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
                            outindexall = cursor_position

                            # Print the updated buffer
                            chan.sendall(buffer)
                        else:
                            history_index_position = 0
                            for i in range(cursor_position):
                                chan.send(b"\b \b")

                            buffer.clear()
                            cursor_position = 0
                            outindexall = 0

                        history_index_position -= 1

            elif byte in (b'\r', b'\n'):
                break
            else:
                history_index_position = -1

                self._handle_event("ontype", self.client_handlers[chan.getpeername()], byte)
                if echo:
                    if outindexall != cursor_position:
                        chan.sendall(byte + buffer[cursor_position:])
                        chan.sendall(f"\033[{cursor_position}G".encode())
                    else:
                        chan.sendall(byte)

                #print(buffer[:cursor_position], byte, buffer[cursor_position:])
                buffer = buffer[:cursor_position] + byte + buffer[cursor_position:]
                cursor_position += 1
                outindexall += 1

        if echo:
            chan.sendall(b'\r\n')

        command = str(buffer.decode('utf-8')).strip()

        if self.history and command.strip() != "" and self.accounts.get_lastcommand(currentuser["current_user"]) != command:
            self.accounts.add_history(currentuser["current_user"], command)

        if command.strip() != "":
            if self.accounts.get_user_timeout(self.client_handlers[chan.getpeername()]["current_user"]) != 0:
                chan.settimeout(0)
                chan.setblocking(False)

            try:
                if self.enasyscom:
                    sct = systemcommand(currentuser, command)
                else:
                    sct = False

                if not sct:
                    if self.XHandler != None:
                        self._handle_event("beforexhandler", currentuser, command)

                        self.XHandler.call(currentuser, command)

                        self._handle_event("afterxhandler", currentuser, command)
                    else:
                        self._handle_event("command", currentuser, command)

            except Exception as e:
                self._handle_event("error", currentuser, e)

        try:
            chan.send(replace_enter_with_crlf(self.accounts.get_prompt(currentuser["current_user"]) + " ").encode('utf-8'))
        except:
            logger.error("Send error")

        if self.accounts.get_user_timeout(self.client_handlers[chan.getpeername()]["current_user"]) != 0:
            chan.settimeout(self.accounts.get_user_timeout(self.client_handlers[chan.getpeername()]["current_user"]))

    except socket.timeout:
        chan.settimeout(0)
        chan.setblocking(False)
        chan.close()
    except Exception as e:
        logger.error(str(e))
    finally:
        try:
            if not byte:
                logger.info(f"{peername} is disconnected")
                self._handle_event("disconnected", self.client_handlers[peername]["current_user"])
        except:
            logger.info(f"{peername} is disconnected by timeout")
            self._handle_event("timeout", self.client_handlers[peername]["current_user"])