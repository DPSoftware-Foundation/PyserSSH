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
# this file is from damp11113-library

from itertools import cycle
import math
import time
from threading import Thread
from time import sleep

from ..system.sysfunc import replace_enter_with_crlf
from ..system.clientype import Client

def Print(channel, string, start="", end="\n"):
    channel.send(replace_enter_with_crlf(start + string + end))

def get_size_unit2(number, unitp, persec=True, unitsize=1024, decimal=True, space=" "):
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if number < unitsize:
            if decimal:
                num = f"{number:.2f}"
            else:
                num = int(number)

            if persec:
                return f"{num}{space}{unit}{unitp}/s"
            else:
                return f"{num}{space}{unit}{unitp}"
        number /= unitsize

def center_string(main_string, replacement_string):
    # Find the center index of the main string
    center_index = len(main_string) // 2

    # Calculate the start and end indices for replacing
    start_index = center_index - len(replacement_string) // 2
    end_index = start_index + len(replacement_string)

    # Replace the substring at the center
    new_string = main_string[:start_index] + replacement_string + main_string[end_index:]

    return new_string

class TextFormatter:
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

        if color in TextFormatter.TEXT_COLORS:
            if color_level in TextFormatter.TEXT_COLOR_LEVELS:
                color_code = TextFormatter.TEXT_COLORS[color]
                color_format = TextFormatter.TEXT_COLOR_LEVELS[color_level].format(color_code)
                formatted_text += color_format
            else:
                formatted_text += TextFormatter.TEXT_COLORS[color]

        if background in TextFormatter.BACKGROUND_COLORS:
            formatted_text += TextFormatter.BACKGROUND_COLORS[background]

        if attributes in TextFormatter.TEXT_ATTRIBUTES:
            formatted_text += TextFormatter.TEXT_ATTRIBUTES[attributes]

        if target_text == "":
            formatted_text += text + TextFormatter.RESET
        else:
            formatted_text += text[:start_index] + text[start_index:end_index] + TextFormatter.RESET + text[end_index:]

        return formatted_text

    @staticmethod
    def format_text_truecolor(text, color=None, background=None, attributes=None, target_text=''):
        formatted_text = ""
        start_index = text.find(target_text)
        end_index = start_index + len(target_text) if start_index != -1 else len(text)

        if color:
            formatted_text += f"\033[38;2;{color}m"

        if background:
            formatted_text += f"\033[48;2;{background}m"

        if attributes in TextFormatter.TEXT_ATTRIBUTES:
            formatted_text += TextFormatter.TEXT_ATTRIBUTES[attributes]

        if target_text == "":
            formatted_text += text + TextFormatter.RESET
        else:
            formatted_text += text[:start_index] + text[start_index:end_index] + TextFormatter.RESET + text[end_index:]

        return formatted_text

def insert_string(base, inserted, position=0):
    return base[:position] + inserted + base[position + len(inserted):]

class Steps:
    sending = ['[   ]', '[-  ]', '[-- ]', '[---]', '[ --]', '[  -]']
    requesting = ['[   ]', '[-  ]', '[ - ]', '[  -]']
    waiting = ['[   ]', '[-  ]', '[-- ]', '[ --]', '[  -]', '[   ]', '[  -]', '[ --]', '[-- ]', '[-  ]']
    pinging = ['[   ]', '[-  ]', '[ - ]', '[  -]', '[   ]', '[  -]', '[ - ]', '[-  ]', '[   ]']
    receiving = ['[   ]', '[  -]', '[ --]', '[---]', '[-- ]', '[-  ]']
    connecting = ['[   ]', '[  -]', '[ - ]', '[-  ]']

    expand_contract = ['[    ]', '[=   ]', '[==  ]', '[=== ]', '[====]', '[ ===]', '[  ==]', '[   =]', '[    ]']
    rotating_dots = ['.    ', '..   ', '...  ', '.... ', '.....', ' ....', '  ...', '   ..', '    .', '     ']
    bouncing_ball = ['o     ', ' o    ', '  o   ', '   o  ', '    o ', '     o', '    o ', '   o  ', '  o   ', ' o    ', 'o     ']
    left_right_dots = ['[    ]', '[.   ]', '[..  ]', '[... ]', '[....]', '[ ...]', '[  ..]', '[   .]', '[    ]']
    expanding_square = ['[ ]', '[■]', '[■■]', '[■■■]', '[■■■■]', '[■■■]', '[■■]', '[■]', '[ ]']
    spinner = ['|', '/', '-', '\\', '|', '/', '-', '\\']
    zigzag = ['/   ', ' /  ', '  / ', '   /', '  / ', ' /  ', '/   ', '\\   ', ' \\  ', '  \\ ', '   \\', '  \\ ', ' \\  ', '\\   ']
    arrows = ['←  ', '←← ', '←←←', '←← ', '←  ', '→  ', '→→ ', '→→→', '→→ ', '→  ']
    snake = ['[>    ]', '[=>   ]', '[==>  ]', '[===> ]', '[====>]', '[ ===>]', '[  ==>]', '[   =>]', '[    >]']
    loading_bar = ['[          ]', '[=         ]', '[==        ]', '[===       ]', '[====      ]', '[=====     ]', '[======    ]', '[=======   ]', '[========  ]', '[========= ]', '[==========]']

class indeterminateStatus:
    def __init__(self, client: Client, desc="Loading...", end="[  OK  ]", timeout=0.1, fail='[FAILED]', steps=None):
        self.client = client
        self.desc = desc
        self.end = end
        self.timeout = timeout
        self.faill = fail

        self._thread = Thread(target=self._animate, daemon=True)
        if steps is None:
            self.steps = Steps.sending
        else:
            self.steps = steps
        self.done = False
        self.fail = False

    def start(self):
        """Start progress bar"""
        self._thread.start()
        return self

    def _animate(self):
        for c in cycle(self.steps):
            if self.done:
                break
            Print(self.client['channel'], f"\r{c} {self.desc}" , end="")
            sleep(self.timeout)

    def __enter__(self):
        self.start()

    def stop(self):
        """stop progress"""
        self.done = True
        cols = self.client["windowsize"]["width"]
        Print(self.client['channel'], "\r" + " " * cols, end="")
        Print(self.client['channel'], f"\r{self.end}")

    def stopfail(self):
        """stop progress with error or fail"""
        self.done = True
        self.fail = True
        cols = self.client["windowsize"]["width"]
        Print(self.client['channel'], "\r" + " " * cols, end="")
        Print(self.client['channel'], f"\r{self.faill}")

    def __exit__(self, exc_type, exc_value, tb):
        # handle exceptions with those variables ^
        self.stop()

class LoadingProgress:
    def __init__(self, client: Client, total=100, totalbuffer=None, length=50, fill='█', fillbufferbar='█', desc="Loading...", status="", enabuinstatus=True, end="[  OK  ]", timeout=0.1, fail='[FAILED]', steps=None, unit="it", barbackground="-", shortnum=False, buffer=False, shortunitsize=1000, currentshortnum=False, show=True, indeterminate=False, barcolor="red", bufferbarcolor="white",barbackgroundcolor="black", color=True):
        """
        Simple loading progress bar python
        @param client: from ssh client request
        @param total: change all total
        @param desc: change description
        @param status: change progress status
        @param end: change success progress
        @param timeout: change speed
        @param fail: change error stop
        @param steps: change steps animation
        @param unit: change unit
        @param buffer: enable buffer progress (experiment)
        @param show: show progress bar
        @param indeterminate: indeterminate mode
        @param barcolor: change bar color
        @param bufferbarcolor: change buffer bar color
        @param barbackgroundcolor: change background color
        @param color: enable colorful
        """
        self.client = client

        self.desc = desc
        self.end = end
        self.timeout = timeout
        self.faill = fail
        self.total = total
        self.length = length
        self.fill = fill
        self.enbuinstatus = enabuinstatus
        self.status = status
        self.barbackground = barbackground
        self.unit = unit
        self.shortnum = shortnum
        self.shortunitsize = shortunitsize
        self.currentshortnum = currentshortnum
        self.printed = show
        self.indeterminate = indeterminate
        self.barcolor = barcolor
        self.barbackgroundcolor = barbackgroundcolor
        self.enabuffer = buffer
        self.bufferbarcolor = bufferbarcolor
        self.fillbufferbar = fillbufferbar
        self.totalbuffer = totalbuffer
        self.enacolor = color

        self._thread = Thread(target=self._animate, daemon=True)

        if steps is None:
            self.steps = Steps.sending
        else:
            self.steps = steps

        if self.totalbuffer is None:
            self.totalbuffer = self.total

        self.currentpercent = 0
        self.currentbufferpercent = 0
        self.current = 0
        self.currentbuffer = 0
        self.startime = 0
        self.done = False
        self.fail = False
        self.currentprint = ""

    def start(self):
        """Start progress bar"""
        self._thread.start()
        self.startime = time.perf_counter()
        return self

    def update(self, i=1):
        """update progress"""
        self.current += i

    def updatebuffer(self, i=1):
        """update buffer progress"""
        self.currentbuffer += i

    def _animate(self):
        for c in cycle(self.steps):
            if self.done:
                break

            if not self.indeterminate:
                if self.total != 0 or math.trunc(float(self.currentpercent)) > 100:
                    if self.enabuffer:
                        self.currentpercent = ("{0:.1f}").format(100 * (self.current / float(self.total)))

                        filled_length = int(self.length * self.current // self.total)

                        if self.enacolor:
                            bar = TextFormatter.format_text(self.fill * filled_length, self.barcolor)
                        else:
                            bar = self.fill * filled_length

                        self.currentbufferpercent = ("{0:.1f}").format(
                            100 * (self.currentbuffer / float(self.totalbuffer)))

                        if float(self.currentbufferpercent) >= 100.0:
                            self.currentbufferpercent = 100

                        filled_length_buffer = int(self.length * self.currentbuffer // self.totalbuffer)

                        if filled_length_buffer >= self.length:
                            filled_length_buffer = self.length

                        if self.enacolor:
                            bufferbar = TextFormatter.format_text(self.fillbufferbar * filled_length_buffer,
                                                                  self.bufferbarcolor)
                        else:
                            bufferbar = self.fillbufferbar * filled_length_buffer

                        bar = insert_string(bufferbar, bar)

                        if self.enacolor:
                            bar += TextFormatter.format_text(self.barbackground * (self.length - filled_length_buffer),
                                                            self.barbackgroundcolor)
                        else:
                            bar += self.barbackground * (self.length - filled_length_buffer)
                    else:
                        self.currentpercent = ("{0:.1f}").format(100 * (self.current / float(self.total)))
                        filled_length = int(self.length * self.current // self.total)
                        if self.enacolor:
                            bar = TextFormatter.format_text(self.fill * filled_length, self.barcolor)

                            bar += TextFormatter.format_text(self.barbackground * (self.length - filled_length),
                                                             self.barbackgroundcolor)
                        else:
                            bar = self.fill * filled_length
                            if self.enacolor:
                                bar = TextFormatter.format_text(bar, self.barcolor)
                            bar += self.barbackground * (self.length - filled_length)


                    if self.enbuinstatus:
                        elapsed_time = time.perf_counter() - self.startime
                        speed = self.current / elapsed_time if elapsed_time > 0 else 0
                        remaining = self.total - self.current
                        eta_seconds = remaining / speed if speed > 0 else 0
                        elapsed_formatted = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
                        eta_formatted = time.strftime('%H:%M:%S', time.gmtime(eta_seconds))
                        if self.shortnum:
                            stotal = get_size_unit2(self.total, '', False, self.shortunitsize, False, '')
                            scurrent = get_size_unit2(self.current, '', False, self.shortunitsize, self.currentshortnum, '')
                        else:
                            stotal = self.total
                            scurrent = self.current

                        if math.trunc(float(self.currentpercent)) > 100:
                            elapsed_time = time.perf_counter() - self.startime
                            elapsed_formatted = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))

                            bar = center_string(self.barbackground * self.length, TextFormatter.format_text("Indeterminate", self.barcolor))

                            self.currentprint = f"{c} {self.desc} | --%|{bar}| {scurrent}/{stotal} | {elapsed_formatted} | {get_size_unit2(speed, self.unit, self.shortunitsize)} | {self.status}"

                        else:
                            self.currentprint = f"{c} {self.desc} | {math.trunc(float(self.currentpercent))}%|{bar}| {scurrent}/{stotal} | {elapsed_formatted}<{eta_formatted} | {get_size_unit2(speed, self.unit, self.shortunitsize)} | {self.status}"
                    else:
                        if self.shortnum:
                            stotal = get_size_unit2(self.total, '', False, self.shortunitsize, False, '')
                            scurrent = get_size_unit2(self.current, '', False, self.shortunitsize, self.currentshortnum, '')
                        else:
                            stotal = self.total
                            scurrent = self.current

                        self.currentprint = f"{c} {self.desc} | {math.trunc(float(self.currentpercent))}%|{bar}| {scurrent}/{stotal} | {self.status}"
                else:
                    elapsed_time = time.perf_counter() - self.startime
                    elapsed_formatted = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))

                    bar = center_string(self.barbackground * self.length, TextFormatter.format_text("Indeterminate", self.barcolor))

                    self.currentprint = f"{c} {self.desc} | --%|{bar}| {elapsed_formatted} | {self.status}"
            else:
                elapsed_time = time.perf_counter() - self.startime
                elapsed_formatted = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))

                bar = center_string(self.barbackground * self.length, TextFormatter.format_text("Indeterminate", self.barcolor))

                self.currentprint = f"{c} {self.desc} | --%|{bar}| {elapsed_formatted} | {self.status}"

            if self.printed:
                Print(self.client["channel"], f"\r{self.currentprint}", end="")

            sleep(self.timeout)

    def __enter__(self):
        self.start()

    def stop(self):
        """stop progress"""
        self.done = True
        cols = self.client["windowsize"]["width"]
        Print(self.client["channel"], "\r" + " " * cols, end="")
        Print(self.client["channel"], f"\r{self.end}")

    def stopfail(self):
        """stop progress with error or fail"""
        self.done = True
        self.fail = True
        cols = self.client["windowsize"]["width"]
        Print(self.client["channel"], "\r" + " " * cols, end="")
        Print(self.client["channel"], f"\r{self.faill}")

    def __exit__(self, exc_type, exc_value, tb):
        # handle exceptions with those variables ^
        self.stop()