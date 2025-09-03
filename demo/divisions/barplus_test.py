import random
import time

from PyserSSH import Clear
from PyserSSH.extensions.BarPlus import BarPlus_Display, BarPlus_ProgressBar
from PyserSSH.extensions.XHandler import Division
from PyserSSH.extensions.dialog import TextInputDialog, TextDialog
from PyserSSH.extensions.processbar import Steps
from PyserSSH.system.clientype import Client

div = Division("barplus", "Test command for bar+ extension module", category="Test Function (Bar+)")

@div.command(name="barplus")
def xh_barplus(client: Client):
    running = True

    def onkey(key):
        nonlocal running

        if key == b"q":
            running = False

    Clear(client, only_current_screen=True)

    display = BarPlus_Display(client, "BarPlus Test Display", update_rate=0.1)

    display.on_key_handle = onkey

    display.add_static_line("Press Q to exit")
    # Create progress bars

    # System 13 - Single bar (red)
    system13 = BarPlus_ProgressBar("System 13", width=30)
    system13.add_segment(0, 500, "255;0;0", "Processing")
    system13.set_info("")

    # System 14 - Stacked bar with multiple segments
    system14 = BarPlus_ProgressBar("System 14", width=30, steps_animation=Steps.receiving, ena_stack_layer=True)
    system14.add_segment(0, 200, "0;255;0", "Complete")
    system14.add_segment(0, 150, "255;255;0", "Processing", layer=1)
    system14.add_segment(0, 100, "255;0;0", "Pending", layer=2)
    system14.set_info("")

    system15 = BarPlus_ProgressBar("System 15", width=30, steps_animation=Steps.connecting)
    system15.add_segment(0, 300, "0;247;247", "Base")  # Base layer
    system15.add_segment(0, 200, "255;255;0", "Buffer")  # Buffer layer (can override base)
    system15.add_segment(0, 100, "255;0;0", "Current")  # Current layer (highest priority)
    system15.set_info("")

    # System 15 - Different colors
    system16 = BarPlus_ProgressBar("System 16", width=30, steps_animation=Steps.requesting)
    system16.add_segment(0, 300, "0;247;247", "Active")
    system16.add_segment(0, 100, "247;0;247", "Queue")
    system16.set_info("")

    # System 16 - Small bar (blue)
    system17 = BarPlus_ProgressBar("System 17", width=30, steps_animation=Steps.waiting)
    system17.add_segment(0, 150, "0;0;255", "Tasks")
    system17.set_info("")

    # Add bars to display
    display.add_progress_bar(system13)
    display.add_progress_bar(system14)
    display.add_progress_bar(system15)
    display.add_progress_bar(system16)
    display.add_progress_bar(system17)

    display.start()

    step = 0
    while True:
        # Update System 13
        system13.update_segment(0, min(step * 2, 500))

        # Update System 14 (stacked)
        system14.update_segment(0, min(step * 1, 200))  # Complete
        system14.update_segment(1, min(step * 1, 150))  # Processing
        system14.update_segment(2, min(step * 1, 100))  # Pending

        # Update System 15 (stacked)
        system16.update_segment(0, min(step * 4, 300))  # Active
        system16.update_segment(1, min(step * 1, 100))  # Queue

        system15.update_segment(0, min(step * 4, 300))  # Base (cyan)
        system15.update_segment(1, min(step * 3, 200))  # Buffer (yellow) - overrides cyan
        system15.update_segment(2, min(step * 2, 100))  # Current (red) - overrides everything

        # Update System 16
        system17.update_segment(0, min(step * 3, 150))

        time.sleep(0.01)
        step += 1

        if step > 250 or not running:  # Reset after completion
            system13.stop()
            system14.stopfail()
            system15.stop()
            system16.stopfail()
            system17.stop()

            time.sleep(0.1)

            display.exit()
            break

class PID:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0
        self.integral = 0

    def compute(self, target, actual):
        error = target - actual
        self.integral += error
        derivative = error - self.prev_error
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.prev_error = error
        return output

@div.command(name="engpid")
def xh_engpid(client: Client):
    running = True
    max_rpm = 7000
    target_rpm = 3000

    display = BarPlus_Display(client, "Engine RPM Controller", update_rate=0.1)
    pid = PID(kp=0.004, ki=0.003, kd=0.0)

    def onkey(key):
        nonlocal running, target_rpm

        if key == b"q":
            running = False
        elif key == b"w":
            target_rpm = min(target_rpm + 100, max_rpm)
            rpm_bar.update_segment(1, int(target_rpm))
        elif key == b"s":
            target_rpm = max(target_rpm - 100, 0)
            rpm_bar.update_segment(1, int(target_rpm))
        elif key == b"p":
            display.is_paused = True
            DiR = TextInputDialog(client, "PID Settings", "Enter new Kp value (Float Number)")
            DiR.render()
            try:
                pid.kp = float(DiR.output())
                Dii = TextDialog(client, f"New Kp value set to {pid.kp}", "PID Settings", exit_key=None)
                Dii.render()
            except:
                Dii = TextDialog(client, "Invalid input. Please enter a valid float number.", "PID Settings", exit_key=None)
                Dii.render()
            display.is_paused = False
        elif key == b"i":
            display.is_paused = True
            DiR = TextInputDialog(client, "PID Settings", "Enter new Ki value (Float Number)")
            DiR.render()
            try:
                pid.ki = float(DiR.output())
                Dii = TextDialog(client, f"New Ki value set to {pid.ki}", "PID Settings", exit_key=None)
                Dii.render()
            except:
                Dii = TextDialog(client, "Invalid input. Please enter a valid float number.", "PID Settings", exit_key=None)
                Dii.render()
            display.is_paused = False
        elif key == b"d":
            display.is_paused = True
            DiR = TextInputDialog(client, "PID Settings", "Enter new Kd value (Float Number)")
            DiR.render()
            try:
                pid.kd = float(DiR.output())
                Dii = TextDialog(client, f"New Kd value set to {pid.kd}", "PID Settings", exit_key=None)
                Dii.render()
            except:
                Dii = TextDialog(client, "Invalid input. Please enter a valid float number.", "PID Settings", exit_key=None)
                Dii.render()
            display.is_paused = False

    Clear(client, only_current_screen=True)

    display.on_key_handle = onkey

    display.add_static_line("Press Q to exit, W to increase target RPM, S to decrease target RPM")
    display.add_static_line("Press P to change Kp, I to change Ki, D to change Kd")

    rpm_bar = BarPlus_ProgressBar("RPM (Revving)", width=40, steps_animation=Steps.requesting, ena_stack_layer=True)

    rpm_bar.add_segment(0, max_rpm, "255;0;0", "Current RPM")
    rpm_bar.add_segment(0, max_rpm, "255;255;0", "Target RPM", layer=1)

    rpm_bar.set_info("")
    display.add_progress_bar(rpm_bar)

    actual_rpm = 0
    throttle = 0

    rpm_bar.update_segment(1, int(target_rpm))

    display.start()

    while True:
        # PID logic
        correction = pid.compute(target_rpm, actual_rpm)
        throttle += correction
        throttle = max(0, min(100, throttle))

        # Simulate engine RPM + noise
        rpm_change = throttle * 80
        noise = random.uniform(-150, 150)
        actual_rpm = rpm_change + noise
        actual_rpm = max(0, min(max_rpm, actual_rpm))

        # Update progress bar
        rpm_bar.update_segment(0, int(actual_rpm))

        time.sleep(0.01)

        if not running:  # Reset after completion
            display.exit()
            break