import os
import time
from damp11113 import SRTParser

from PyserSSH import Server, Send, AccountManager
from PyserSSH.extensions.XHandler import XHandler
from PyserSSH.extensions.moredisplay import Send_karaoke_effect, ShowCursor

accountmanager = AccountManager()
accountmanager.add_account("admin", "")

XH = XHandler()
server = Server(accountmanager, XHandler=XH)

@XH.command()
def karaoke(client):
    ShowCursor(client, False)
    subtitle = SRTParser("Save Your Tears lyrics.srt", removeln=True)

    for sub in subtitle:
        delay = sub["duration"] / len(sub["text"])
        Send_karaoke_effect(client, sub["text"], delay)

        if sub["next_text_duration"] is not None:
            time.sleep(sub["next_text_duration"])

    ShowCursor(client)

server.run(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'private_key.pem'))