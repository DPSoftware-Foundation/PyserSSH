from PyserSSH.extensions.STGL import TerminalGraphics, Color
from PyserSSH.extensions.XHandler import Division
from PyserSSH.extensions.AdvancedInput import EventType, InputEvent, AdvancedInput, SpecialKey, MouseButton
from PyserSSH.system.clientype import Client
from PyserSSH.interactive import Clear
from PyserSSH.extensions.moreinteractive import ShowCursor

div = Division("tui")

@div.command("stgl_test")
def stgl_test(client: Client):
    ShowCursor(client, False)
    running = True

    tg = TerminalGraphics(client)
    tg.init()

    # Create display surface
    screen = tg.set_mode()

    # Fill background with dark blue
    screen.fill(Color.rgb(20, 20, 40), ' ')

    # Draw some shapes with RGB colors
    screen.draw_rect(Color.rgb(255, 100, 100), (10, 5, 20, 10), 0, '█')  # Light red
    screen.draw_rect(Color.rgb(100, 255, 100), (35, 5, 20, 10), 1, '▓')  # Light green outline

    screen.draw_circle(Color.rgb(100, 150, 255), (20, 15), 5, 0, '●')  # Light blue filled
    screen.draw_circle(Color.rgb(255, 255, 100), (45, 15), 5, 1, '○')  # Yellow outline

    # Rainbow line using HSL
    for i in range(70):
        hue = (i / 70.0) * 360  # 0 to 360 degrees
        color = Color.hsl(hue, 1.0, 0.5)  # Full saturation, medium lightness
        screen.draw_pixel((i + 5, 18), color, '▪')

    # Gradient rectangle
    for x in range(30):
        for y in range(5):
            r = int(255 * (x / 29.0))  # Red gradient
            g = int(255 * (y / 4.0))  # Green gradient
            b = 128  # Constant blue
            color = Color.rgb(r, g, b)
            screen.draw_pixel((x + 25, y + 8), color, '▓')

    # Hex color examples
    screen.draw_text("24-bit Terminal Graphics!", (20, 1), Color.hex('#FF6B6B'))
    screen.draw_text("RGB Colors Available", (22, 2), Color.hex('#4ECDC4'))
    screen.draw_text("Press Enter to exit", (25, 22), Color.rgb(255, 215, 0))

    # create a button
    btn1_posize = (2, 25, 10, 3) # x, y, w, h
    btn1_is_clicked = False
    screen.draw_rect(Color.rgb(200, 200, 200), btn1_posize, 0, '▓')

    screen.draw_3d_box(Color.rgb(255, 0, 0), (65, 5), 15, 10, 8)

    # Update display
    tg.render()

    adv_input = AdvancedInput(client, mouse_mode=3)

    def my_handler(event: InputEvent):
        nonlocal running, btn1_is_clicked

        if event.event_type == EventType.KEY_PRESS:
            print(event)
            if event.special_key == SpecialKey.ENTER:
                running = False

        elif event.event_type == EventType.MOUSE_PRESS:
            print(event)
            if event.button == MouseButton.LEFT:
                # check if mouse is clicked inside the button
                if (btn1_posize[0] <= event.x < btn1_posize[0] + btn1_posize[2] and btn1_posize[1] <= event.y < btn1_posize[1] + btn1_posize[3]):
                    if not btn1_is_clicked:
                        screen.draw_rect(Color.rgb(100, 255, 100), btn1_posize, 0, '▓')
                        btn1_is_clicked = True
                    else:
                        screen.draw_rect(Color.rgb(200, 200, 200), btn1_posize, 0, '▓')
                        btn1_is_clicked = False

                    tg.render()

        elif event.event_type == EventType.MOUSE_RELEASE:
            print(event)

        #elif event.event_type == EventType.MOUSE_DRAG:
        #    print(event)

    adv_input.event_handler_function = my_handler

    while running:
        adv_input.tick()

    adv_input._disable_mouse_reporting()
    Clear(client)
    tg.exit()
    client.sendln("Session ended.")