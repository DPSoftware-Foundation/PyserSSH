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
import socket
import time
import logging

from .sysfunc import replace_enter_with_crlf
from .syscom import systemcommand

logger = logging.getLogger("PyserSSH.InputSystem")

def expect(self, client, echo=True):
    buffer = bytearray()
    cursor_position = 0
    history_index_position = -1  # Start at -1 (no history selected)
    chan = client["channel"]

    def clear_input_area():
        """Clear only the input area, preserving the prompt"""
        # Move cursor back to start of input, then clear to end of line
        if cursor_position > 0:
            chan.sendall(f'\x1b[{cursor_position}D'.encode())  # Move cursor to start of input
        chan.sendall(b'\x1b[K')  # Clear from cursor to end of line

    def redraw_line():
        """Redraw only the input buffer, not the prompt"""
        if echo:
            # Clear the current input area
            clear_input_area()
            # Write the buffer content
            if buffer:
                chan.sendall(buffer)
                # Move cursor to correct position
                chars_after_cursor = len(buffer) - cursor_position
                if chars_after_cursor > 0:
                    chan.sendall(f'\x1b[{chars_after_cursor}D'.encode())

    def redraw_from_cursor():
        """Redraw from cursor position to end of line"""
        if echo:
            remaining_text = buffer[cursor_position:]
            # Clear from cursor to end of line
            chan.sendall(b'\x1b[K')
            # Write remaining text
            chan.sendall(remaining_text)
            # Move cursor back to correct position
            if remaining_text:
                chan.sendall(f'\x1b[{len(remaining_text)}D'.encode())

    try:
        while True:
            try:
                byte = chan.recv(1)
            except socket.timeout:
                chan.setblocking(False)
                chan.settimeout(None)
                chan.close()
                raise EOFError()

            self._handle_event("rawtype", self.client_handlers[chan.getpeername()], byte)
            self.client_handlers[chan.getpeername()]["last_activity_time"] = time.time()

            if not byte or byte == b'\x04':
                raise EOFError()
            elif byte == b'\x03':
                pass
            elif byte == b'\t':
                pass
            elif byte == b'\x7f' or byte == b'\x08':  # Backspace
                if cursor_position > 0:
                    # Remove character from buffer
                    buffer = buffer[:cursor_position - 1] + buffer[cursor_position:]
                    cursor_position -= 1

                    if echo:
                        # Move cursor back one position
                        chan.sendall(b'\b')
                        # Redraw from current position
                        redraw_from_cursor()
                else:
                    # Bell sound for invalid backspace
                    chan.sendall(b"\x07")
            elif byte == b"\x1b":  # Escape sequence
                # Handle arrow keys with timeout to avoid blocking
                chan.settimeout(0.1)
                try:
                    next_byte = chan.recv(1)
                    if next_byte == b'[':
                        arrow_key = chan.recv(1)

                        # Handle left/right arrow keys for cursor movement
                        if arrow_key == b'C':  # Right arrow
                            if cursor_position < len(buffer):
                                chan.sendall(b'\x1b[C')
                                cursor_position += 1
                        elif arrow_key == b'D':  # Left arrow
                            if cursor_position > 0:
                                chan.sendall(b'\x1b[D')
                                cursor_position -= 1

                        # Handle up/down arrow keys for history
                        if self.history:
                            if arrow_key == b'A':  # Up arrow
                                history_index_position += 1
                                try:
                                    if history_index_position == 0:
                                        command = self.accounts.get_lastcommand(client["current_user"])
                                    else:
                                        command = self.accounts.get_history(client["current_user"],
                                                                            history_index_position)

                                    # Clear current input and update buffer with history command
                                    clear_input_area()
                                    buffer = bytearray(command.encode('utf-8'))
                                    cursor_position = len(buffer)
                                    if echo and buffer:
                                        chan.sendall(buffer)
                                except:
                                    # If no more history, stay at current position
                                    history_index_position -= 1

                            elif arrow_key == b'B':  # Down arrow
                                if history_index_position > -1:
                                    history_index_position -= 1

                                    if history_index_position == -1:
                                        # Clear buffer (no history selected)
                                        clear_input_area()
                                        buffer.clear()
                                        cursor_position = 0
                                    else:
                                        try:
                                            if history_index_position == 0:
                                                command = self.accounts.get_lastcommand(client["current_user"])
                                            else:
                                                command = self.accounts.get_history(client["current_user"],
                                                                                    history_index_position)

                                            clear_input_area()
                                            buffer = bytearray(command.encode('utf-8'))
                                            cursor_position = len(buffer)
                                            if echo and buffer:
                                                chan.sendall(buffer)
                                        except:
                                            # If history access fails, clear buffer
                                            clear_input_area()
                                            buffer.clear()
                                            cursor_position = 0
                                            history_index_position = -1
                    else:
                        # Not an arrow key sequence, treat as regular input
                        buffer = buffer[:cursor_position] + b'\x1b' + next_byte + buffer[cursor_position:]
                        cursor_position += 2
                        if echo:
                            chan.sendall(b'\x1b' + next_byte)
                            redraw_from_cursor()
                except socket.timeout:
                    # Just escape key, treat as regular character
                    buffer = buffer[:cursor_position] + byte + buffer[cursor_position:]
                    cursor_position += 1
                    if echo:
                        chan.sendall(byte)
                        redraw_from_cursor()
                finally:
                    chan.settimeout(None)

            elif byte in (b'\r', b'\n'):
                break
            else:
                # Regular character input
                history_index_position = -1  # Reset history position

                self._handle_event("type", self.client_handlers[chan.getpeername()], byte)

                # Insert character at cursor position
                buffer = buffer[:cursor_position] + byte + buffer[cursor_position:]
                cursor_position += 1

                if echo:
                    chan.sendall(byte)
                    # If we're not at the end, redraw the rest of the line
                    if cursor_position < len(buffer):
                        redraw_from_cursor()

            client["inputbuffer"] = buffer

        if echo:
            chan.sendall(b'\r\n')

        command = str(buffer.decode('utf-8')).strip()

        if self.history and command.strip() != "" and self.accounts.get_lastcommand(client["current_user"]) != command:
            self.accounts.add_history(client["current_user"], command)
            client["last_command"] = command

        if command.strip() != "":
            if self.accounts.get_user_timeout(self.client_handlers[chan.getpeername()]["current_user"]) != None:
                chan.setblocking(False)
                chan.settimeout(None)

            try:
                if self.enasyscom:
                    sct = systemcommand(client, command, self)
                else:
                    sct = False

                if not sct:
                    if self.XHandler != None:
                        self._handle_event("beforexhandler", client, command)

                        self.XHandler.call(client, command)

                        self._handle_event("afterxhandler", client, command)
                    else:
                        self._handle_event("command", client, command)

            except Exception as e:
                self._handle_event("error", client, e)
        if echo:
            try:
                chan.send(replace_enter_with_crlf(client["prompt"] + " "))
            except:
                logger.error("Send error")

        chan.setblocking(False)
        chan.settimeout(None)

        if self.accounts.get_user_timeout(self.client_handlers[chan.getpeername()]["current_user"]) != None:
            chan.setblocking(False)
            chan.settimeout(self.accounts.get_user_timeout(self.client_handlers[chan.getpeername()]["current_user"]))
    except socket.error:
        pass
    except Exception as e:
        logger.error(str(e))
    finally:
        try:
            if not byte:
                return False
            return True
        except:
            return False