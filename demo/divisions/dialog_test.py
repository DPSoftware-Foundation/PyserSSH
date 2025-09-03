import requests
from bs4 import BeautifulSoup

from PyserSSH import Send
from PyserSSH.extensions.XHandler import Division
from PyserSSH.extensions.dialog import TextDialog, TextInputDialog, MenuDialog
from PyserSSH.extensions.processbar import indeterminateStatus
from PyserSSH.system.clientype import Client

div = Division("dialog", "Test command for dialog extension module", category="Test Function (Dialog)")

@div.command(name="dialogtest")
def xh_dialogtest(client: Client):
    Di1 = TextDialog(client, "Hello Dialog!", "PyserSSH Extension")
    Di1.render()

@div.command(name="dialogtest2")
def xh_dialogtest2(client: Client):
    Di2 = MenuDialog(client, ["H1", "H2", "H3"], "PyserSSH Extension", "Hello world")
    Di2.render()
    Send(client, f"selected index: {Di2.output()}")

@div.command(name="dialogtest3")
def xh_dialogtest3(client: Client):
    Di3 = TextInputDialog(client, "PyserSSH Extension")
    Di3.render()
    Send(client, f"input: {Di3.output()}")

@div.command(name="passdialogtest3")
def xh_passdialogtest3(client: Client):
    Di3 = TextInputDialog(client, "PyserSSH Extension", inputtitle="Password Here", password=True)
    Di3.render()
    Send(client, f"password: {Di3.output()}")

@div.command(name="vieweb")
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
