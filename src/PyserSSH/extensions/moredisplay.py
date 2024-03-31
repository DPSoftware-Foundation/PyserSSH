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

def clickable_url(url, link_text=""):
    return f"\033]8;;{url}\033\\{link_text}\033]8;;\033\\"

class BasicTextFormatter:
    RESET = "\033[0m"
    TEXT_COLORS = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m"
    }
    TEXT_COLOR_LEVELS = {
        "light": "\033[1;{}m",  # Light color prefix
        "dark": "\033[2;{}m"  # Dark color prefix
    }
    BACKGROUND_COLORS = {
        "black": "\033[40m",
        "red": "\033[41m",
        "green": "\033[42m",
        "yellow": "\033[43m",
        "blue": "\033[44m",
        "magenta": "\033[45m",
        "cyan": "\033[46m",
        "white": "\033[47m"
    }
    TEXT_ATTRIBUTES = {
        "bold": "\033[1m",
        "italic": "\033[3m",
        "underline": "\033[4m",
        "blink": "\033[5m",
        "reverse": "\033[7m",
        "strikethrough": "\033[9m"
    }

    @staticmethod
    def format_text(text, color=None, color_level=None, background=None, attributes=None, target_text=''):
        formatted_text = ""
        start_index = text.find(target_text)
        end_index = start_index + len(target_text) if start_index != -1 else len(text)

        if color in BasicTextFormatter.TEXT_COLORS:
            if color_level in BasicTextFormatter.TEXT_COLOR_LEVELS:
                color_code = BasicTextFormatter.TEXT_COLORS[color]
                color_format = BasicTextFormatter.TEXT_COLOR_LEVELS[color_level].format(color_code)
                formatted_text += color_format
            else:
                formatted_text += BasicTextFormatter.TEXT_COLORS[color]

        if background in BasicTextFormatter.BACKGROUND_COLORS:
            formatted_text += BasicTextFormatter.BACKGROUND_COLORS[background]

        if attributes in BasicTextFormatter.TEXT_ATTRIBUTES:
            formatted_text += BasicTextFormatter.TEXT_ATTRIBUTES[attributes]

        if target_text == "":
            formatted_text += text + BasicTextFormatter.RESET
        else:
            formatted_text += text[:start_index] + text[start_index:end_index] + BasicTextFormatter.RESET + text[end_index:]

        return formatted_text
