from threading import Thread, Lock, Event

from .processbar import Steps, TextFormatter, Print
from ..system.clientype import Client
from ..interactive import wait_inputkey

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