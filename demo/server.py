import os
import socket
import time
import shlex
from damp11113 import TextFormatter
import cv2
import traceback

from PyserSSH import Server, AccountManager, Send, wait_input, wait_inputkey
from PyserSSH.system.info import system_banner
from PyserSSH.extensions.processbar import indeterminateStatus, LoadingProgress

useraccount = AccountManager()
useraccount.add_account("admin", "") # create user without password

ssh = Server(useraccount, system_commands=True, system_message=False)

nonamewarning = """Connection Warning:
Unauthorized access or improper use of this system is prohibited.
Please ensure you have proper authorization before proceeding."""

Authorizedmessage = """You have successfully connected to the server.
Enjoy your session and remember to follow security protocols."""

@ssh.on_user("connect")
def connect(channel, client):
    #print(client["windowsize"])
    if client['current_user'] == "":
        warningmessage = nonamewarning
    else:
        warningmessage = Authorizedmessage


    wm = f"""*********************************************************************************************
Hello {client['current_user']},

{warningmessage}

{system_banner}
*********************************************************************************************"""

    for char in wm:
        Send(channel, char, ln=False)
        time.sleep(0.005)  # Adjust the delay as needed
    Send(channel, '\n')  # Send newline after each line

@ssh.on_user("error")
def error(channel, error, client):
    if isinstance(error, socket.error):
        pass
    else:
        Send(channel, traceback.format_exc())

@ssh.on_user("command")
def command(channel, command: str, client):
    if command == "passtest":
        user = wait_input(channel, "username: ")
        password = wait_input(channel, "password: ", password=True)
        Send(channel, f"username: {user} | password: {password}")
    elif command == "colortest":
        for i in range(0, 255, 5):
            Send(channel, TextFormatter.format_text_truecolor(" ", background=f"{i};0;0"), ln=False)
        Send(channel, "")
        for i in range(0, 255, 5):
            Send(channel, TextFormatter.format_text_truecolor(" ", background=f"0;{i};0"), ln=False)
        Send(channel, "")
        for i in range(0, 255, 5):
            Send(channel, TextFormatter.format_text_truecolor(" ", background=f"0;0;{i}"), ln=False)
        Send(channel, "")

        Send(channel, "TrueColors 24-Bit")
    elif command == "keytest":
        user = wait_inputkey(channel, "press any key", raw=True)
        Send(channel, "")
        Send(channel, f"key: {user}")
        for i in range(10):
            user = wait_inputkey(channel, "press any key", raw=True)
            Send(channel, "")
            Send(channel, f"key: {user}")
    elif command.startswith("typing"):
        args = shlex.split(command)
        messages = args[1]
        speed = float(args[2])
        for w in messages:
            Send(channel, w, ln=False)
            time.sleep(speed)
        Send(channel, "")
    elif command == "renimtest":
        image = cv2.imread(r"opensource.png", cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        width, height = client['windowsize']["width"], client['windowsize']["height"]

        # resize image
        resized = cv2.resize(image, (width, height))

        # Scan all pixels
        for y in range(0, height):
            for x in range(0, width):
                pixel_color = resized[y, x]
                #PyserSSH.Send(channel, f"Pixel color at ({x}, {y}): {pixel_color}")
                if pixel_color.tolist() != [0, 0, 0]:
                    Send(channel, TextFormatter.format_text_truecolor(" ", background=f"{pixel_color[0]};{pixel_color[1]};{pixel_color[2]}"), ln=False)
                else:
                    Send(channel, " ", ln=False)

            Send(channel, "")
    elif command == "errortest":
        raise Exception("hello error")
    elif command == "inloadtest":
        loading = indeterminateStatus(client)
        loading.start()
        time.sleep(5)
        loading.stop()
    elif command == "loadtest":
        l = LoadingProgress(client, total=100, color=True)
        l.start()
        for i in range(101):
            l.current = i
            l.desc = "loading..."
            time.sleep(0.05)
        l.stop()

ssh.run(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'private_key.pem'))