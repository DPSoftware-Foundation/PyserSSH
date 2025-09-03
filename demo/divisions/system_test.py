from PyserSSH import Send
from PyserSSH.extensions.XHandler import Division
from PyserSSH.system.clientype import Client
from damp11113.utils import TextFormatter

div = Division("system", "Test command for system", category="Test Function (System)")

@div.command(name="errortest")
def xh_errortest(client: Client):
    raise Exception("hello error")

@div.command(name="colortest")
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
