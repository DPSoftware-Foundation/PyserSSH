import os
import logging
import random
import sys
import socket
import time
import rich
from rich.tree import Tree

class PrintHandler(logging.Handler):
    def __init__(self):
        super().__init__()

        self.show = True
        self.isbooted = False

        self.bootlog = []
        self.start_time = time.monotonic()

    def emit(self, record):
        if self.show:
            if not self.isbooted:
                elapsed = time.monotonic() - self.start_time
                # Format to 6 decimal places like Linux: [      0.000000]

                log_entry = f"[{elapsed:12.6f}] {record.name}: {record.getMessage()}"

                self.bootlog.append(log_entry)
            else:
                log_entry = self.format(record)

            sys.__stdout__.write(log_entry + "\n")

log_handler = PrintHandler()

# Configure logging
logging.basicConfig(format='[{asctime}] [{levelname}] {name}: {message}', datefmt='%Y-%m-%d %H:%M:%S', style='{', level=logging.DEBUG, handlers=[log_handler])

from PyserSSH import Server, LocalAccountManager
from PyserSSH.extensions.virtualSTD import StreamSTD
from PyserSSH.account.mongoAM import MongoDBAccountManager
from PyserSSH.interactive import Send, wait_input, wait_inputkey, wait_choose, Clear, wait_input_old
from PyserSSH.system.info import version, Flag_TH
from PyserSSH.extensions.moredisplay import clickable_url
from PyserSSH.extensions.XHandler import XHandler, DivisionHandler
from PyserSSH.system.clientype import Client
from PyserSSH.system.RemoteStatus import remotestatus
from PyserSSH.system.KeyInteract import InteractiveAuthManager
from PyserSSH.extensions.pyofetch import pyofetch

#---------------------------------------------------

useraccount = MongoDBAccountManager("mongodb://localhost:27017", allow_guest=True)
#useraccount = LocalAccountManager(allow_guest=True, autoload=False, autosave=True)
#if not os.path.isfile("autosave_session.ses"): # for local
if not useraccount.has_user("admin"): # for mongodb
    useraccount.add_account("admin", "", sudo=True)  # create user without password
    useraccount.add_account("test", "test")  # create user without password
    useraccount.add_account("test2", interactive_auth=True)  # create user without password
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
#DH.register_division_from_module("divisions.remodesk_test.div")
DH.register_division_from_module("divisions.paint.div")
DH.register_division_from_module("divisions.system_test.div")
DH.register_division_from_module("divisions.vstream_test.div")
DH.register_division_from_module("divisions.dialogplus_test.div")
DH.register_division_from_module("divisions.stgl_test.div")

def xhPreSudo(client, command):
    for i in range(3):
        password = wait_input_old(client, f"[sudo] password for {client.get_name()}: ", password=True)

        if useraccount.validate_credentials(useraccount.get_root_user(), password):
            return True
        else:
            client.sendln("Sorry, try again.")

    client.sendln("sudo: 3 incorrect password attempts")

    return False

XH.preSudoActionFunc = xhPreSudo

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

@ssh.on_user("auth_interactive")
def auth_interactive(username, IAM: InteractiveAuthManager):
    IAM.title = "Verify it's you"
    IAM.desc = f"Please verify with OTP that in PyserSSH TTY"

    promptid1 = IAM.add_prompt("OTP: ")

    OTP = random.randint(100000, 999999)

    print(f"OTP for {username} is {OTP}")

    IAM.wait_for_input()

    InOTP = int(IAM.get_response(promptid1))

    if InOTP == OTP:
        IAM.is_authorized(True)
    else:
        IAM.is_authorized(False)

@ssh.on_user("connect")
def connect(client):
    if client.get_name() == "remote":
        return

    client.set_prompt(client["current_user"] + "@" + ssh.hostname + ":~$")

    wm = f"""{Flag_TH()}{'–'*50}
Hello {client['current_user']},

This is testing server of PyserSSH v{version}.

Visit: {clickable_url("https://damp11113.xyz", "DOPFoundation")} (Clickable link)
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
        stream = StreamSTD(client)
        width, height = client.get_terminal_size()
        console = rich.console.Console(
            file=stream.stdout,
            force_terminal=True,
            color_system="truecolor",
            width=width,
            height=height
        )
        console.print_exception()
        stream.deactivate()
        del console

@XH.command(name="typing")
def xh_typing(client: Client, messages, speed = 1):
    for w in messages:
        Send(client, w, ln=False)
        time.sleep(float(speed))
    Send(client, "")

@XH.command(name="shutdown", permissions=["root"], category="System")
def xh_shutdown(client: Client, at: str):
    if at == "now":
        ssh.stop_server()

@XH.command(name="status", category="System")
def xh_status(client: Client):
    remotestatus(ssh, client.channel, True)

@XH.command(name="info", category="System")
def xh_info(client: Client):
    info = pyofetch()
    info.info(ssh, client)

@XH.command(name="dmesg", permissions=["root"], category="System")
def xh_dmesg(client: Client):
    for log in log_handler.bootlog:
        client.sendln(log)

@XH.command(name="division", permissions=["root"], category="System")
def xh_shutdown(client: Client, command:str, module:str=None):
    """
    command: list, reload, enable, disable, unload
    """
    stream = StreamSTD(client)

    console = rich.console.Console(
        file=stream.stdout,
        force_terminal=True,
        color_system="truecolor"  # or "standard" or "256"
    )

    if command == "list":
        modules = DH.list_divisions()
        root = Tree("[bold cyan]XHandler Divisions[/]")

        for module_name, data in modules.items():
            mod_branch = root.add(f"[green]{module_name}[/] ([yellow]{data['category']}[/])")
            mod_branch.add(f"[white]Description:[/] {data['description']}")
            mod_branch.add(f"[white]Enabled:[/] {'True' if data['enabled'] else 'False'}")
            cmds = mod_branch.add(f"[blue]Commands ({data['command_count']}):[/]")
            for cmd in data['commands']:
                cmds.add(f"[magenta]{cmd}[/]")

        console.print(root)
    elif command == "reload":
        with console.status(f"Reloading {module}", spinner="material"):
            is_success = DH.reload_division(module)

        if is_success:
            console.print(f"[green]Module {module} reloaded successfully.[/]")
        else:
            console.print(f"[red]Failed to reload module {module}[/]")
    elif command == "enable":
        is_success = DH.enable_division(module)
        if is_success:
            console.print(f"[green]Module {module} enabled successfully.[/]")
        else:
            console.print(f"[red]Failed to enable module {module}[/]")
    elif command == "disable":
        is_success = DH.disable_division(module)

        if is_success:
            console.print(f"[green]Module {module} disabled successfully.[/]")
        else:
            console.print(f"[red]Failed to disable module {module}[/]")
    elif command == "unload":
        is_success = DH.unregister_division(module)

        if is_success:
            console.print(f"[green]Module {module} unloaded successfully.[/]")
        else:
            console.print(f"[red]Failed to unload module {module}[/]")
    else:
        console.print(f"[red]Unknown command: {command}[/]")

    del console
    stream.deactivate()

@XH.command(name="session", permissions=["root"], category="System")
def xh_shutdown(client: Client, command:str):
    """
    command: list, kill
    """

    if command == "list":
        stream = StreamSTD(client)

        console = rich.console.Console(
            file=stream.stdout,
            force_terminal=True,
            color_system="truecolor"  # or "standard" or "256"
        )

        sessions = ssh.get_active_threads()

        root = Tree("[bold cyan]Active Sessions[/]")
        for peername, sess in sessions.items():
            sess_branch = root.add(f"[green]Session ID: {peername}[/]")
            sess_branch.add(f"[white]Username:[/] {sess['username']}")
            sess_branch.add(f"[white]Connected uptime:[/] {time.time() - sess['start_time']}")

        console.print(root)
        stream.deactivate()

    elif command == "kill":
        sessions = ssh.get_active_threads()
        slist = sessions.items()
        sstrlist = []
        for peername, sess in slist:
            sstrlist.append(f"{peername[0]}:{peername[1]} ({sess['username']})")

        index = wait_choose(client, sstrlist, prompt="Select session to kill: ", selectchar=("< ", " >"))
        peername = list(slist)[index][0]
        ssh.kill_client_thread(peername)
        Send(client, f"Session {peername} has been killed.")
    else:
        Send(client, f"Unknown command: {command}")

@ssh.on_user("disconnected")
def disconnect(client: Client):
    print(f"{client.current_user} from {client.peername} is disconnected")


#@ssh.on_user("command")
#def command(client: Client, command: str):

ssh.run(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'private_key.pem'), daemon=True, host="::", ipv6=True)
log_handler.isbooted = True
#log_handler.show = False
# clear the log
#sys.stdout.write("\033c")
ssh.tty(thread=False)
#sys.stdout.write("\033c")
#log_handler.show = True


while ssh.isrunning:
    try:
        time.sleep(10)
    except:
        ssh.stop_server()
        break