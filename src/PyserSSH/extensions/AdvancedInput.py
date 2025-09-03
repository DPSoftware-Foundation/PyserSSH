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
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional
from enum import Enum

from ..interactive import wait_inputkey

class MouseButton(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2
    WHEEL_UP = 64
    WHEEL_DOWN = 65
    NONE = -1

class EventType(Enum):
    MOUSE_PRESS = "mouse_press"
    MOUSE_RELEASE = "mouse_release"
    MOUSE_MOVE = "mouse_move"
    MOUSE_DRAG = "mouse_drag"
    MOUSE_WHEEL = "mouse_wheel"
    KEY_PRESS = "key_press"
    UNKNOWN = "unknown"

class SpecialKey(Enum):
    # Arrow keys
    UP = "\033[A"
    DOWN = "\033[B"
    RIGHT = "\033[C"
    LEFT = "\033[D"

    # Function keys
    F1 = "\033[OP"
    F2 = "\033[OQ"
    F3 = "\033[OR"
    F4 = "\033[OS"
    F5 = "\033[15~"
    F6 = "\033[17~"
    F7 = "\033[18~"
    F8 = "\033[19~"
    F9 = "\033[20~"
    F10 = "\033[21~"
    F11 = "\033[23~"
    F12 = "\033[24~"

    # Navigation keys
    HOME = "\033[H"
    END = "\033[F"
    INSERT = "\033[2~"
    DELETE = "\033[3~"
    PAGE_UP = "\033[5~"
    PAGE_DOWN = "\033[6~"

    # Control keys
    TAB = "\t"
    ENTER = "\r"
    ESCAPE = "\033"
    BACKSPACE = "\x7f"

    # Ctrl combinations
    CTRL_A = "\x01"
    CTRL_B = "\x02"
    CTRL_C = "\x03"
    CTRL_D = "\x04"
    CTRL_E = "\x05"
    CTRL_F = "\x06"
    CTRL_G = "\x07"
    CTRL_H = "\x08"
    CTRL_I = "\x09"  # Same as TAB
    CTRL_J = "\x0a"  # Same as newline
    CTRL_K = "\x0b"
    CTRL_L = "\x0c"
    CTRL_M = "\x0d"  # Same as ENTER
    CTRL_N = "\x0e"
    CTRL_O = "\x0f"
    CTRL_P = "\x10"
    CTRL_Q = "\x11"
    CTRL_R = "\x12"
    CTRL_S = "\x13"
    CTRL_T = "\x14"
    CTRL_U = "\x15"
    CTRL_V = "\x16"
    CTRL_W = "\x17"
    CTRL_X = "\x18"
    CTRL_Y = "\x19"
    CTRL_Z = "\x1a"


@dataclass
class InputEvent:
    event_type: EventType
    button: MouseButton = MouseButton.NONE
    x: int = 0
    y: int = 0
    key: str = ""
    special_key: Optional[SpecialKey] = None
    modifiers: dict = None  # Will contain 'ctrl', 'alt', 'shift' flags
    raw_data: bytes = b""
    pressed: bool = False  # For SGR mode: True=press, False=release

    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = {'ctrl': False, 'alt': False, 'shift': False}

        # Try to identify special key
        if self.key and self.special_key is None:
            for special in SpecialKey:
                if special.value == self.key:
                    self.special_key = special
                    break

class AdvancedInput:
    def __init__(self, client, mouse_mode=0):
        """
        mouse_mode
        0: (1000) Simple input [Press/Release,Wheel] events -> Button, X, Y
        1: (1002) More input [Press/Release,Wheel,Drag] events -> Button, X, Y
        2: (1003) Advanced input with mouse movement [Press/Release,Wheel,Drag,Move] events -> Button, X, Y
        3: (1003 + 1006) Advanced input with SGR [Press/Release,Wheel,Drag,Move] events -> Button, UpDown, X, Y, UTF-8
        """
        self.client = client
        self.mouse_mode = mouse_mode
        self.event_handler_function: Optional[Callable[[InputEvent], None]] = None

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._buffer = b""
        self._mouse_pressed = set()  # Track pressed buttons for drag detection

        # Enable mouse reporting based on mode
        if self.mouse_mode in (0, 1, 2, 3):
            self._enable_mouse_reporting()

    def _enable_mouse_reporting(self):
        """Enable appropriate mouse reporting mode"""
        # Enable mouse reporting
        if self.mouse_mode == 0:
            self.client.send("\033[?1000h")  # Basic mouse reporting
        elif self.mouse_mode == 1:
            self.client.send("\033[?1002h")  # Button event tracking
        elif self.mouse_mode == 2:
            self.client.send("\033[?1003h")  # Any event tracking
        elif self.mouse_mode == 3:
            self.client.send("\033[?1003h\033[?1006h")  # SGR mouse mode

        # Enable alternative screen buffer (optional, helps with mouse tracking)
        #self.client.send("\033[?47h")

    def _disable_mouse_reporting(self):
        """Disable mouse reporting"""
        if self.mouse_mode == 0:
            self.client.send("\033[?1000l")
        elif self.mouse_mode == 1:
            self.client.send("\033[?1002l")
        elif self.mouse_mode == 2:
            self.client.send("\033[?1003l")
        elif self.mouse_mode == 3:
            self.client.send("\033[?1003l\033[?1006l")

        # Disable alternative screen buffer
        #self.client.send("\033[?47l")

    def _parse_standard_mouse(self, data: bytes) -> Optional[InputEvent]:
        """Parse standard mouse sequences (\033[M + 3 bytes)"""
        if len(data) < 6 or not data.startswith(b'\033[M'):
            return None

        try:
            cb = data[3] - 32  # Button and modifier info
            cx = data[4] - 33  # X coordinate (1-based, convert to 0-based)
            cy = data[5] - 33  # Y coordinate (1-based, convert to 0-based)

            button_code = cb & 3
            drag = cb & 32
            wheel = cb & 64
            release = cb & 3 == 3

            if wheel:
                button = MouseButton.WHEEL_UP if cb & 1 == 0 else MouseButton.WHEEL_DOWN
                event_type = EventType.MOUSE_WHEEL
            elif release:
                button = MouseButton.NONE
                event_type = EventType.MOUSE_RELEASE
                # Remove from pressed set
                self._mouse_pressed.discard(button_code)
            elif drag and button_code in self._mouse_pressed:
                button = MouseButton(button_code)
                event_type = EventType.MOUSE_DRAG
            else:
                button = MouseButton(button_code)
                if drag or (self.mouse_mode >= 2 and button_code not in self._mouse_pressed):
                    if button_code == 3:  # Movement without button
                        event_type = EventType.MOUSE_MOVE
                        button = MouseButton.NONE
                    else:
                        event_type = EventType.MOUSE_MOVE if drag else EventType.MOUSE_PRESS
                        if event_type == EventType.MOUSE_PRESS:
                            self._mouse_pressed.add(button_code)
                else:
                    event_type = EventType.MOUSE_PRESS
                    self._mouse_pressed.add(button_code)

            return InputEvent(
                event_type=event_type,
                button=button,
                x=cx,
                y=cy,
                raw_data=data[:6]
            )

        except (IndexError, ValueError):
            return None

    def _parse_sgr_mouse(self, data: bytes) -> Optional[InputEvent]:
        try:
            data_str = data.decode('utf-8')
            if not data_str.startswith('\033[<'):
                return None

            end_char = data_str[-1]
            if end_char not in 'Mm':
                return None

            params = data_str[3:-1].split(';')
            if len(params) < 3:
                return None

            button_code = int(params[0])
            x = int(params[1]) - 1
            y = int(params[2]) - 1

            base_button = button_code & 3
            pressed = end_char == 'M'

            if button_code >= 64:
                button = MouseButton.WHEEL_UP if button_code == 64 else MouseButton.WHEEL_DOWN
                event_type = EventType.MOUSE_WHEEL
            else:
                if base_button == 3:
                    button = MouseButton.NONE
                else:
                    button = MouseButton(base_button)

                if pressed:
                    if button_code & 32:  # Drag
                        event_type = EventType.MOUSE_DRAG
                        pressed = base_button in self._mouse_pressed
                    else:
                        event_type = EventType.MOUSE_PRESS
                        self._mouse_pressed.add(base_button)
                        pressed = True
                else:
                    event_type = EventType.MOUSE_RELEASE
                    self._mouse_pressed.discard(base_button)
                    pressed = False

            return InputEvent(
                event_type=event_type,
                button=button,
                x=x,
                y=y,
                pressed=pressed,
                raw_data=data
            )

        except (ValueError, IndexError, UnicodeDecodeError):
            return None

    def _parse_keyboard_modifiers(self, key: str) -> dict:
        """Parse keyboard modifiers from escape sequences"""
        modifiers = {'ctrl': False, 'alt': False, 'shift': False}

        # Check for Alt (ESC prefix in some terminals)
        if key.startswith('\033') and len(key) > 1:
            # Simple Alt detection - more complex parsing could be added
            if key.startswith('\033[1;'):
                # Format: \033[1;modifiercode~
                try:
                    parts = key[4:].split(';')
                    if len(parts) >= 1:
                        mod_code = int(parts[0])
                        modifiers['shift'] = bool(mod_code & 1)
                        modifiers['alt'] = bool(mod_code & 2)
                        modifiers['ctrl'] = bool(mod_code & 4)
                except (ValueError, IndexError):
                    pass

        # Check for Ctrl sequences (0x01-0x1A)
        elif len(key) == 1 and 1 <= ord(key) <= 26:
            modifiers['ctrl'] = True

        return modifiers

    def _parse_input(self, data: bytes) -> Optional[InputEvent]:
        """Parse input data and return appropriate event"""
        if not data:
            return None

        # Try to parse as mouse input first
        if data.startswith(b'\033[M') and len(data) >= 6:
            # Standard mouse mode
            return self._parse_standard_mouse(data)
        elif data.startswith(b'\033[<') and self.mouse_mode == 3:
            # SGR mouse mode
            return self._parse_sgr_mouse(data)
        elif data.startswith(b'\033['):
            # Other escape sequences (arrow keys, function keys, etc.)
            try:
                key_str = data.decode('utf-8')
                modifiers = self._parse_keyboard_modifiers(key_str)
                return InputEvent(
                    event_type=EventType.KEY_PRESS,
                    key=key_str,
                    modifiers=modifiers,
                    raw_data=data
                )
            except UnicodeDecodeError:
                pass
        else:
            # Regular key press
            try:
                key_str = data.decode('utf-8')
                modifiers = self._parse_keyboard_modifiers(key_str)
                return InputEvent(
                    event_type=EventType.KEY_PRESS,
                    key=key_str,
                    modifiers=modifiers,
                    raw_data=data
                )
            except UnicodeDecodeError:
                pass

        # Unknown input
        return InputEvent(
            event_type=EventType.UNKNOWN,
            raw_data=data
        )

    def _find_complete_sequence(self, buffer: bytes) -> tuple[Optional[bytes], bytes]:
        """Find and extract complete input sequences from buffer"""
        if not buffer:
            return None, buffer

        # Check for mouse sequences
        if buffer.startswith(b'\033[M') and len(buffer) >= 6:
            return buffer[:6], buffer[6:]

        if buffer.startswith(b'\033[<'):
            # Look for SGR mouse sequence end
            for i, byte in enumerate(buffer):
                if byte in (ord('M'), ord('m')):
                    return buffer[:i + 1], buffer[i + 1:]

        if buffer.startswith(b'\033['):
            # Look for other escape sequences
            for i in range(2, min(len(buffer), 10)):
                if 64 <= buffer[i] <= 126:  # Final character range
                    return buffer[:i + 1], buffer[i + 1:]

        # Single character or unknown sequence
        if buffer[0] < 128 or buffer.startswith(b'\033'):
            return buffer[:1], buffer[1:]

        # UTF-8 sequence
        try:
            char = buffer.decode('utf-8')[0]
            char_bytes = char.encode('utf-8')
            return char_bytes, buffer[len(char_bytes):]
        except UnicodeDecodeError:
            return buffer[:1], buffer[1:]

    def tick(self) -> bool:
        """Process one tick of input. Returns True if an event was processed."""
        try:
            # Get input with short timeout for non-blocking operation
            raw_input = wait_inputkey(self.client, maxlen=50, timeout=0.01)
            if raw_input:
                self._buffer += raw_input

            # Process complete sequences in buffer
            sequence, self._buffer = self._find_complete_sequence(self._buffer)
            if sequence:
                event = self._parse_input(sequence)
                if event and self.event_handler_function:
                    self.event_handler_function(event)
                    return True

            return False
        except Exception:
            return False

    def _input_thread(self):
        """Main input processing thread"""
        while self._running:
            try:
                if not self.tick():
                    time.sleep(0.001)  # Small delay if no input
            except Exception:
                if self._running:  # Only continue if we're supposed to be running
                    time.sleep(0.01)

    def start_receive(self):
        """Start receiving input in a separate thread"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._input_thread, daemon=True)
        self._thread.start()

    def stop_receive(self):
        """Stop receiving input and clean up"""
        if not self._running:
            return

        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        self._disable_mouse_reporting()
        self._thread = None

    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, '_running') and self._running:
            self.stop_receive()