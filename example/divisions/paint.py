import math

from PyserSSH.extensions.XHandler import Division
from PyserSSH.extensions.AdvancedInput import EventType, InputEvent, AdvancedInput, SpecialKey, MouseButton
from PyserSSH.system.clientype import Client
from PyserSSH.interactive import Clear
from PyserSSH.extensions.moreinteractive import ShowCursor

div = Division("paint")

@div.command("paint")
def paint(client: Client):
    ShowCursor(client, False)
    running = True

    # Canvas dimensions
    canvas_width, canvas_height = client.get_terminal_size()
    canvas_height = canvas_height - 10

    # Initialize canvas with spaces and colors
    canvas = [[{'char': ' ', 'color': '37'} for _ in range(canvas_width)] for _ in range(canvas_height)]

    # Current drawing character and color
    current_char = '█'
    colors = ['37', '31', '32', '33', '34', '35', '36', '91', '92', '93', '94', '95', '96']
    color_names = ['White', 'Red', 'Green', 'Yellow', 'Blue', 'Magenta', 'Cyan',
                   'Bright Red', 'Bright Green', 'Bright Yellow', 'Bright Blue',
                   'Bright Magenta', 'Bright Cyan']
    current_color_idx = 0

    # Drawing modes
    modes = ['PAINT', 'LINE', 'RECTANGLE', 'RECTANGLE_FILL', 'CIRCLE', 'CIRCLE_FILL']
    current_mode = 0

    # Drawing state
    is_drawing = False
    start_x, start_y = 0, 0
    preview_canvas = None

    adv_input = AdvancedInput(client, mouse_mode=3)

    def draw_header():
        client.send("\033[H")  # Move cursor home
        client.sendln("🎨 PIXEL PAINT WITH SHAPES 🎨")
        client.sendln("=" * 60)
        client.sendln(
            f"Mode: {modes[current_mode]} | Color: \033[{colors[current_color_idx]}m{color_names[current_color_idx]}\033[0m | Brush: {current_char}")
        client.sendln("Controls: Click/drag | 'm'=mode | 'c'=color | 'b'=brush | 'r'=reset | Ctrl+C=exit")
        client.sendln("-" * 60)

    def copy_canvas():
        return [[{'char': cell['char'], 'color': cell['color']} for cell in row] for row in canvas]

    def draw_canvas(use_preview=False):
        display_canvas = preview_canvas if use_preview and preview_canvas else canvas
        client.send("\033[s")  # Save cursor position
        for y, row in enumerate(display_canvas):
            client.send(f"\033[{y+6};1H")  # Move cursor to line
            line = ""
            for cell in row:
                if cell['char'] == ' ':
                    line += ' '
                else:
                    line += f"\033[{cell['color']}m{cell['char']}\033[0m"
            client.send(line)
        client.send("\033[u")  # Restore cursor position

    def draw_pixel(x, y, char=None, color=None):
        canvas_y = y - 5
        canvas_x = x

        if 0 <= canvas_x < canvas_width and 0 <= canvas_y < canvas_height:
            cell = canvas[canvas_y][canvas_x]
            cell['char'] = char or current_char
            cell['color'] = color or colors[current_color_idx]

            # Draw only updated pixel
            client.send(f"\033[{canvas_y+6};{canvas_x+1}H")
            client.send(f"\033[{cell['color']}m{cell['char']}\033[0m")

    def set_pixel(x, y, char=None, color=None, target_canvas=None):
        if target_canvas is None:
            draw_pixel(x, y, char, color)
            target_canvas = canvas

        canvas_y = y - 5
        canvas_x = x

        if 0 <= canvas_x < canvas_width and 0 <= canvas_y < canvas_height:
            target_canvas[canvas_y][canvas_x]['char'] = char or current_char
            target_canvas[canvas_y][canvas_x]['color'] = color or colors[current_color_idx]
            return True
        return False

    def draw_line(x1, y1, x2, y2, target_canvas=None):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        x, y = x1, y1
        while True:
            set_pixel(x, y, target_canvas=target_canvas)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def draw_rectangle(x1, y1, x2, y2, target_canvas=None, fill=False):
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        if fill:
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    set_pixel(x, y, target_canvas=target_canvas)
        else:
            for x in range(min_x, max_x + 1):
                set_pixel(x, min_y, target_canvas=target_canvas)
                set_pixel(x, max_y, target_canvas=target_canvas)
            for y in range(min_y, max_y + 1):
                set_pixel(min_x, y, target_canvas=target_canvas)
                set_pixel(max_x, y, target_canvas=target_canvas)

    def draw_circle(cx, cy, radius, target_canvas=None, fill=False):
        x = 0
        y = radius
        d = 3 - 2 * radius

        def draw_circle_points(cx, cy, x, y):
            points = [(cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y), (cx - x, cy - y),
                      (cx + y, cy + x), (cx - y, cy + x), (cx + y, cy - x), (cx - y, cy - x)]
            for px, py in points:
                set_pixel(px, py, target_canvas=target_canvas)

        if fill:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        set_pixel(cx + dx, cy + dy, target_canvas=target_canvas)
        else:
            draw_circle_points(cx, cy, x, y)
            while y >= x:
                x += 1
                if d > 0:
                    y -= 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6
                draw_circle_points(cx, cy, x, y)

    def reset_canvas():
        nonlocal canvas
        canvas = [[{'char': ' ', 'color': '37'} for _ in range(canvas_width)] for _ in range(canvas_height)]
        draw_canvas()

    def create_shape_preview(x1, y1, x2, y2):
        nonlocal preview_canvas
        preview_canvas = copy_canvas()

        if modes[current_mode] == 'LINE':
            draw_line(x1, y1, x2, y2, preview_canvas)
        elif modes[current_mode] == 'RECTANGLE':
            draw_rectangle(x1, y1, x2, y2, preview_canvas)
        elif modes[current_mode] == 'RECTANGLE_FILL':
            draw_rectangle(x1, y1, x2, y2, preview_canvas, fill=True)
        elif modes[current_mode] == 'CIRCLE':
            radius = int(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))
            draw_circle(x1, y1, radius, preview_canvas)
        elif modes[current_mode] == 'CIRCLE_FILL':
            radius = int(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))
            draw_circle(x1, y1, radius, preview_canvas, fill=True)

    def finalize_shape(x1, y1, x2, y2):
        if modes[current_mode] == 'LINE':
            draw_line(x1, y1, x2, y2)
        elif modes[current_mode] == 'RECTANGLE':
            draw_rectangle(x1, y1, x2, y2)
        elif modes[current_mode] == 'RECTANGLE_FILL':
            draw_rectangle(x1, y1, x2, y2, fill=True)
        elif modes[current_mode] == 'CIRCLE':
            radius = int(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))
            draw_circle(x1, y1, radius)
        elif modes[current_mode] == 'CIRCLE_FILL':
            radius = int(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))
            draw_circle(x1, y1, radius, fill=True)

    def my_handler(event: InputEvent):
        nonlocal running, is_drawing, current_color_idx, current_char, current_mode
        nonlocal start_x, start_y, preview_canvas

        if event.event_type == EventType.KEY_PRESS:
            if event.special_key == SpecialKey.CTRL_C:
                adv_input._disable_mouse_reporting()
                client.sendln("\033[0m")
                client.sendln("Exiting paint mode. Goodbye!")
                running = False
            elif event.key == "c":
                current_color_idx = (current_color_idx + 1) % len(colors)
                draw_header()
            elif event.key == "b":
                brushes = ['█', '▓', '▒', '░', '*', '#', '@', '+', '.', 'o', 'x']
                current_brush_idx = brushes.index(current_char) if current_char in brushes else 0
                current_char = brushes[(current_brush_idx + 1) % len(brushes)]
                draw_header()
            elif event.key == "m":
                current_mode = (current_mode + 1) % len(modes)
                draw_header()
            elif event.key == "r":
                reset_canvas()

        elif event.event_type == EventType.MOUSE_PRESS:
            if event.button == MouseButton.LEFT:
                is_drawing = True
                start_x, start_y = event.x, event.y
                if modes[current_mode] == 'PAINT':
                    set_pixel(event.x, event.y)

        elif event.event_type == EventType.MOUSE_RELEASE:
            if event.button == MouseButton.LEFT:
                if is_drawing and modes[current_mode] != 'PAINT':
                    finalize_shape(start_x, start_y, event.x, event.y)
                    preview_canvas = None
                is_drawing = False

        elif event.event_type == EventType.MOUSE_DRAG:
            if is_drawing:
                if modes[current_mode] == 'PAINT':
                    set_pixel(event.x, event.y)
                else:
                    create_shape_preview(start_x, start_y, event.x, event.y)
                    draw_canvas(use_preview=True)

    adv_input.event_handler_function = my_handler

    draw_header()
    draw_canvas()

    while running:
        adv_input.tick()

    Clear(client)
    ShowCursor(client, True)
    client.sendln("Paint session ended.")