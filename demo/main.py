import os
os.environ["damp11113_load_all_module"] = "NO"

import socket
import time
import traceback
import logging

# Configure logging
logging.basicConfig(format='[{asctime}] [{levelname}] {name}: {message}', datefmt='%Y-%m-%d %H:%M:%S', style='{', level=logging.DEBUG)

from PyserSSH import Server, AccountManager
from PyserSSH.interactive import Send, wait_input, wait_inputkey, wait_choose, Clear, wait_input_old
from PyserSSH.system.info import version, Flag_TH
from PyserSSH.extensions.moredisplay import clickable_url
from PyserSSH.extensions.XHandler import XHandler, DivisionHandler
from PyserSSH.system.clientype import Client
from PyserSSH.system.RemoteStatus import remotestatus

useraccount = AccountManager(allow_guest=True, autoload=True, autosave=True)
if not os.path.isfile("autosave_session.ses"):
    useraccount.add_account("admin", "", sudo=True)  # create user without password
    useraccount.add_account("test", "test")  # create user without password
    useraccount.add_account("demo")
    useraccount.add_account("remote", "12345", permissions=["remote_desktop"])
    useraccount.set_user_enable_inputsystem_echo("remote", False)
    useraccount.set_user_sftp_allow("admin", True)

XH = XHandler()
DH = DivisionHandler(XH)
ssh = Server(useraccount,
             system_commands=True,
             system_message=False,
             sftp=True,
             enable_preauth_banner=True,
             XHandler=XH,
             enable_remote_status=True)

DH.register_division_from_module("divisions.barplus_test.div")
DH.register_division_from_module("divisions.dialog_test.div")
DH.register_division_from_module("divisions.drawing_test.div")
DH.register_division_from_module("divisions.interactive_test.div")
DH.register_division_from_module("divisions.processbar_test.div")
DH.register_division_from_module("divisions.remodesk_test.div")
DH.register_division_from_module("divisions.system_test.div")
DH.register_division_from_module("divisions.vstream_test.div")
DH.register_division_from_module("divisions.dialogplus_test.div")
DH.register_division_from_module("divisions.paint.div")

servername = "PyserSSH"

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

                password = wait_input_old(client, "Password: ", password=True, noabort=True)

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

                password = wait_input_old(client, "Password: ", password=True, noabort=True)

                if not password:
                    Send(client, "Please Enter password")
                    wait_inputkey(client, "Press any key to continue...")
                    continue

                confirmpassword = wait_input_old(client, "Confirm Password: ", password=True, noabort=True)

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

This is testing server of PyserSSH v{version}.

Visit: {clickable_url("https://damp11113.xyz", "DPCloudev")}
{'–'*50}"""

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

@XH.command(name="typing")
def xh_typing(client: Client, messages, speed = 1):
    for w in messages:
        Send(client, w, ln=False)
        time.sleep(float(speed))
    Send(client, "")

@XH.command(name="shutdown", permissions=["root"])
def xh_shutdown(client: Client, at: str):
    if at == "now":
        ssh.stop_server()

@XH.command(name="status")
def xh_status(client: Client):
    remotestatus(ssh, client.channel, True)

#@ssh.on_user("command")
#def command(client: Client, command: str):

ssh.run(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'private_key.pem'))