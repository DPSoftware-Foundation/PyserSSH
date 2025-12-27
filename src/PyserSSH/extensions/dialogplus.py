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

from ..interactive import Clear, Send, wait_inputkey
from .moredisplay import alternate

import re
from abc import ABC, abstractmethod
from typing import Optional, List


class Widget(ABC):
    """Base class for all widgets"""

    def __init__(self, x: int = 0, y: int = 0, width: int = None, height: int = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.focused = False
        self.visible = True

    @abstractmethod
    def render(self, window) -> List[str]:
        """Render the widget and return list of lines"""
        pass

    @abstractmethod
    def handle_input(self, key: bytes) -> bool:
        """Handle input. Return True if key was consumed"""
        pass

    def set_focus(self, focused: bool):
        """Set widget focus state"""
        self.focused = focused

    def set_visible(self, visible: bool):
        """Set widget visibility"""
        self.visible = visible


class TextWidget(Widget):
    """Widget for displaying static text"""

    def __init__(self, text: str = "", align: str = "left", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.align = align  # left, center, right

    def render(self, window) -> List[str]:
        if not self.visible:
            return []

        lines = self.text.split('\n')
        rendered_lines = []

        for line in lines:
            if self.align == "center":
                rendered_lines.append(line.center(self.width or len(line)))
            elif self.align == "right":
                rendered_lines.append(line.rjust(self.width or len(line)))
            else:
                rendered_lines.append(line.ljust(self.width or len(line)))

        return rendered_lines

    def handle_input(self, key: bytes) -> bool:
        return False  # Text widgets don't handle input

    def set_text(self, text: str):
        """Update the text content"""
        self.text = text


class MenuWidget(Widget):
    """Widget for displaying a selectable menu"""

    def __init__(self, items: List[str], selected_index: int = 0,
                 selection_prefix: str = "> ", **kwargs):
        super().__init__(**kwargs)
        self.items = items
        self.selected_index = selected_index
        self.selection_prefix = selection_prefix
        self.selected = False
        self.cancelled = False

    def render(self, window) -> List[str]:
        if not self.visible:
            return []

        rendered_lines = []
        for i, item in enumerate(self.items):
            if i == self.selected_index and self.focused:
                rendered_lines.append(f"{self.selection_prefix}{item}")
            else:
                rendered_lines.append(f"{' ' * len(self.selection_prefix)}{item}")

        return rendered_lines

    def handle_input(self, key: bytes) -> bool:
        if not self.focused:
            return False

        if key == b'\x1b[A':  # Up arrow
            self.selected_index = max(0, self.selected_index - 1)
            return True
        elif key == b'\x1b[B':  # Down arrow
            self.selected_index = min(len(self.items) - 1, self.selected_index + 1)
            return True
        elif key == b'\r':  # Enter
            self.selected = True
            return True
        elif key == b'c':  # Cancel
            self.cancelled = True
            return True

        return False

    def get_selected_item(self) -> Optional[str]:
        """Get the currently selected item"""
        if self.selected and 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def get_selected_index(self) -> Optional[int]:
        """Get the currently selected index"""
        if self.selected:
            return self.selected_index
        return None if self.cancelled else None


class TextInputWidget(Widget):
    """Widget for text input"""

    def __init__(self, placeholder: str = "", password: bool = False,
                 max_length: int = None, **kwargs):
        super().__init__(**kwargs)
        self.placeholder = placeholder
        self.password = password
        self.max_length = max_length
        self.buffer = bytearray()
        self.cursor_position = 0
        self.completed = False
        self.cancelled = False

    def render(self, window) -> List[str]:
        if not self.visible:
            return []

        if self.buffer:
            if self.password:
                display_text = "*" * len(self.buffer.decode('utf-8'))
            else:
                display_text = self.buffer.decode('utf-8')
        else:
            display_text = self.placeholder if not self.focused else ""

        prefix = "> " if self.focused else "  "
        rendered_line = f"{prefix}{display_text}"

        # Add cursor if focused
        if self.focused and not self.password:
            if self.cursor_position <= len(display_text):
                cursor_pos = len(prefix) + self.cursor_position
                if cursor_pos < len(rendered_line):
                    rendered_line = rendered_line[:cursor_pos] + "|" + rendered_line[cursor_pos:]
                else:
                    rendered_line += "|"

        return [rendered_line]

    def handle_input(self, key: bytes) -> bool:
        if not self.focused:
            return False

        if key == b'\r':  # Enter
            self.completed = True
            return True
        elif key == b'\x03':  # Ctrl+C
            self.cancelled = True
            return True
        elif key == b'\x7f' or key == b'\x08':  # Backspace
            if self.cursor_position > 0:
                self.buffer = self.buffer[:self.cursor_position - 1] + self.buffer[self.cursor_position:]
                self.cursor_position -= 1
            return True
        elif key == b'\x1b[C':  # Right arrow
            self.cursor_position = min(len(self.buffer), self.cursor_position + 1)
            return True
        elif key == b'\x1b[D':  # Left arrow
            self.cursor_position = max(0, self.cursor_position - 1)
            return True
        elif bool(re.compile(b'\x1b\[[0-9;]*[mGK]').search(key)):
            return True  # Ignore ANSI escape codes
        else:
            # Regular character input
            if self.max_length is None or len(self.buffer) < self.max_length:
                self.buffer = self.buffer[:self.cursor_position] + key + self.buffer[self.cursor_position:]
                self.cursor_position += 1
            return True

    def get_text(self) -> Optional[str]:
        """Get the input text if completed"""
        if self.completed:
            return self.buffer.decode('utf-8')
        return None if self.cancelled else None

    def set_text(self, text: str):
        """Set the input text"""
        self.buffer = bytearray(text.encode('utf-8'))
        self.cursor_position = len(self.buffer)


class Window:
    """Container for widgets with layout management"""

    def __init__(self, title: str = "", width: int = None, height: int = None,
                 border: bool = True, padding: int = 1):
        self.title = title
        self.width = width
        self.height = height
        self.border = border
        self.padding = padding
        self.widgets: List[Widget] = []
        self.focused_widget_index = -1

    def add_widget(self, widget: Widget, x: int = None, y: int = None) -> Widget:
        """Add a widget to the window"""
        if x is not None:
            widget.x = x
        if y is not None:
            widget.y = y

        self.widgets.append(widget)

        # Focus first focusable widget if none is focused
        if self.focused_widget_index == -1 and self._can_focus(widget):
            self.focused_widget_index = len(self.widgets) - 1
            widget.set_focus(True)

        return widget

    def _can_focus(self, widget: Widget) -> bool:
        """Check if a widget can receive focus"""
        return isinstance(widget, (MenuWidget, TextInputWidget))

    def set_focus(self, widget_index: int):
        """Set focus to a specific widget"""
        if 0 <= widget_index < len(self.widgets):
            # Remove focus from current widget
            if 0 <= self.focused_widget_index < len(self.widgets):
                self.widgets[self.focused_widget_index].set_focus(False)

            # Set focus to new widget
            self.focused_widget_index = widget_index
            self.widgets[widget_index].set_focus(True)

    def next_focus(self):
        """Move focus to next focusable widget"""
        current = self.focused_widget_index
        for i in range(len(self.widgets)):
            next_index = (current + i + 1) % len(self.widgets)
            if self._can_focus(self.widgets[next_index]):
                self.set_focus(next_index)
                break

    def previous_focus(self):
        """Move focus to previous focusable widget"""
        current = self.focused_widget_index
        for i in range(len(self.widgets)):
            prev_index = (current - i - 1) % len(self.widgets)
            if self._can_focus(self.widgets[prev_index]):
                self.set_focus(prev_index)
                break

    def render(self, client) -> List[str]:
        """Render the window and all its widgets"""
        window_width = self.width or client["windowsize"]["width"]
        window_height = self.height or client["windowsize"]["height"]

        # Create empty window content
        content_lines = [""] * (window_height - 3 if self.border else window_height)

        # Render title if present
        title_y = 0
        if self.title and self.border:
            title_line = self.title.center(window_width)
            if title_y < len(content_lines):
                content_lines[title_y] = title_line

            # Add separator
            if title_y + 1 < len(content_lines):
                content_lines[title_y + 1] = "-" * window_width

        # Render widgets
        for widget in self.widgets:
            if not widget.visible:
                continue

            widget_lines = widget.render(self)
            widget_y = widget.y + (2 if self.border and self.title else 0) + self.padding

            for i, line in enumerate(widget_lines):
                line_y = widget_y + i
                if 0 <= line_y < len(content_lines):
                    # Position the line horizontally
                    widget_x = widget.x + self.padding
                    if widget_x >= 0:
                        current_line = content_lines[line_y]
                        # Pad current line if necessary
                        while len(current_line) < widget_x:
                            current_line += " "

                        # Insert widget line
                        new_line = current_line[:widget_x] + line
                        if len(new_line) > window_width - self.padding:
                            new_line = new_line[:window_width - self.padding]

                        content_lines[line_y] = new_line

        # Center content on screen
        screen_width = client["windowsize"]["width"]
        screen_height = client["windowsize"]["height"]

        centered_lines = []
        for line in content_lines:
            centered_line = line.center(screen_width) if line.strip() else " " * screen_width
            centered_lines.append(centered_line)

        return centered_lines

    def handle_input(self, key: bytes) -> bool:
        """Handle input for the focused widget or window navigation"""
        # Tab navigation between widgets
        if key == b'\t':
            self.next_focus()
            return True
        elif key == b'\x1b[Z':  # Shift+Tab
            self.previous_focus()
            return True

        # Let focused widget handle input
        if 0 <= self.focused_widget_index < len(self.widgets):
            return self.widgets[self.focused_widget_index].handle_input(key)

        return False


class Dialog:
    """Main dialog class that manages a window and handles the event loop"""

    def __init__(self, client, window: Window, exit_keys: List[bytes] = None):
        self.client = client
        self.window = window
        self.exit_keys = exit_keys or [b'\x1b']  # Escape key by default
        self.running = False
        self.result = None

        self.is_init = False

    def show(self) -> any:
        """Show the dialog and return the result"""
        self.running = True

        while self.running:
            self._render()
            self._handle_input()

        return self.result

    def _render(self):
        """Render the dialog"""
        if not self.is_init:
            alternate.enter(self.client)

            self.is_init = True
        else:
            alternate.clear(self.client)

        content_lines = self.window.render(self.client)

        for line in content_lines:
            Send(self.client, line)

        # Add help text
        help_text = self._get_help_text()
        if help_text:
            Send(self.client, help_text, ln=False)

    def _get_help_text(self) -> str:
        """Generate help text based on focused widget"""
        if 0 <= self.window.focused_widget_index < len(self.window.widgets):
            widget = self.window.widgets[self.window.focused_widget_index]

            if isinstance(widget, MenuWidget):
                return "Use arrow keys to navigate, Enter to select, 'c' to cancel, Esc to exit"
            elif isinstance(widget, TextInputWidget):
                return "Type to input text, Enter to confirm, Ctrl+C to cancel, Esc to exit"

        return "Press Esc to exit"

    def _handle_input(self):
        """Handle input for the dialog"""
        key = wait_inputkey(self.client, raw=True)

        # Check for exit keys
        if key in self.exit_keys:
            self.running = False
            self.result = None
            return

        # Let window handle the input
        if not self.window.handle_input(key):
            # Check if any widget completed their task
            self._check_widget_completion()

    def _check_widget_completion(self):
        """Check if any widget has completed and set result"""
        for widget in self.window.widgets:
            if isinstance(widget, MenuWidget):
                if widget.selected:
                    self.result = {
                        'type': 'menu_selection',
                        'index': widget.get_selected_index(),
                        'item': widget.get_selected_item()
                    }
                    self.running = False
                    return
                elif widget.cancelled:
                    self.result = None
                    self.running = False
                    return

            elif isinstance(widget, TextInputWidget):
                if widget.completed:
                    self.result = {
                        'type': 'text_input',
                        'text': widget.get_text()
                    }
                    self.running = False
                    return
                elif widget.cancelled:
                    self.result = None
                    self.running = False
                    return

    def close(self, result=None):
        """Close the dialog with optional result"""
        self.running = False
        self.result = result
        alternate.exit(self.client)


# Convenience functions for common dialog types
def show_text_dialog(client, content: str = "", title: str = "", exit_key: bytes = b'\r') -> None:
    """Show a simple text dialog"""
    window = Window(title=title, border=True)
    window.add_widget(TextWidget(text=content), x=0, y=0)

    dialog = Dialog(client, window, exit_keys=[exit_key] if exit_key else [b'\x1b'])
    dialog.show()


def show_menu_dialog(client, items: List[str], title: str = "", description: str = "") -> Optional[dict]:
    """Show a menu dialog and return selection result"""
    window = Window(title=title, border=True)

    if description:
        window.add_widget(TextWidget(text=description), x=0, y=0)
        menu_y = len(description.split('\n')) + 1
    else:
        menu_y = 0

    window.add_widget(MenuWidget(items=items), x=0, y=menu_y)

    dialog = Dialog(client, window)
    return dialog.show()


def show_input_dialog(client, prompt: str = "Enter text:", title: str = "",
                      password: bool = False, max_length: int = None) -> Optional[dict]:
    """Show a text input dialog and return input result"""
    window = Window(title=title, border=True)

    window.add_widget(TextWidget(text=prompt), x=0, y=0)
    window.add_widget(TextInputWidget(password=password, max_length=max_length), x=0, y=2)

    dialog = Dialog(client, window)
    return dialog.show()


def show_complex_dialog(client, title: str = "") -> Window:
    """Create a complex dialog window for custom layouts"""
    return Window(title=title, border=True)


def example_complex_form(client):
    """Example of a complex form with multiple widgets"""
    window = Window(title="User Registration Form", border=True)

    # Add form fields
    window.add_widget(TextWidget(text="Please fill out the registration form:"), x=0, y=0)

    window.add_widget(TextWidget(text="Username:"), x=0, y=2)
    username_input = window.add_widget(TextInputWidget(placeholder="Enter username"), x=0, y=3)

    window.add_widget(TextWidget(text="Password:"), x=0, y=5)
    password_input = window.add_widget(TextInputWidget(password=True, placeholder="Enter password"), x=0, y=6)

    window.add_widget(TextWidget(text="User Type:"), x=0, y=8)
    user_type_menu = window.add_widget(MenuWidget(items=["Regular User", "Administrator", "Guest"]), x=0, y=9)

    # Custom dialog handling
    dialog = Dialog(client, window)
    result = dialog.show()

    if result:
        # Collect all form data
        form_data = {
            'username': username_input.get_text(),
            'password': password_input.get_text(),
            'user_type': user_type_menu.get_selected_item()
        }
        return form_data

    return None