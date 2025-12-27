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
import os
import platform
import sys
import time

import GPUtil
import cpuinfo
import distro
import psutil

from ..server import Server
from ..system.clientype import Client
from ..system.info import version as libversion

def get_accurate_windows_version():
    """
    Returns 'Windows 11' or 'Windows 10' (or other for older Windows).
    """
    if platform.system() == "Windows":
        version_info = sys.getwindowsversion()
        # Windows 11 is version 10.0 but with a build number >= 22000
        if version_info.major >= 10 and version_info.build >= 22000:
            return "Windows 11"
        elif version_info.major == 10:
            return "Windows 10"
        else:
            # Fallback for older versions or unexpected results
            return f"Windows {version_info.major}.{version_info.minor}"
    else:
        # Not Windows, return the standard system name
        return platform.system()

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

def center_string(main_string, replacement_string):
    # Find the center index of the main string
    center_index = len(main_string) // 2

    # Calculate the start and end indices for replacing
    start_index = center_index - len(replacement_string) // 2
    end_index = start_index + len(replacement_string)

    # Replace the substring at the center
    new_string = main_string[:start_index] + replacement_string + main_string[end_index:]

    return new_string

def get_format_time(sec):
    if sec >= 31557600: # years
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        return f"{y}y {d}d {h}h {m}m {s}s"
    elif sec >= 2628002: # months
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        mo, d = divmod(d, 30)
        return f"{mo}mo {d}d {h}h {m}m {s}s"
    elif sec >= 604800:# weeks
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        return f"{w}w {d}d {h}h {m}m {s}s"
    elif sec >= 86400: # days
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"{d}d {h}h {m}m {s}s"
    elif sec >= 3600:# hours
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"{h}h {m}m {s}s"
    elif sec >= 60: # minutes
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return f"{m}m {s}s"
    else:
        return f"{sec}s"

def get_memory_info():
    vm = psutil.virtual_memory()
    total = vm.total / (1024**3)
    used = (vm.total - vm.available) / (1024**3)
    percent = vm.percent
    return total, used, percent

def get_disk_info():
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mount": part.mountpoint,
                "total": usage.total / (1024**3),
                "used": usage.used / (1024**3),
                "percent": usage.percent,
                "fstype": part.fstype
            })
        except PermissionError:
            continue
    return disks

class pyofetch:
    def __init__(self):
        RESET = TextFormatter.RESET
        BOLD = TextFormatter.TEXT_ATTRIBUTES["bold"]

        BLACK = TextFormatter.TEXT_COLORS["black"]
        RED = TextFormatter.TEXT_COLORS["red"]
        GREEN = TextFormatter.TEXT_COLORS["green"]
        YELLOW = TextFormatter.TEXT_COLORS["yellow"]
        BLUE = TextFormatter.TEXT_COLORS["blue"]
        MAGENTA = TextFormatter.TEXT_COLORS["magenta"]
        CYAN = TextFormatter.TEXT_COLORS["cyan"]
        WHITE = TextFormatter.TEXT_COLORS["white"]

        self.ASCII_LOGO = [
            "                ",
            "    {}████████{}    ".format(YELLOW+BOLD, RESET),
            "  {}██{}{}████████{}{}██{}  ".format(WHITE, RESET, YELLOW+BOLD, RESET, WHITE, RESET),
            "{}████{}{}████████{}{}████{}".format(YELLOW+BOLD, RESET, YELLOW, RESET, YELLOW+BOLD, RESET),
            "{}██{}{}██{}{}██{}{}████████{}{}██{}".format(YELLOW+BOLD, RESET, YELLOW, RESET, BLACK+BOLD, RESET, YELLOW, RESET, YELLOW+BOLD, RESET),
            "{}██{}██{}  {}██{}{}██{}  {}██{}██{}".format(YELLOW, WHITE, RESET, BLACK+BOLD, RESET, YELLOW, RESET, WHITE, YELLOW, RESET),
            "{}██{}██{}  {}████{}  {}██{}██{}".format(YELLOW, WHITE, RESET, BLACK+BOLD, RESET, WHITE, YELLOW, RESET),
            "{}████████████████{}".format(BLACK+BOLD, RESET),
            "{}████████████████{}".format(BLACK+BOLD, RESET),
            "                ",
        ]

        D_COLORS = [BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE]
        B_COLORS = [c[:-1] + ";1m" for c in D_COLORS]

        self.bright_colors = [color + "███" for color in B_COLORS]
        self.dark_colors = [color + "███" for color in D_COLORS]
        self.RESET = RESET

    def render(self, info, ascii_logo, gap=1):
        combined_lines = []

        # Adjust lengths of lists to match
        if len(ascii_logo) < len(info):
            for _ in range(len(info) - len(ascii_logo)):
                ascii_logo.append(" " * len(ascii_logo[0]))
        elif len(ascii_logo) > len(info):
            for _ in range(len(ascii_logo) - len(info)):
                info.append(" ")

        # Combine lines of ascii_logo and info
        for (art_line, info_line) in zip(ascii_logo, info):
            combined_lines.append(("{}" + (" " * gap) + "{}").format(art_line, info_line))

        return combined_lines

    def info(self, server: Server, client: Client, moreinfo="", Itext_theme="yellow", text_theme="cyan", logo=None, raw_out=False):
        client_name = client.get_name()
        hostname = server.hostname
        node = platform.node()
        hostnameofhost = os.getlogin()

        unformatted_length = len(client_name) + len("@") + len(hostname) + len(" in ") + len(hostnameofhost) + len("@") + len(node)

        userhost = (
                TextFormatter.format_text(client_name, color=text_theme)
                + TextFormatter.format_text("@", color=Itext_theme)
                + TextFormatter.format_text(hostname, color=text_theme)
                + TextFormatter.format_text(" in ", color=Itext_theme)
                + TextFormatter.format_text(hostnameofhost, color=text_theme)
                + TextFormatter.format_text("@", color=Itext_theme)
                + TextFormatter.format_text(node, color=text_theme)
        )

        if platform.system() == "Windows":
            os_name = get_accurate_windows_version() + f" {cpuinfo.get_cpu_info()['arch']}"
            kernelinfo = f"{os.name} {platform.version()}"
        elif platform.system() == "Linux":
            distro_name = distro.name(pretty=True)
            os_name = f"{distro_name} {cpuinfo.get_cpu_info()['arch']}"
            kernelinfo = f"{platform.system()} {platform.release()}"
        else:
            kernelinfo = f"{platform.system()} {platform.release()}"
            os_name = f"{platform.system()} {platform.release()} ({platform.version()}) {cpuinfo.get_cpu_info()['arch']}"

        formatted_uptime = get_format_time(int(time.time() - psutil.boot_time()))

        formatted_uptime_server = get_format_time(int(time.time() - server.startuptime))

        gpus = GPUtil.getGPUs() or []
        disks = get_disk_info()
        mem_total, mem_used, mem_percent = get_memory_info()

        allinfo = [
            f"{userhost}",
            f"{TextFormatter.format_text(center_string('-'*unformatted_length, 'Host'), color=text_theme)}",
            f"{TextFormatter.format_text('OS', color=Itext_theme)}: {TextFormatter.format_text(os_name, color=text_theme)}",
            f"{TextFormatter.format_text('Kernel', color=Itext_theme)}: {TextFormatter.format_text(kernelinfo, color=text_theme)}",
            f"{TextFormatter.format_text('Uptime', color=Itext_theme)}: {TextFormatter.format_text(formatted_uptime, color=text_theme)}",
            f"{TextFormatter.format_text('CPU', color=Itext_theme)}: {TextFormatter.format_text(cpuinfo.get_cpu_info()['brand_raw'], color=text_theme)}"
        ]

        for i, gpu in enumerate(gpus):
            allinfo.append(f"{TextFormatter.format_text(f'GPU {i+1}', color=Itext_theme)}: {TextFormatter.format_text(gpu.name, color=text_theme)}")

        allinfo.append(
            f"{TextFormatter.format_text('Memory', color=Itext_theme)}: {TextFormatter.format_text(f'{mem_used:.2f} / {mem_total:.2f} GiB ({mem_percent}%)', color=text_theme)}")

        for d in disks:
            allinfo.append("{}: {}".format(TextFormatter.format_text(f'Disk ({d["device"]})', color=Itext_theme), TextFormatter.format_text(f'{d["used"]:.2f} / {d["total"]:.2f} GiB ({d["percent"]}%) - {d["fstype"]}', color=text_theme)))

        allinfo.append(TextFormatter.format_text(center_string('-'*unformatted_length, 'System'), color=text_theme))

        allinfo.append(f"{TextFormatter.format_text('Runtime', color=Itext_theme)}: {TextFormatter.format_text(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}', color=text_theme)}")
        allinfo.append(f"{TextFormatter.format_text('PyserSSH', color=Itext_theme)}: {TextFormatter.format_text(libversion, color=text_theme)}")
        allinfo.append(f"{TextFormatter.format_text('Protocol', color=Itext_theme)}: {TextFormatter.format_text(server._protocol.upper(), color=text_theme)}")
        allinfo.append(f"{TextFormatter.format_text('Server Uptime', color=Itext_theme)}: {TextFormatter.format_text(formatted_uptime_server, color=text_theme)}")

        allinfo.append(TextFormatter.format_text(center_string('-' * unformatted_length, 'Client'), color=text_theme))
        allinfo.append(f"{TextFormatter.format_text('Connection IP', color=Itext_theme)}: {TextFormatter.format_text(client.get_peername()[0], color=text_theme)}")
        allinfo.append(f"{TextFormatter.format_text('Terminal Size', color=Itext_theme)}: {TextFormatter.format_text(f'{client.get_terminal_size()[0]}x{client.get_terminal_size()[1]}', color=text_theme)}")
        allinfo.append(f"{TextFormatter.format_text('Session Uptime', color=Itext_theme)}: {TextFormatter.format_text(get_format_time(int(client.get_session_duration())), color=text_theme)}")

        if moreinfo:
            allinfo.append(TextFormatter.format_text(center_string('-' * unformatted_length, 'Info'), color=text_theme))
            allinfo.append(moreinfo)

        allinfo.append("")
        allinfo.append("".join(self.dark_colors) + self.RESET)
        allinfo.append("".join(self.bright_colors) + self.RESET)
        allinfo.append("")

        rendered = self.render(allinfo, self.ASCII_LOGO if logo is None else logo)

        if not raw_out:
            for line in rendered:
                client.sendln(line)

        return rendered