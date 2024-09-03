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

def replace_enter_with_crlf(input_string):
    if isinstance(input_string, str):
        # Replace '\n' with '\r\n' in the string
        input_string = input_string.replace('\n', '\r\n')
        # Encode the string to bytes
        return input_string.encode()
    elif isinstance(input_string, bytes):
        # Decode bytes to string
        decoded_string = input_string.decode()
        # Replace '\n' with '\r\n' in the string
        modified_string = decoded_string.replace('\n', '\r\n')
        # Encode the modified string back to bytes
        return modified_string.encode()
    else:
        raise TypeError("Input must be a string or bytes")

def text_centered_screen(text, screen_width, screen_height, spacecharacter=" "):
    screen = []
    lines = text.split("\n")
    padding_vertical = (screen_height - len(lines)) // 2  # Calculate vertical padding

    for y in range(screen_height):
        line = ""
        if padding_vertical <= y < padding_vertical + len(lines):  # Check if it's within the range of the text lines
            index = y - padding_vertical  # Get the corresponding line index
            padding_horizontal = (screen_width - len(lines[index])) // 2  # Calculate horizontal padding for each line
            line += spacecharacter * padding_horizontal + lines[index] + spacecharacter * padding_horizontal
        else:  # Fill other lines with space characters
            line += spacecharacter * screen_width
        screen.append(line)

    return "\n".join(screen)