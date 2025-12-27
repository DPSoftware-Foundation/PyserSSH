"""
STGL - Simple Terminal Graphics Library

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
import math
from typing import Tuple

from .moredisplay import alternate

class Color:
    """Color utilities supporting both ANSI and 24-bit RGB colors"""

    # ANSI color constants (for compatibility)
    BLACK = '30'
    RED = '31'
    GREEN = '32'
    YELLOW = '33'
    BLUE = '34'
    MAGENTA = '35'
    CYAN = '36'
    WHITE = '37'
    BRIGHT_BLACK = '90'
    BRIGHT_RED = '91'
    BRIGHT_GREEN = '92'
    BRIGHT_YELLOW = '93'
    BRIGHT_BLUE = '94'
    BRIGHT_MAGENTA = '95'
    BRIGHT_CYAN = '96'
    BRIGHT_WHITE = '97'

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """Create 24-bit RGB color code (0-255 for each component)"""
        return f"38;2;{r};{g};{b}"

    @staticmethod
    def rgb_bg(r: int, g: int, b: int) -> str:
        """Create 24-bit RGB background color code"""
        return f"48;2;{r};{g};{b}"

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color (#RRGGBB) to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            # Short format #RGB -> #RRGGBB
            hex_color = ''.join([c * 2 for c in hex_color])
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def hex(hex_color: str) -> str:
        """Create 24-bit color from hex string (#RRGGBB or #RGB)"""
        r, g, b = Color.hex_to_rgb(hex_color)
        return Color.rgb(r, g, b)

    @staticmethod
    def hsl(h: float, s: float, l: float) -> str:
        """Create RGB color from HSL values (H: 0-360, S: 0-1, L: 0-1)"""

        def hsl_to_rgb(h, s, l):
            h = h / 360.0
            c = (1 - abs(2 * l - 1)) * s
            x = c * (1 - abs((h * 6) % 2 - 1))
            m = l - c / 2

            if 0 <= h < 1 / 6:
                r, g, b = c, x, 0
            elif 1 / 6 <= h < 1 / 3:
                r, g, b = x, c, 0
            elif 1 / 3 <= h < 1 / 2:
                r, g, b = 0, c, x
            elif 1 / 2 <= h < 2 / 3:
                r, g, b = 0, x, c
            elif 2 / 3 <= h < 5 / 6:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x

            return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

        r, g, b = hsl_to_rgb(h, s, l)
        return Color.rgb(r, g, b)

    # Predefined RGB colors (pygame-compatible)
    @staticmethod
    def get_preset_colors():
        return {
            'black': Color.rgb(0, 0, 0),
            'white': Color.rgb(255, 255, 255),
            'red': Color.rgb(255, 0, 0),
            'green': Color.rgb(0, 255, 0),
            'blue': Color.rgb(0, 0, 255),
            'yellow': Color.rgb(255, 255, 0),
            'magenta': Color.rgb(255, 0, 255),
            'cyan': Color.rgb(0, 255, 255),
            'orange': Color.rgb(255, 165, 0),
            'purple': Color.rgb(128, 0, 128),
            'pink': Color.rgb(255, 192, 203),
            'lime': Color.rgb(50, 205, 50),
            'navy': Color.rgb(0, 0, 128),
            'maroon': Color.rgb(128, 0, 0),
            'olive': Color.rgb(128, 128, 0),
            'teal': Color.rgb(0, 128, 128),
            'silver': Color.rgb(192, 192, 192),
            'gray': Color.rgb(128, 128, 128),
        }


class Surface:
    """Terminal surface for drawing operations"""

    def __init__(self, width: int = None, height: int = None):
        if width is None or height is None:
            self.width = 80
            self.height = 24
        else:
            self.width = width
            self.height = height

        # Initialize canvas
        self.canvas = [[{'char': ' ', 'fg': Color.rgb(255, 255, 255), 'bg': None}
                        for _ in range(self.width)]
                       for _ in range(self.height)]
        self.current_color = Color.rgb(255, 255, 255)
        self.current_char = '█'

    def get_size(self) -> Tuple[int, int]:
        """Get surface dimensions"""
        return (self.width, self.height)

    def set_at(self, pos: Tuple[int, int], color: str = None, char: str = None):
        """Set pixel at position - similar to pygame Surface.set_at()"""
        x, y = pos
        if 0 <= x < self.width and 0 <= y < self.height:
            if color:
                self.canvas[y][x]['fg'] = color
            if char:
                self.canvas[y][x]['char'] = char
            return True
        return False

    def get_at(self, pos: Tuple[int, int]) -> dict:
        """Get pixel data at position"""
        x, y = pos
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.canvas[y][x].copy()
        return {'char': ' ', 'fg': Color.rgb(255, 255, 255), 'bg': None}

    def fill(self, color: str = None, char: str = ' '):
        """Fill entire surface with color/character"""
        if color is None:
            color = Color.rgb(0, 0, 0)  # Default to black
        for y in range(self.height):
            for x in range(self.width):
                self.canvas[y][x] = {'char': char, 'fg': color, 'bg': None}

    def blit(self, source: 'Surface', dest: Tuple[int, int]):
        """Copy another surface to this surface at dest position"""
        dest_x, dest_y = dest
        src_width, src_height = source.get_size()

        for y in range(src_height):
            for x in range(src_width):
                target_x = dest_x + x
                target_y = dest_y + y
                if 0 <= target_x < self.width and 0 <= target_y < self.height:
                    self.canvas[target_y][target_x] = source.canvas[y][x].copy()

    # Basic drawing functions
    def draw_pixel(self, pos: Tuple[int, int], color: str = None, char: str = None):
        """Draw a single pixel"""
        color = color or self.current_color
        char = char or self.current_char
        self.set_at(pos, color, char)

    def draw_line(self, color: str, start: Tuple[int, int], end: Tuple[int, int], char: str = None):
        """Draw a line using Bresenham's algorithm"""
        char = char or self.current_char
        x1, y1 = start
        x2, y2 = end

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while True:
            self.set_at((x, y), color, char)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def draw_rect(self, color: str, rect: Tuple[int, int, int, int], width: int = 0, char: str = None):
        """Draw rectangle. width=0 fills the rectangle"""
        char = char or self.current_char
        x, y, w, h = rect

        if width == 0:  # Fill rectangle
            for py in range(y, y + h):
                for px in range(x, x + w):
                    self.set_at((px, py), color, char)
        else:  # Draw outline
            # Top and bottom lines
            for px in range(x, x + w):
                self.set_at((px, y), color, char)
                if h > 1:
                    self.set_at((px, y + h - 1), color, char)
            # Left and right lines
            for py in range(y, y + h):
                self.set_at((x, py), color, char)
                if w > 1:
                    self.set_at((x + w - 1, py), color, char)

    def draw_circle(self, color: str, center: Tuple[int, int], radius: int, width: int = 0, char: str = None):
        """Draw circle using midpoint algorithm"""
        char = char or self.current_char
        cx, cy = center

        if width == 0:  # Fill circle
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        self.set_at((cx + dx, cy + dy), color, char)
        else:  # Draw outline
            x = 0
            y = radius
            d = 3 - 2 * radius

            def draw_circle_points(cx, cy, x, y):
                points = [
                    (cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y), (cx - x, cy - y),
                    (cx + y, cy + x), (cx - y, cy + x), (cx + y, cy - x), (cx - y, cy - x)
                ]
                for px, py in points:
                    self.set_at((px, py), color, char)

            draw_circle_points(cx, cy, x, y)
            while y >= x:
                x += 1
                if d > 0:
                    y -= 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6
                draw_circle_points(cx, cy, x, y)

    def draw_triangle(self, color: str, points: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]],
                      width: int = 0, char: str = None):
        """Draw triangle given three points. width=0 fills the triangle"""
        char = char or self.current_char
        p1, p2, p3 = points

        if width == 0:  # Fill triangle using scanline algorithm
            # Sort points by y-coordinate
            points_sorted = sorted([p1, p2, p3], key=lambda p: p[1])
            x1, y1 = points_sorted[0]
            x2, y2 = points_sorted[1]
            x3, y3 = points_sorted[2]

            def interpolate_x(y, p1, p2):
                """Interpolate x coordinate for given y on line between p1 and p2"""
                if p2[1] == p1[1]:  # Horizontal line
                    return p1[0]
                return p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])

            # Fill triangle using horizontal scanlines
            for y in range(y1, y3 + 1):
                if y <= y2:  # Upper part of triangle
                    x_left = interpolate_x(y, (x1, y1), (x3, y3))
                    x_right = interpolate_x(y, (x1, y1), (x2, y2))
                else:  # Lower part of triangle
                    x_left = interpolate_x(y, (x1, y1), (x3, y3))
                    x_right = interpolate_x(y, (x2, y2), (x3, y3))

                # Ensure left is actually left
                if x_left > x_right:
                    x_left, x_right = x_right, x_left

                # Draw horizontal line
                for x in range(int(x_left), int(x_right) + 1):
                    self.set_at((x, y), color, char)
        else:  # Draw outline
            self.draw_line(color, p1, p2, char)
            self.draw_line(color, p2, p3, char)
            self.draw_line(color, p3, p1, char)

    def draw_polygon(self, color: str, points: list, width: int = 0, char: str = None):
        """Draw polygon from list of points. width=0 fills the polygon"""
        char = char or self.current_char
        if len(points) < 3:
            return

        if width == 0:  # Fill polygon using scanline algorithm
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)

            for y in range(min_y, max_y + 1):
                intersections = []

                # Find intersections with polygon edges
                for i in range(len(points)):
                    p1 = points[i]
                    p2 = points[(i + 1) % len(points)]

                    if p1[1] != p2[1]:  # Not horizontal line
                        if min(p1[1], p2[1]) <= y < max(p1[1], p2[1]):
                            x = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                            intersections.append(x)

                intersections.sort()

                # Fill between pairs of intersections
                for i in range(0, len(intersections), 2):
                    if i + 1 < len(intersections):
                        x_start = int(intersections[i])
                        x_end = int(intersections[i + 1])
                        for x in range(x_start, x_end + 1):
                            self.set_at((x, y), color, char)
        else:  # Draw outline
            for i in range(len(points)):
                p1 = points[i]
                p2 = points[(i + 1) % len(points)]
                self.draw_line(color, p1, p2, char)

    def draw_ellipse(self, color: str, rect: Tuple[int, int, int, int], width: int = 0, char: str = None):
        """Draw ellipse within bounding rectangle"""
        char = char or self.current_char
        x, y, w, h = rect
        cx = x + w // 2
        cy = y + h // 2
        rx = w // 2
        ry = h // 2

        if width == 0:  # Fill ellipse
            for dy in range(-ry, ry + 1):
                for dx in range(-rx, rx + 1):
                    # Check if point is inside ellipse
                    if rx != 0 and ry != 0:
                        if (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1:
                            self.set_at((cx + dx, cy + dy), color, char)
        else:  # Draw outline using parametric equation
            steps = max(w, h) * 2
            for i in range(steps):
                angle = 2 * math.pi * i / steps
                px = int(cx + rx * math.cos(angle))
                py = int(cy + ry * math.sin(angle))
                self.set_at((px, py), color, char)

    def draw_arc(self, color: str, center: Tuple[int, int], radius: int,
                 start_angle: float, end_angle: float, char: str = None):
        """Draw arc from start_angle to end_angle (in radians)"""
        char = char or self.current_char

        cx, cy = center
        steps = int(abs(end_angle - start_angle) * radius)
        if steps == 0:
            steps = 1

        angle_step = (end_angle - start_angle) / steps

        for i in range(steps + 1):
            angle = start_angle + i * angle_step
            x = int(cx + radius * math.cos(angle))
            y = int(cy + radius * math.sin(angle))
            self.set_at((x, y), color, char)

    def draw_bezier(self, color: str, points: list, segments: int = 100, char: str = None):
        """Draw Bezier curve through control points"""
        char = char or self.current_char
        if len(points) < 2:
            return

        def bezier_point(t, control_points):
            """Calculate point on Bezier curve at parameter t (0-1)"""
            n = len(control_points) - 1
            x, y = 0, 0

            # Binomial coefficient calculation
            def binomial(n, k):
                if k > n - k:
                    k = n - k
                result = 1
                for i in range(k):
                    result = result * (n - i) // (i + 1)
                return result

            for i, (px, py) in enumerate(control_points):
                coeff = binomial(n, i) * (t ** i) * ((1 - t) ** (n - i))
                x += coeff * px
                y += coeff * py

            return int(x), int(y)

        prev_point = bezier_point(0, points)
        for i in range(1, segments + 1):
            t = i / segments
            curr_point = bezier_point(t, points)
            self.draw_line(color, prev_point, curr_point, char)
            prev_point = curr_point

    def draw_gradient_rect(self, rect: Tuple[int, int, int, int],
                           start_color: str, end_color: str,
                           horizontal: bool = True, char: str = None):
        """Draw rectangle with gradient fill"""
        char = char or self.current_char
        x, y, w, h = rect

        # Simple gradient by interpolating between colors
        # Note: This is a basic implementation - you might want to enhance
        # color interpolation based on your Color class capabilities

        if horizontal:
            for px in range(x, x + w):
                progress = (px - x) / (w - 1) if w > 1 else 0
                # Use start_color for now - you'd interpolate based on your Color class
                color = start_color if progress < 0.5 else end_color
                for py in range(y, y + h):
                    self.set_at((px, py), color, char)
        else:  # Vertical gradient
            for py in range(y, y + h):
                progress = (py - y) / (h - 1) if h > 1 else 0
                color = start_color if progress < 0.5 else end_color
                for px in range(x, x + w):
                    self.set_at((px, py), color, char)

    def draw_text(self, text: str, pos: Tuple[int, int], color: str = None):
        """Draw text at position"""
        if color is None:
            color = Color.rgb(255, 255, 255)
        x, y = pos
        for i, char in enumerate(text):
            if x + i < self.width and y < self.height:
                self.set_at((x + i, y), color, char)

    def draw_text_multiline(self, text: str, pos: Tuple[int, int], color: str = None, line_spacing: int = 1):
        """Draw multiline text"""
        if color is None:
            color = Color.rgb(255, 255, 255)
        x, y = pos
        lines = text.split('\n')
        for i, line in enumerate(lines):
            self.draw_text(line, (x, y + i * line_spacing), color)

    def draw_box_border(self, rect: Tuple[int, int, int, int], color: str,
                        border_chars: dict = None, char: str = None):
        """Draw decorative box border with custom characters"""
        if border_chars is None:
            border_chars = {
                'top_left': '┌', 'top_right': '┐',
                'bottom_left': '└', 'bottom_right': '┘',
                'horizontal': '─', 'vertical': '│'
            }

        x, y, w, h = rect

        # Corners
        self.set_at((x, y), color, border_chars['top_left'])
        self.set_at((x + w - 1, y), color, border_chars['top_right'])
        self.set_at((x, y + h - 1), color, border_chars['bottom_left'])
        self.set_at((x + w - 1, y + h - 1), color, border_chars['bottom_right'])

        # Horizontal lines
        for px in range(x + 1, x + w - 1):
            self.set_at((px, y), color, border_chars['horizontal'])
            self.set_at((px, y + h - 1), color, border_chars['horizontal'])

        # Vertical lines
        for py in range(y + 1, y + h - 1):
            self.set_at((x, py), color, border_chars['vertical'])
            self.set_at((x + w - 1, py), color, border_chars['vertical'])

    def draw_3d_box(self, color: str, pos: Tuple[int, int], width: int, height: int, depth: int,
                    face_chars: dict = None, outline_only: bool = False):
        """Draw 3D box using isometric projection"""
        if face_chars is None:
            face_chars = {
                'front': '█',
                'top': '▓',
                'right': '▒'
            }

        x, y = pos

        # Calculate isometric offsets (30-degree angles approximated)
        # For terminal chars, we use simpler ratios for better appearance
        depth_x_offset = depth // 2
        depth_y_offset = depth // 3

        # Define the 8 corners of the 3D box
        # Front face (bottom-left, bottom-right, top-left, top-right)
        front_bl = (x, y + height)
        front_br = (x + width, y + height)
        front_tl = (x, y)
        front_tr = (x + width, y)

        # Back face (offset by depth)
        back_bl = (x + depth_x_offset, y + height - depth_y_offset)
        back_br = (x + width + depth_x_offset, y + height - depth_y_offset)
        back_tl = (x + depth_x_offset, y - depth_y_offset)
        back_tr = (x + width + depth_x_offset, y - depth_y_offset)

        if outline_only:
            # Draw wireframe edges
            # Front face edges
            self.draw_line(color, front_tl, front_tr)
            self.draw_line(color, front_tr, front_br)
            self.draw_line(color, front_br, front_bl)
            self.draw_line(color, front_bl, front_tl)

            # Back face edges
            self.draw_line(color, back_tl, back_tr)
            self.draw_line(color, back_tr, back_br)
            self.draw_line(color, back_br, back_bl)
            self.draw_line(color, back_bl, back_tl)

            # Connecting edges
            self.draw_line(color, front_tl, back_tl)
            self.draw_line(color, front_tr, back_tr)
            self.draw_line(color, front_bl, back_bl)
            self.draw_line(color, front_br, back_br)
        else:
            # Draw filled faces (back to front for proper depth)

            # 1. Draw top face (parallelogram)
            top_points = [back_tl, back_tr, front_tr, front_tl]
            self.draw_polygon(color, top_points, 0, face_chars['top'])

            # 2. Draw right face (parallelogram)
            right_points = [front_tr, back_tr, back_br, front_br]
            self.draw_polygon(color, right_points, 0, face_chars['right'])

            # 3. Draw front face (rectangle) - drawn last so it's on top
            front_points = [front_tl, front_tr, front_br, front_bl]
            self.draw_polygon(color, front_points, 0, face_chars['front'])

    def draw_3d_cube(self, color: str, pos: Tuple[int, int], size: int,
                     face_chars: dict = None, outline_only: bool = False):
        """Draw 3D cube (equal width, height, depth)"""
        self.draw_3d_box(color, pos, size, size, size, face_chars, outline_only)

    def draw_isometric_grid(self, color: str, origin: Tuple[int, int],
                            grid_size: int, cell_size: int, char: str = None):
        """Draw isometric grid for 3D drawing reference"""
        char = char or '·'
        ox, oy = origin

        # Draw grid points in isometric pattern
        for row in range(grid_size):
            for col in range(grid_size):
                # Calculate isometric position
                x = ox + col * cell_size + row * (cell_size // 2)
                y = oy + row * (cell_size // 3)
                self.set_at((x, y), color, char)

                # Draw connecting lines for grid
                if col > 0:  # Horizontal line to left
                    prev_x = ox + (col - 1) * cell_size + row * (cell_size // 2)
                    self.draw_line(color, (prev_x, y), (x, y), char)

                if row > 0:  # Diagonal line to previous row
                    prev_y = oy + (row - 1) * (cell_size // 3)
                    prev_x2 = ox + col * cell_size + (row - 1) * (cell_size // 2)
                    self.draw_line(color, (prev_x2, prev_y), (x, y), char)

    def draw_3d_pyramid(self, color: str, base_pos: Tuple[int, int],
                        base_size: int, height: int, char: str = None):
        """Draw 3D pyramid with square base"""
        char = char or '█'
        x, y = base_pos

        # Base corners
        base_tl = (x, y)
        base_tr = (x + base_size, y)
        base_bl = (x, y + base_size)
        base_br = (x + base_size, y + base_size)

        # Apex (center top)
        apex = (x + base_size // 2, y - height)

        # Draw faces (back to front for depth)
        # Back face
        back_face = [base_tl, apex, base_tr]
        self.draw_triangle(color, back_face, 0, '▒')

        # Right face
        right_face = [base_tr, apex, base_br]
        self.draw_triangle(color, right_face, 0, '▓')

        # Front faces
        front_left = [base_bl, apex, base_tl]
        self.draw_triangle(color, front_left, 0, char)

        front_right = [base_br, apex, base_bl]
        self.draw_triangle(color, front_right, 0, char)

    def draw_3d_cylinder(self, color: str, pos: Tuple[int, int], radius: int, height: int,
                         segments: int = 16, char: str = None):
        """Draw 3D cylinder using isometric projection"""
        char = char or '█'

        x, y = pos

        # Draw bottom ellipse (base)
        self.draw_ellipse(color, (x - radius, y + height - radius // 2,
                                  radius * 2, radius), 0, '▒')

        # Draw top ellipse
        self.draw_ellipse(color, (x - radius, y - radius // 2,
                                  radius * 2, radius), 0, '▓')

        # Draw vertical sides
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            edge_x = int(x + radius * math.cos(angle))

            # Only draw front-facing edges
            if math.cos(angle) >= 0:  # Front hemisphere
                self.draw_line(color, (edge_x, y), (edge_x, y + height), char)

    def clear(self, color: str = None):
        """Clear surface (alias for fill with default background)"""
        self.fill(color or Color.rgb(0, 0, 0), ' ')

    def copy(self) -> 'Surface':
        """Create a copy of this surface"""
        new_surface = Surface(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                new_surface.canvas[y][x] = self.canvas[y][x].copy()
        new_surface.current_color = self.current_color
        new_surface.current_char = self.current_char
        return new_surface

class TerminalGraphics:
    """Main graphics class with pygame-like API"""

    def __init__(self, client):
        self.client = client

        self.screen = None
        self.current_color = Color.rgb(255, 255, 255)
        self.current_char = '█'

    def init(self):
        """Initialize graphics system"""
        # Clear screen and hide cursor
        alternate.enter(self.client)
        self.client.send('\033[?25l')
        return True

    def exit(self):
        """Clean up graphics system"""
        # Show cursor and reset
        self.client.send('\033[?25h')
        alternate.exit(self.client)

    def set_mode(self, size: Tuple[int, int] = None) -> Surface:
        """Set display mode and return screen surface"""
        if size:
            self.screen = Surface(size[0], size[1])
        else:
            self.screen = Surface(*self.client.get_terminal_size())
        return self.screen

    def get_surface(self) -> Surface:
        """Get current screen surface"""
        return self.screen

    def render(self, line_render: bool = True, auto_resize: bool = True, raw_output: bool = False):
        """Update entire display"""
        if not self.screen:
            return

        # Option 1: Auto-resize screen to match current terminal size
        if auto_resize:
            current_size = self.client.get_terminal_size()
            if current_size != (self.screen.width, self.screen.height):
                # Create new screen with current terminal size
                old_screen = self.screen
                self.screen = Surface(current_size[0], current_size[1])
                # Optionally copy content from old screen
                self.screen.blit(old_screen, (0, 0))

        # Option 2: Just get current terminal size for bounds checking
        terminal_width, terminal_height = self.client.get_terminal_size()
        render_width = min(self.screen.width, terminal_width)
        render_height = min(self.screen.height, terminal_height)

        buffer = []

        # Move to top-left
        if not raw_output:
            self.client.send('\033[H')

        for y in range(render_height):
            for x in range(render_width):
                cell = self.screen.canvas[y][x]
                color_code = f"\033[{cell['fg']}m" if cell['fg'] else ""
                reset_code = "\033[0m" if cell['fg'] else ""
                output = f"{color_code}{cell['char']}{reset_code}"
                self.client.send(output) if not line_render else buffer.append(output)
            if y < render_height - 1:
                self.client.sendln("") if not line_render else buffer.append("\n")

        if line_render and not raw_output:
            for line in buffer:
                self.client.send(line)

        if raw_output:
            return "".join(buffer)

    def check_terminal_resize(self) -> bool:
        """Check if terminal has been resized since screen was created"""
        if not self.screen:
            return False
        current_size = self.client.get_terminal_size()
        return current_size != (self.screen.width, self.screen.height)

    def resize_to_terminal(self):
        """Resize screen to match current terminal size"""
        if not self.screen:
            return
        current_size = self.client.get_terminal_size()
        if current_size != (self.screen.width, self.screen.height):
            old_screen = self.screen
            self.screen = Surface(current_size[0], current_size[1])
            # Copy existing content
            self.screen.blit(old_screen, (0, 0))