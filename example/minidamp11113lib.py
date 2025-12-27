import natsort
import os
import re

def sort_files(file_list, reverse=False):
    flist = []
    for file in file_list:
        flist.append(file)
    return natsort.natsorted(flist, reverse=reverse)

def allfiles(folder, scan_subfolders=False, include_path=False, sort_by=None, sort_reverse=False, valid_extensions=None):
    """
    Scans files in a specified folder (and optionally its subfolders), and returns a list of file names
    with options for sorting and including the full file path.

    Parameters:
    - folder (str): The path of the folder to scan for files.
    - scan_subfolders (bool): If True, recursively scans subfolders. Defaults to False.
    - include_path (bool): If True, includes the full path of each file. Defaults to False.
    - sort_by (str or None): Defines the sorting criterion. Options are:
        - 'name': Sort files alphabetically.
        - 'size': Sort files by size.
        - 'created': Sort files by creation time.
        - 'modified': Sort files by last modified time.
        Defaults to None (no sorting).
    - sort_reverse (bool): If True, sorts in reverse order (descending). Defaults to False.
    - valid_extensions (tuple or None): A tuple of file extensions to include (e.g., ('.mp4', '.jpg')). If None, no filter is applied.

    Returns:
    - list: A list of file names or paths, sorted as per the specified options.

    Example:
    - allfiles("/path/to/folder", scan_subfolders=True, include_path=True, sort_by="name", sort_reverse=True, valid_extensions=('.mp4', '.jpg'))
    """

    # If valid_extensions is None, disable the filter and return all files
    if valid_extensions is None:
        valid_extensions = []

    all_files = []

    # Scan files in subfolders if needed
    if scan_subfolders:
        for root, dirs, files in os.walk(folder):
            for file in files:
                # If valid_extensions is empty, no filtering is applied
                if not valid_extensions or file.endswith(valid_extensions):
                    file_path = os.path.join(root, file) if include_path else file
                    all_files.append(file_path)
    else:
        for file in os.listdir(folder):
            # If valid_extensions is empty, no filtering is applied
            if not valid_extensions or file.endswith(valid_extensions):
                file_path = os.path.join(folder, file) if include_path else file
                all_files.append(file_path)

    # Sorting the files if requested
    if sort_by:
        # Sorting options
        if sort_by == 'name':
            all_files.sort(key=lambda x: [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', x)], reverse=sort_reverse)  # Sort alphabetically (case insensitive)
        elif sort_by == 'size':
            all_files.sort(key=lambda x: os.path.getsize(x), reverse=sort_reverse)  # Sort by file size
        elif sort_by == 'created':
            all_files.sort(key=lambda x: os.path.getctime(x), reverse=sort_reverse)  # Sort by creation time
        elif sort_by == 'modified':
            all_files.sort(key=lambda x: os.path.getmtime(x), reverse=sort_reverse)  # Sort by last modified time

        return all_files

    return all_files

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

    @staticmethod
    def interpolate_color(color1, color2, ratio):
        """
        Interpolates between two RGB colors.
        """
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        return f"{r};{g};{b}"

    @staticmethod
    def format_gradient_text(text, color1, color2, attributes=None):
        formatted_text = ""
        gradient_length = len(text)
        for i in range(gradient_length):
            ratio = i / (gradient_length - 1)
            interpolated_color = TextFormatter.interpolate_color(color1, color2, ratio)
            formatted_text += f"\033[38;2;{interpolated_color}m{text[i]}"
        formatted_text += TextFormatter.RESET

        if attributes:
            formatted_text = f"{TextFormatter.TEXT_ATTRIBUTES[attributes]}{formatted_text}"

        return formatted_text

def SRTParser(file_path, removeln=True):
    def parse_srt_time(time_str):
        """Convert SRT time format to seconds."""
        hours, minutes, seconds_millis = time_str.split(':')
        seconds, millis = seconds_millis.split(',')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000
        return total_seconds

    """Parse an SRT file and return a list of subtitle entries."""
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()

    # Split content by double newlines to get subtitle blocks
    blocks = content.strip().split('\n\n')

    subtitles = []

    for i, block in enumerate(blocks):
        lines = block.split('\n')

        # The first line is the index
        index = int(lines[0].strip())

        # The second line is the time range
        time_range = lines[1].strip()
        start_time_str, end_time_str = time_range.split(' --> ')
        start_time = parse_srt_time(start_time_str.strip())
        end_time = parse_srt_time(end_time_str.strip())

        # Calculate duration in seconds
        duration = end_time - start_time

        # The rest is the subtitle text
        if removeln:
            text = ' '.join(line.strip() for line in lines[2:])
        else:
            text = '\n'.join(line.strip() for line in lines[2:])

        # Calculate next text duration in seconds
        if i < len(blocks) - 1:
            next_start_time_str = blocks[i + 1].split('\n')[1].split(' --> ')[0].strip()
            next_start_time = parse_srt_time(next_start_time_str)
            next_text_duration = next_start_time - end_time
        else:
            next_text_duration = None

        subtitles.append({
            'index': index,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'text': text,
            'next_text_duration': next_text_duration
        })

    return subtitles