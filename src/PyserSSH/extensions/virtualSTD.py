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

import sys
import io
from typing import List

from ..system.clientype import Client
from ..interactive import wait_input, wait_inputkey

class VStdin:
    """Custom stdin implementation"""

    def __init__(self, client: Client = None, input_data: str = ""):
        self._client = client
        self._buffer = io.StringIO(input_data)
        self.encoding = 'utf-8'
        self.errors = 'strict'
        self.newlines = None
        self.closed = False
        self._line_buffer = ""  # Buffer for incomplete lines

        self.auto_enter = False

    def read(self, size: int = -1) -> str:
        """Read and return at most size characters from the stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")

        # If size is 0, return empty string immediately
        if size == 0:
            return ""

        result = ""
        chars_needed = size if size > 0 else float('inf')

        # First, try to satisfy from existing buffer
        if self._buffer.tell() > 0:
            self._buffer.seek(0)
            buffered_data = self._buffer.read()
            self._buffer = io.StringIO()  # Clear buffer

            if size > 0 and len(buffered_data) >= size:
                # Buffer has enough data
                result = buffered_data[:size]
                # Put remaining back in buffer
                if len(buffered_data) > size:
                    self._buffer.write(buffered_data[size:])
                return result
            else:
                result = buffered_data
                chars_needed -= len(result)

        # Need more data from input
        try:
            while chars_needed > 0:
                if self.auto_enter and chars_needed == 1:
                    # Single character mode with auto-enter
                    char = wait_inputkey(self._client, echo=True)
                    if char:
                        result += char
                        chars_needed -= len(char)
                else:
                    # Get input line by line
                    input_data = wait_input(self._client, noabort=True)
                    if input_data is None:
                        break  # EOF or no more input

                    # Add newline if not present (stdin.read() includes newlines)
                    if not input_data.endswith('\n'):
                        input_data += '\n'

                    if size > 0 and len(result) + len(input_data) > size:
                        # Input would exceed requested size
                        take = size - len(result)
                        result += input_data[:take]
                        # Put remainder in buffer for next read
                        self._buffer.write(input_data[take:])
                        chars_needed = 0
                    else:
                        result += input_data
                        chars_needed -= len(input_data)

                        # If we got a complete line and size is unlimited,
                        # we can stop here (common stdin.read() behavior)
                        if size < 0:
                            break

        except (AttributeError, NotImplementedError, EOFError):
            # Client doesn't support input operations
            pass

        return result

    def readline(self, size: int = -1) -> str:
        """Read and return one line from the stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")

        # If size is 0, return empty string
        if size == 0:
            return ""

        result = ""

        # Check if we have a complete line in our line buffer
        if '\n' in self._line_buffer:
            newline_pos = self._line_buffer.index('\n') + 1
            line = self._line_buffer[:newline_pos]
            self._line_buffer = self._line_buffer[newline_pos:]

            if size > 0 and len(line) > size:
                # Line is longer than requested size
                result = line[:size]
                # Put the rest back at the beginning of line buffer
                self._line_buffer = line[size:] + self._line_buffer
            else:
                result = line
            return result

        # No complete line in buffer, need to read more
        try:
            while True:
                input_data = wait_input(self._client, noabort=True)
                if input_data is None:
                    # EOF - return whatever we have in line buffer
                    result = self._line_buffer
                    self._line_buffer = ""
                    break

                # Add newline if not present
                if not input_data.endswith('\n'):
                    input_data += '\n'

                self._line_buffer += input_data

                # Check if we now have a complete line
                if '\n' in self._line_buffer:
                    newline_pos = self._line_buffer.index('\n') + 1
                    line = self._line_buffer[:newline_pos]
                    self._line_buffer = self._line_buffer[newline_pos:]

                    if size > 0 and len(line) > size:
                        # Line is longer than requested size
                        result = line[:size]
                        # Put the rest back at the beginning of line buffer
                        self._line_buffer = line[size:] + self._line_buffer
                    else:
                        result = line
                    break

        except (AttributeError, NotImplementedError, EOFError):
            # Client doesn't support input operations
            # Return whatever is in the line buffer
            result = self._line_buffer
            self._line_buffer = ""

        return result

    def readlines(self, hint: int = -1) -> List[str]:
        """Read and return a list of lines from the stream"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._buffer.readlines(hint)

    def readable(self) -> bool:
        """Return whether object supports reading"""
        return not self.closed

    def seek(self, offset: int, whence: int = 0) -> int:
        """Move to new file position and return the file position"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._buffer.seek(offset, whence)

    def tell(self) -> int:
        """Return current stream position"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self._buffer.tell()

    def close(self) -> None:
        """Close the stream"""
        self.closed = True
        self._buffer.close()

    def flush(self) -> None:
        """Flush write buffers, if applicable"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self._buffer.flush()

    def isatty(self) -> bool:
        """Return whether this is an 'interactive' stream"""
        return False

    def set_input(self, data: str) -> None:
        """Set new input data for the stream"""
        self._buffer = io.StringIO(data)

    def __iter__(self):
        """Iterator interface for reading lines"""
        return iter(self._buffer)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class VStdout:
    """Custom stdout implementation"""

    def __init__(self, client: Client = None, forward_to_original: bool = False):
        self._client = client
        self._buffer = io.StringIO()
        self._forward_to_original = forward_to_original
        self._original_stream = sys.__stdout__
        self.encoding = 'utf-8'
        self.errors = 'strict'
        self.newlines = None
        self.closed = False
        self._output_history = []

    def write(self, text: str) -> int:
        """Write string to stream and return number of characters written"""
        if self.closed:
            raise ValueError("I/O operation on closed file")

        text_str = str(text)

        # Store in internal buffer
        chars_written = self._buffer.write(text_str)
        self._output_history.append(text_str)

        # Notify client
        try:
            self._client.send(text_str)
        except (AttributeError, NotImplementedError):
            pass

        # Forward to original stream if requested
        if self._forward_to_original and self._original_stream:
            self._original_stream.write(text_str)

        return chars_written

    def writelines(self, lines) -> None:
        """Write a list of lines to the stream"""
        for line in lines:
            self.write(line)

    def flush(self) -> None:
        """Flush write buffers, if applicable"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self._buffer.flush()
        if self._forward_to_original and self._original_stream:
            self._original_stream.flush()

    def close(self) -> None:
        """Close the stream"""
        self.closed = True
        self._buffer.close()

    def writable(self) -> bool:
        """Return whether object supports writing"""
        return not self.closed

    def isatty(self) -> bool:
        """Return whether this is an 'interactive' stream"""
        return False

    def get_output(self) -> str:
        """Get all output written to this stream"""
        return self._buffer.getvalue()

    def get_output_history(self) -> List[str]:
        """Get history of all write operations"""
        return self._output_history.copy()

    def clear_output(self) -> None:
        """Clear the internal buffer and history"""
        self._buffer = io.StringIO()
        self._output_history.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class VStderr:
    """Custom stderr implementation"""

    def __init__(self, client: Client = None, forward_to_original: bool = False):
        self._client = client
        self._buffer = io.StringIO()
        self._forward_to_original = forward_to_original
        self._original_stream = sys.__stderr__
        self.encoding = 'utf-8'
        self.errors = 'strict'
        self.newlines = None
        self.closed = False
        self._output_history = []

    def write(self, text: str) -> int:
        """Write string to stream and return number of characters written"""
        if self.closed:
            raise ValueError("I/O operation on closed file")

        text_str = str(text)

        # Store in internal buffer
        chars_written = self._buffer.write(text_str)
        self._output_history.append(text_str)

        # Notify client
        try:
            # add color red for stderr output
            self._client.send(f"\033[31m{text_str}\033[0m")
        except (AttributeError, NotImplementedError):
            pass

        # Forward to original stream if requested
        if self._forward_to_original and self._original_stream:
            self._original_stream.write(text_str)

        return chars_written

    def writelines(self, lines) -> None:
        """Write a list of lines to the stream"""
        for line in lines:
            self.write(line)

    def flush(self) -> None:
        """Flush write buffers, if applicable"""
        if self.closed:
            raise ValueError("I/O operation on closed file")
        self._buffer.flush()
        if self._forward_to_original and self._original_stream:
            self._original_stream.flush()

    def close(self) -> None:
        """Close the stream"""
        self.closed = True
        self._buffer.close()

    def writable(self) -> bool:
        """Return whether object supports writing"""
        return not self.closed

    def isatty(self) -> bool:
        """Return whether this is an 'interactive' stream"""
        return False

    def get_output(self) -> str:
        """Get all output written to this stream"""
        return self._buffer.getvalue()

    def get_output_history(self) -> List[str]:
        """Get history of all write operations"""
        return self._output_history.copy()

    def clear_output(self) -> None:
        """Clear the internal buffer and history"""
        self._buffer = io.StringIO()
        self._output_history.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class StreamSTD:
    def __init__(self,
                 client: Client = None,
                 stdin_data: str = "",
                 forward_stdout: bool = False,
                 forward_stderr: bool = False):
        self.client = client
        self._original_stdin = sys.stdin
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        # Create the stream objects
        self.stdin = VStdin(client, stdin_data)
        self.stdout = VStdout(client, forward_stdout)
        self.stderr = VStderr(client, forward_stderr)

        self._is_active = False

    def activate(self) -> None:
        """Replace sys streams with custom streams"""
        sys.stdin = self.stdin
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self._is_active = True

    def deactivate(self) -> None:
        """Restore original sys streams"""
        sys.stdin = self._original_stdin
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        self._is_active = False

    def is_active(self) -> bool:
        """Check if custom streams are currently active"""
        return self._is_active

    def get_captured_output(self) -> dict:
        """Get all captured output from streams"""
        return {
            'stdout': self.stdout.get_output(),
            'stderr': self.stderr.get_output(),
            'stdout_history': self.stdout.get_output_history(),
            'stderr_history': self.stderr.get_output_history()
        }

    def clear_output(self) -> None:
        """Clear all captured output"""
        self.stdout.clear_output()
        self.stderr.clear_output()

    def set_stdin_data(self, data: str) -> None:
        """Set new input data for stdin"""
        self.stdin.set_input(data)

    def __enter__(self):
        """Context manager entry"""
        self.activate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.deactivate()