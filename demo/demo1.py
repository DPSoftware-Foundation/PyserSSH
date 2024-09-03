import os
import socket
import time
import cv2
import traceback
import requests
from bs4 import BeautifulSoup
import numpy as np

#import logging
#logging.basicConfig(level=logging.DEBUG)

from PyserSSH import Server, AccountManager
from PyserSSH.interactive import Send, wait_input, wait_inputkey, wait_choose, Clear, wait_inputmouse
from PyserSSH.system.info import __version__, Flag_TH
from PyserSSH.extensions.processbar import indeterminateStatus, LoadingProgress
from PyserSSH.extensions.dialog import MenuDialog, TextDialog, TextInputDialog
from PyserSSH.extensions.moredisplay import clickable_url, Send_karaoke_effect
from PyserSSH.extensions.moreinteractive import ShowCursor
from PyserSSH.extensions.remodesk import RemoDesk
from PyserSSH.extensions.XHandler import XHandler
from PyserSSH.system.clientype import Client
from PyserSSH.system.remotestatus import remotestatus

useraccount = AccountManager(allow_guest=True)
useraccount.add_account("admin", "")  # create user without password
useraccount.add_account("test", "test")  # create user without password
useraccount.add_account("demo")
useraccount.add_account("remote", "12345", permissions=["remote_desktop"])
useraccount.set_user_enable_inputsystem_echo("remote", False)
useraccount.set_user_sftp_allow("admin", True)

XH = XHandler()
ssh = Server(useraccount,
             system_commands=True,
             system_message=False,
             sftp=True,
             enable_preauth_banner=True,
             XHandler=XH)

remotedesktopserver = RemoDesk()

servername = "PyserSSH"

loading = ["PyserSSH", "Extensions"]

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

@ssh.on_user("pre-shell")
def guestauth(client):
    if client.get_name() == "remote":
        return

    if not useraccount.has_user(client.get_name()):
        while True:
            Clear(client)
            Send(client, f"You are currently logged in as a guest. To access, please login or register.\nYour current account: {client.get_name()}\n")
            method = wait_choose(client, ["Login", "Register", "Exit"], prompt="Action: ")
            Clear(client)
            if method == 0:  # login
                username = wait_input(client, "Username: ", noabort=True)

                if not username:
                    Send(client, "Please Enter username")
                    wait_inputkey(client, "Press any key to continue...")
                    continue

                password = wait_input(client, "Password: ", password=True, noabort=True)

                Send(client, "Please wait...")
                if not useraccount.has_user(username):
                    Send(client, f"Username isn't exist. Please try again")
                    wait_inputkey(client, "Press any key to continue...")
                    continue

                if not useraccount.validate_credentials(username, password):
                    Send(client, f"Password incorrect. Please try again")
                    wait_inputkey(client, "Press any key to continue...")
                    continue

                Clear(client)
                client.switch_user(username)
                break
            elif method == 1:  # register
                username = wait_input(client, "Please choose a username: ", noabort=True)
                if not username:
                    Send(client, "Please Enter username")
                    wait_inputkey(client, "Press any key to continue...")
                    continue

                if useraccount.has_user(username):
                    Send(client, f"Username is exist. Please try again")
                    wait_inputkey(client, "Press any key to continue...")
                    continue

                password = wait_input(client, "Password: ", password=True, noabort=True)

                if not password:
                    Send(client, "Please Enter password")
                    wait_inputkey(client, "Press any key to continue...")
                    continue

                confirmpassword = wait_input(client, "Confirm Password: ", password=True, noabort=True)

                if not password:
                    Send(client, "Please Enter confirm password")
                    wait_inputkey(client, "Press any key to continue...")
                    continue

                if password != confirmpassword:
                    Send(client, "Password do not matching the confirm password. Please try again.")
                    wait_inputkey(client, "Press any key to continue...")
                    continue

                Send(client, "Please wait...")
                useraccount.add_account(username, password, ["user"])
                client.switch_user(username)
                Clear(client)
                break
            else:
                client.close()

@ssh.on_user("connect")
def connect(client):
    if client.get_name() == "remote":
        return

    client.set_prompt(client["current_user"] + "@" + servername + ":~$")

    wm = f"""{Flag_TH()}{'–'*50}
Hello {client['current_user']},

This is testing server of PyserSSH v{__version__}.

Visit: {clickable_url("https://damp11113.xyz", "DPCloudev")}
{'–'*50}"""

    for i in loading:
        P = indeterminateStatus(client, f"Starting {i}", f"[ OK ] Started {i}")
        P.start()

        time.sleep(len(i) / 20)

        P.stop()

    Di1 = TextDialog(client, "Welcome!\n to PyserSSH test server", "PyserSSH Extension")
    Di1.render()

    for char in wm:
        Send(client, char, ln=False)
        #time.sleep(0.005)  # Adjust the delay as needed
    Send(client, '\n')  # Send newline after each line

@ssh.on_user("authbanner")
def banner(tmp):
    return "Hello World!\n", "en"

@ssh.on_user("error")
def error(client, error):
    if isinstance(error, socket.error):
        pass
    else:
        Send(client, traceback.format_exc())

@XH.command(name="startremotedesktop", category="Remote", permissions=["remote_desktop"])
def remotedesktop(client):
    remotedesktopserver.handle_new_client(client)

@XH.command(name="passtest", category="Test Function")
def xh_passtest(client):
    user = wait_input(client, "username: ")
    password = wait_input(client, "password: ", password=True)
    Send(client, f"username: {user} | password: {password}")

@XH.command(name="colortest", category="Test Function")
def xh_colortest(client):
    for i in range(0, 255, 5):
        Send(client, TextFormatter.format_text_truecolor(" ", background=f"{i};0;0"), ln=False)
    Send(client, "")
    for i in range(0, 255, 5):
        Send(client, TextFormatter.format_text_truecolor(" ", background=f"0;{i};0"), ln=False)
    Send(client, "")
    for i in range(0, 255, 5):
        Send(client, TextFormatter.format_text_truecolor(" ", background=f"0;0;{i}"), ln=False)
    Send(client, "")
    Send(client, "TrueColors 24-Bit")

@XH.command(name="keytest", category="Test Function")
def xh_keytest(client: Client):
    user = wait_inputkey(client, "press any key", raw=True, timeout=1)
    Send(client, "")
    Send(client, f"key: {user}")
    for i in range(10):
        user = wait_inputkey(client, "press any key", raw=True, timeout=1)
        Send(client, "")
        Send(client, f"key: {user}")

@XH.command(name="typing")
def xh_typing(client: Client, messages, speed = 1):
    for w in messages:
        Send(client, w, ln=False)
        time.sleep(float(speed))
    Send(client, "")

@XH.command(name="renimtest")
def xh_renimtest(client: Client, path: str):
    Clear(client)
    image = cv2.imread(f"opensource.png", cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    width, height = client['windowsize']["width"] - 5, client['windowsize']["height"] - 5

    # resize image
    resized = cv2.resize(image, (width, height))
    t = ""

    # Scan all pixels
    for y in range(0, height):
        for x in range(0, width):
            pixel_color = resized[y, x]
            if pixel_color.tolist() != [0, 0, 0]:
                t += TextFormatter.format_text_truecolor(" ",
                                                            background=f"{pixel_color[0]};{pixel_color[1]};{pixel_color[2]}")
            else:
                t += " "

        Send(client, t, ln=False)
        Send(client, "")
        t = ""

@XH.command(name="errortest", category="Test Function")
def xh_errortest(client: Client):
    raise Exception("hello error")

@XH.command(name="inloadtest", category="Test Function")
def xh_inloadtest(client: Client):
    loading = indeterminateStatus(client)
    loading.start()
    time.sleep(5)
    loading.stop()

@XH.command(name="loadtest", category="Test Function")
def xh_loadtest(client: Client):
    l = LoadingProgress(client, total=100, color=True)
    l.start()
    for i in range(101):
        l.current = i
        l.status = f"loading {i}"
        time.sleep(0.05)
    l.stop()

@XH.command(name="dialogtest", category="Test Function")
def xh_dialogtest(client: Client):
    Di1 = TextDialog(client, "Hello Dialog!", "PyserSSH Extension")
    Di1.render()

@XH.command(name="dialogtest2", category="Test Function")
def xh_dialogtest2(client: Client):
    Di2 = MenuDialog(client, ["H1", "H2", "H3"], "PyserSSH Extension", "Hello world")
    Di2.render()
    Send(client, f"selected index: {Di2.output()}")

@XH.command(name="dialogtest3", category="Test Function")
def xh_dialogtest3(client: Client):
    Di3 = TextInputDialog(client, "PyserSSH Extension")
    Di3.render()
    Send(client, f"input: {Di3.output()}")

@XH.command(name="passdialogtest3", category="Test Function")
def xh_passdialogtest3(client: Client):
    Di3 = TextInputDialog(client, "PyserSSH Extension", inputtitle="Password Here", password=True)
    Di3.render()
    Send(client, f"password: {Di3.output()}")

@XH.command(name="choosetest", category="Test Function")
def xh_choosetest(client: Client):
    mylist = ["H1", "H2", "H3"]
    cindex = wait_choose(client, mylist, "select: ")
    Send(client, f"selected: {mylist[cindex]}")

@XH.command(name="vieweb")
def xh_vieweb(client: Client, url: str):
    loading = indeterminateStatus(client, desc=f"requesting {url}...")
    loading.start()
    try:
        content = requests.get(url).content
    except:
        loading.stopfail()
        return
    loading.stop()
    loading = indeterminateStatus(client, desc=f"parsing html {url}...")
    loading.start()
    try:
        soup = BeautifulSoup(content, 'html.parser')
        # Extract only the text content
        text_content = soup.get_text()
    except:
        loading.stopfail()
        return
    loading.stop()
    Di1 = TextDialog(client, text_content, url)
    Di1.render()

@XH.command(name="shutdown")
def xh_shutdown(client: Client, at: str):
    if at == "now":
        ssh.stop_server()

@XH.command(name="mouseinput", category="Test Function")
def xh_mouseinput(client: Client):
    for i in range(10):
        button, x, y = wait_inputmouse(client)
        if button == 0:
            Send(client, "Left Button")
        elif button == 1:
            Send(client, "Middle Button")
        elif button == 2:
            Send(client, "Right Button")
        elif button == 3:
            Send(client, "Button Up")

        Send(client, f"Current POS: X {x} | Y {y} with button {button}")

@XH.command(name="karaoke")
def xh_karaoke(client: Client):
    ShowCursor(client, False)
    Send_karaoke_effect(client, "Python can print like karaoke!")
    ShowCursor(client)

R1 = 1
R2 = 2
K2 = 5

theta_spacing = 0.07
phi_spacing = 0.02

illumination = np.fromiter(".,-~:;=!*#$@", dtype="<U1")

def render_frame(A: float, B: float, screen_size) -> np.ndarray:
    K1 = screen_size * K2 * 3 / (8 * (R1 + R2))
    """
    Returns a frame of the spinning 3D donut.
    Based on the pseudocode from: https://www.a1k0n.net/2011/07/20/donut-math.html
    """
    cos_A = np.cos(A)
    sin_A = np.sin(A)
    cos_B = np.cos(B)
    sin_B = np.sin(B)

    output = np.full((screen_size, screen_size), " ")  # (40, 40)
    zbuffer = np.zeros((screen_size, screen_size))  # (40, 40)

    cos_phi = np.cos(phi := np.arange(0, 2 * np.pi, phi_spacing))  # (315,)
    sin_phi = np.sin(phi)  # (315,)
    cos_theta = np.cos(theta := np.arange(0, 2 * np.pi, theta_spacing))  # (90,)
    sin_theta = np.sin(theta)  # (90,)
    circle_x = R2 + R1 * cos_theta  # (90,)
    circle_y = R1 * sin_theta  # (90,)

    x = (np.outer(cos_B * cos_phi + sin_A * sin_B * sin_phi, circle_x) - circle_y * cos_A * sin_B).T  # (90, 315)
    y = (np.outer(sin_B * cos_phi - sin_A * cos_B * sin_phi, circle_x) + circle_y * cos_A * cos_B).T  # (90, 315)
    z = ((K2 + cos_A * np.outer(sin_phi, circle_x)) + circle_y * sin_A).T  # (90, 315)
    ooz = np.reciprocal(z)  # Calculates 1/z
    xp = (screen_size / 2 + K1 * ooz * x).astype(int)  # (90, 315)
    yp = (screen_size / 2 - K1 * ooz * y).astype(int)  # (90, 315)
    L1 = (((np.outer(cos_phi, cos_theta) * sin_B) - cos_A * np.outer(sin_phi, cos_theta)) - sin_A * sin_theta)  # (315, 90)
    L2 = cos_B * (cos_A * sin_theta - np.outer(sin_phi, cos_theta * sin_A))  # (315, 90)
    L = np.around(((L1 + L2) * 8)).astype(int).T  # (90, 315)
    mask_L = L >= 0  # (90, 315)
    chars = illumination[L]  # (90, 315)

    for i in range(90):
        mask = mask_L[i] & (ooz[i] > zbuffer[xp[i], yp[i]])  # (315,)

        zbuffer[xp[i], yp[i]] = np.where(mask, ooz[i], zbuffer[xp[i], yp[i]])
        output[xp[i], yp[i]] = np.where(mask, chars[i], output[xp[i], yp[i]])

    return output

@XH.command()
def donut(client, screen_size=40):
    screen_size = int(screen_size)

    A = 1
    B = 1

    for _ in range(screen_size * screen_size):
        A += theta_spacing
        B += phi_spacing
        Clear(client)
        array = render_frame(A, B, screen_size)
        for row in array:
            Send(client, " ".join(row))
            Send(client, "\n")

        if wait_inputkey(client, raw=True, timeout=0.01) == "\x03": break


@XH.command(name="status")
def xh_status(client: Client):
    remotestatus(ssh, client.channel, True)

#@ssh.on_user("command")
#def command(client: Client, command: str):

ssh.run(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'private_key.pem'))

#manager = ServerManager()

# Add servers to the manager
#manager.add_server("server1", server1)

# Start a specific server
#manager.start_server("server1", private_key_path="key")
