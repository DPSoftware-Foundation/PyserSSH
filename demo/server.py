import os
import socket
import time
import shlex
from damp11113 import TextFormatter, sort_files, allfiles
import cv2
import traceback
import requests
from bs4 import BeautifulSoup

from PyserSSH import Server, AccountManager, Send, wait_input, wait_inputkey, wait_choose, Clear, Title
from PyserSSH.system.info import system_banner
from PyserSSH.extensions.processbar import indeterminateStatus, LoadingProgress
from PyserSSH.extensions.dialog import MenuDialog, TextDialog, TextInputDialog
from PyserSSH.extensions.moredisplay import clickable_url

useraccount = AccountManager()
useraccount.add_account("admin", "") # create user without password
useraccount.add_account("test", "test") # create user without password

ssh = Server(useraccount, system_commands=True, system_message=False)

nonamewarning = """Connection Warning:
Unauthorized access or improper use of this system is prohibited.
Please ensure you have proper authorization before proceeding."""

Authorizedmessage = """You have successfully connected to the server.
Enjoy your session and remember to follow security protocols."""

loading = ["PyserSSH", "Extensions"]

@ssh.on_user("connect")
def connect(client):
    Title(client, "PyserSSH")
    #print(client["windowsize"])
    if client['current_user'] == "":
        warningmessage = nonamewarning
    else:
        warningmessage = Authorizedmessage

    wm = f"""*********************************************************************************************
Hello {client['current_user']},

{warningmessage}

Visit: {clickable_url("https://damp11113.xyz", "DPCloudev")}

{system_banner}
*********************************************************************************************"""

    if client['current_user'] != "test":
        for i in loading:
            P = indeterminateStatus(client, f"Starting {i}", f"[ OK ] Started {i}")
            P.start()

            time.sleep(len(i) / 20)

            P.stop()

        Di1 = TextDialog(client, "PyserSSH Extension", "Welcome!\n to PyserSSH test server")
        Di1.render()

        for char in wm:
            Send(client, char, ln=False)
            # time.sleep(0.005)  # Adjust the delay as needed
        Send(client, '\n')  # Send newline after each line

@ssh.on_user("error")
def error(client, error):
    if isinstance(error, socket.error):
        pass
    else:
        Send(client, traceback.format_exc())


#@ssh.on_user("onrawtype")
#def onrawtype(client, key):
#    print(key)

@ssh.on_user("command")
def command(client, command: str):
    if command == "passtest":
        user = wait_input(client, "username: ")
        password = wait_input(client, "password: ", password=True)
        Send(client, f"username: {user} | password: {password}")
    elif command == "colortest":
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
    elif command == "keytest":
        user = wait_inputkey(client, "press any key", raw=True)
        Send(client, "")
        Send(client, f"key: {user}")
        for i in range(10):
            user = wait_inputkey(client, "press any key", raw=True)
            Send(client, "")
            Send(client, f"key: {user}")
    elif command.startswith("typing"):
        args = shlex.split(command)
        messages = args[1]
        speed = float(args[2])
        for w in messages:
            Send(client, w, ln=False)
            time.sleep(speed)
        Send(client, "")
    elif command.startswith("renimtest"):
        args = shlex.split(command)
        Clear(client)
        image = cv2.imread(f"opensource.png", cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        width, height = client['windowsize']["width"]-5, client['windowsize']["height"]-5

        # resize image
        resized = cv2.resize(image, (width, height))
        t = ""

        # Scan all pixels
        for y in range(0, height):
            for x in range(0, width):
                pixel_color = resized[y, x]
                # PyserSSH.Send(channel, f"Pixel color at ({x}, {y}): {pixel_color}")
                if pixel_color.tolist() != [0, 0, 0]:
                    t += TextFormatter.format_text_truecolor(" ", background=f"{pixel_color[0]};{pixel_color[1]};{pixel_color[2]}")
                else:
                    t += " "

            Send(client, t, ln=False)
            Send(client, "")
            t = ""

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
            l.status = f"loading {i}"
            time.sleep(0.05)
        l.stop()
    elif command == "dialogtest":
        Di1 = TextDialog(client, "PyserSSH Extension", "Hello Dialog!")
        Di1.render()
    elif command == "dialogtest2":
        Di2 = MenuDialog(client, ["H1", "H2", "H3"], "PyserSSH Extension", "Hello world")
        Di2.render()
        Send(client, f"selected index: {Di2.output()}")
    elif command == "dialogtest3":
        Di3 = TextInputDialog(client, "PyserSSH Extension")
        Di3.render()
        Send(client, f"input: {Di3.output()}")
    elif command == "passdialogtest3":
        Di3 = TextInputDialog(client, "PyserSSH Extension", inputtitle="Password Here", password=True)
        Di3.render()
        Send(client, f"password: {Di3.output()}")
    elif command == "choosetest":
        cindex = wait_choose(client, ["H1", "H2", "H3"], "select: ")
        Send(client, f"selected index: {cindex}")
    elif command.startswith("vieweb"):
        args = shlex.split(command)
        url = args[1]
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
        Di1 = TextDialog(client, url, text_content)
        Di1.render()


ssh.run(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'private_key.pem'))
