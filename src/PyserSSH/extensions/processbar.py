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
from threading import Thread, Lock, Event
from time import sleep

from ..system.sysfunc import replace_enter_with_crlf
from ..system.clientype import Client
from ..interactive import wait_inputkey

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

#-------------------------------------------------------------------------------------------

class BarPlus_StackedBar:
    """Represents a segment in a stacked progress bar"""

    def __init__(self, value, max_value, color, label="", layer=0):
        self.value = value
        self.max_value = max_value
        self.color = color
        self.label = label
        self.layer = layer  # Layer depth: 0 = front, higher numbers = back
        self.percentage = (value / max_value * 100) if max_value > 0 else 0


class BarPlus_ProgressBar:
    """Individual progress bar with support for stacked segments"""

    def __init__(self, label, width=40, show_percentage=True, show_values=True, steps_animation=None, ena_steps=True,
                 fill='█', barbackground="░", ena_stack_layer=False, stopped="[  OK  ]", stopped_fail='[FAILED]'):
        self.label = label
        self.width = width
        self.show_percentage = show_percentage
        self.show_values = show_values
        self.stacked_bars = []
        self.info_text = ""
        self.steps_animation = Steps.sending if not steps_animation else steps_animation
        self.current_steps_ani = 0
        self.total_steps_ani = len(self.steps_animation)
        self.ena_steps = ena_steps
        self.fill = fill
        self.barbackground = barbackground
        self.ena_stack_layer = ena_stack_layer
        self.stopped = stopped
        self.stopped_fail = stopped_fail
        self.is_stopped = False
        self.is_failed = False

    def change_animation_steps(self, steps_animation):
        """Change the animation steps used for rendering"""
        self.steps_animation = steps_animation
        self.total_steps_ani = len(steps_animation)
        self.current_steps_ani = 0

    def add_segment(self, value, max_value, color, label="", layer=0):
        """Add a segment to the stacked bar with optional layer support"""
        segment = BarPlus_StackedBar(value, max_value, color, label, layer)
        self.stacked_bars.append(segment)

    def update_segment(self, index, value):
        """Update the value of a specific segment"""
        if 0 <= index < len(self.stacked_bars):
            self.stacked_bars[index].value = value
            self.stacked_bars[index].percentage = (
                    value / self.stacked_bars[index].max_value * 100
            ) if self.stacked_bars[index].max_value > 0 else 0

    def set_info(self, text):
        """Set additional info text to display"""
        self.info_text = text

    def stop(self):
        """Stop the progress bar and show success status"""
        self.is_stopped = True
        self.is_failed = False

    def stopfail(self):
        """Stop the progress bar and show failure status"""
        self.is_stopped = True
        self.is_failed = True

    def render(self):
        """Render the progress bar as a string"""
        # If stopped, return the stopped status instead of the normal bar
        if self.is_stopped:
            status = self.stopped_fail if self.is_failed else self.stopped
            return f"{status}"

        if not self.stacked_bars:
            return f"{self.label}: No data"

        # Calculate total percentage for display
        total_percentage = 0
        total_current = 0
        total_max = 0

        for bar in self.stacked_bars:
            total_current += bar.value
            total_max += bar.max_value

        if total_max > 0:
            total_percentage = (total_current / total_max) * 100

        # Build the visual bar
        if self.ena_stack_layer:
            bar_str = self._render_layered_bar(total_max)
        else:
            bar_str = self._render_traditional_bar(total_percentage, total_max)

        # Build the result string with animation at the front
        result_parts = []

        # Add animation at the very front if enabled
        if self.ena_steps:
            result_parts.append(f"{self.steps_animation[self.current_steps_ani]}")
            self.current_steps_ani = (self.current_steps_ani + 1) % self.total_steps_ani

        # Add label
        result_parts.append(f"{self.label}")

        # Add percentage if requested
        if self.show_percentage:
            result_parts.append(f"{total_percentage:3.0f}%")

        # Add the bar itself
        result_parts.append(f"|{bar_str}|")

        # Add segment information
        if self.stacked_bars:
            segments_info = []
            for bar in self.stacked_bars:
                if bar.label:
                    layer_info = f" [L{bar.layer}]" if self.ena_stack_layer else ""
                    segments_info.append(f"{bar.label}: {bar.value}/{bar.max_value}{layer_info}")

            if segments_info:
                result_parts.append(f"{' | '.join(segments_info)}")

        # Add info text
        if self.info_text:
            result_parts.append(f"{self.info_text}")

        # Join all parts with appropriate separators
        return f"{result_parts[0]} {result_parts[1]} | {result_parts[2]} {result_parts[3]} {' '.join(result_parts[4:])}"

    def _render_layered_bar(self, total_max):
        """Render bar with layer support - segments are rendered back to front"""
        # Create array to hold the final bar characters
        bar_chars = [' '] * self.width

        # Sort segments by layer (highest layer first, so they render in back)
        sorted_segments = sorted(self.stacked_bars, key=lambda x: x.layer, reverse=True)

        for segment in sorted_segments:
            if segment.value <= 0:
                continue

            # Calculate the segment's width based on its own percentage
            # Each segment fills independently based on its value/max_value ratio
            segment_width = int((segment.value / segment.max_value) * self.width) if segment.max_value > 0 else 0

            # For layered rendering, each segment starts from the beginning
            # and fills up to its value, overlaying previous layers
            for i in range(min(segment_width, self.width)):
                colored_char = TextFormatter.format_text_truecolor(self.fill, segment.color)
                bar_chars[i] = colored_char

        # Fill remaining space with background
        for i in range(self.width):
            if bar_chars[i] == ' ':
                bar_chars[i] = self.barbackground

        return ''.join(bar_chars)

    def _render_traditional_bar(self, total_percentage, total_max):
        """Render bar with traditional stacking - segments are placed side by side"""
        filled_chars = int((total_percentage / 100) * self.width)
        empty_chars = self.width - filled_chars

        # Create stacked visual representation
        bar_parts = []
        remaining_filled = filled_chars

        for i, bar in enumerate(self.stacked_bars):
            if remaining_filled <= 0:
                break

            # Calculate how much of this segment should be filled
            segment_percentage = bar.percentage
            segment_filled = int((segment_percentage / 100) * (bar.max_value / total_max * self.width))
            segment_filled = min(segment_filled, remaining_filled)

            if segment_filled > 0:
                # Use foreground color for the block characters
                bar_parts.append(TextFormatter.format_text_truecolor(self.fill * segment_filled, bar.color))
                remaining_filled -= segment_filled

        # Add empty space
        if empty_chars > 0:
            bar_parts.append(self.barbackground * empty_chars)

        return ''.join(bar_parts)


class BarPlus_Display:
    """Manages multiple progress bars with terminal positioning"""

    def __init__(self, client: Client, title="Progress bar", update_rate=0.1):
        self.client = client
        self.title = title
        self.bars = []
        self.static_lines = []
        self.terminal_width = self.client["windowsize"]["width"]
        self.terminal_height = self.client["windowsize"]["height"]
        self.lock = Lock()
        self.start_row = 1
        self.update_rate = update_rate
        self.on_key_handle = None  # Placeholder for key event handler
        self.is_paused = False

        # Threading controls
        self._stop_event = Event()
        self._thread = None
        self._is_running = False

    def add_static_line(self, text):
        """Add a static line that appears at the top"""
        with self.lock:
            self.static_lines.append(text)

    def add_progress_bar(self, bar):
        """Add a progress bar to the display"""
        with self.lock:
            self.bars.append(bar)

    def remove_progress_bar(self, bar):
        """Remove a progress bar from the display"""
        with self.lock:
            if bar in self.bars:
                self.bars.remove(bar)

    def clear_static_lines(self):
        """Clear all static lines"""
        with self.lock:
            self.static_lines.clear()

    def move_cursor_to(self, row, col=0):
        """Move cursor to specific position"""
        return f"\033[{row};{col}H"

    def clear_line(self):
        """Clear current line"""
        return "\033[2K"

    def hide_cursor(self):
        """Hide terminal cursor"""
        return "\033[?25l"

    def show_cursor(self):
        """Show terminal cursor"""
        return "\033[?25h"

    def save_cursor(self):
        """Save cursor position"""
        return "\033[s"

    def restore_cursor(self):
        """Restore cursor position"""
        return "\033[u"

    def render(self):
        """Render the complete display"""
        with self.lock:
            output = []
            current_row = self.start_row

            # Add title
            if self.title:
                output.append(self.move_cursor_to(current_row))
                output.append(self.clear_line())
                output.append(TextFormatter.format_text(self.title, attributes='bold'))
                current_row += 1

                # Empty line after title
                output.append(self.move_cursor_to(current_row))
                output.append(self.clear_line())
                current_row += 1

            # Add static lines
            for line in self.static_lines:
                output.append(self.move_cursor_to(current_row))
                output.append(self.clear_line())
                # Truncate if too long
                if len(line) > self.terminal_width:
                    line = line[:self.terminal_width - 3] + "..."
                output.append(line)
                current_row += 1

            # Empty line after static lines
            if self.static_lines:
                output.append(self.move_cursor_to(current_row))
                output.append(self.clear_line())
                current_row += 1

            # Add progress bars
            for bar in self.bars:
                output.append(self.move_cursor_to(current_row))
                output.append(self.clear_line())
                rendered_bar = bar.render()
                # Truncate if too long
                # if len(rendered_bar) > self.terminal_width:
                #     rendered_bar = rendered_bar[:self.terminal_width - 3] + "..."
                output.append(rendered_bar)
                current_row += 1

            return ''.join(output)

    def start(self):
        """Start the display loop"""
        if self._is_running:
            return False  # Already running

        self._stop_event.clear()
        self._is_running = True
        self._thread = Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop the display loop"""
        if not self._is_running:
            return False  # Not running

        self._stop_event.set()
        self._is_running = False

        # Wait for thread to finish (with timeout)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        return True

    def exit(self):
        """Exit and cleanup the display"""
        self.stop()
        self.cleanup()

    def is_running(self):
        """Check if the display loop is running"""
        return self._is_running

    def _update_loop(self):
        """Update the display periodically"""
        try:
            while not self._stop_event.is_set():
                if not self.is_paused:
                    self.display()

                    if self.on_key_handle:
                        key = wait_inputkey(self.client, timeout=self.update_rate)
                        if key:
                            self.on_key_handle(key)
                    else:
                        # Use wait instead of sleep for better responsiveness
                        if self._stop_event.wait(timeout=self.update_rate):
                            break  # Stop event was set

        except Exception as e:
            print(f"Error in display update loop: {e}")
        finally:
            self._is_running = False

    def display(self):
        """Display the progress bars"""
        Print(self.client.channel, self.hide_cursor() + self.render(), end='')

    def cleanup(self):
        """Clean up display"""
        Print(self.client.channel, self.show_cursor())

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.exit()

    def __del__(self):
        """Destructor - ensure cleanup"""
        if hasattr(self, '_is_running') and self._is_running:
            self.exit()