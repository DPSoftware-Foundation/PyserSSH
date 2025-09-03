import time
from damp11113.format import SRTParser

from PyserSSH import wait_input, Send, wait_inputkey, wait_choose, wait_inputmouse, wait_input_old
from PyserSSH.extensions.XHandler import Division
from PyserSSH.extensions.moredisplay import Send_karaoke_effect
from PyserSSH.extensions.moreinteractive import ShowCursor
from PyserSSH.system.clientype import Client

div = Division("interactive", "Test command for interactive module", category="Test Function (Interactive)")

@div.command(name="passtest")
def xh_passtest(client):
    user = wait_input(client, "username: ")
    password = wait_input_old(client, "password: ", password=True)
    Send(client, f"username: {user} | password: {password}")

@div.command(name="keytest")
def xh_keytest(client: Client):
    user = wait_inputkey(client, "press any key", raw=True, timeout=1)
    Send(client, "")
    Send(client, f"key: {user}")
    for i in range(10):
        user = wait_inputkey(client, "press any key", raw=True, timeout=1)
        Send(client, "")
        Send(client, f"key: {user}")

@div.command(name="choosetest")
def xh_choosetest(client: Client):
    mylist = ["H1", "H2", "H3"]
    cindex = wait_choose(client, mylist, "select: ")
    Send(client, f"selected: {mylist[cindex]}")

@div.command(name="mouseinput")
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

@div.command(name="karaoke")
def xh_karaoke(client: Client):
    ShowCursor(client, False)
    Send_karaoke_effect(client, "Python can print like karaoke!")
    ShowCursor(client)

@div.command(name="karaoke_srt")
def xh_karaoke_srt(client):
    ShowCursor(client, False)
    subtitle = SRTParser("SaveYourTears.srt", removeln=True)

    for sub in subtitle:
        delay = sub["duration"] / len(sub["text"])
        Send_karaoke_effect(client, sub["text"], delay)

        if sub["next_text_duration"] is not None:
            time.sleep(sub["next_text_duration"])

    ShowCursor(client)