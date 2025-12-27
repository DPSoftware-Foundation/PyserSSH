import time

from PyserSSH.extensions.XHandler import Division
from PyserSSH.extensions.processbar import indeterminateStatus, LoadingProgress
from PyserSSH.system.clientype import Client

div = Division("processbar", "Test command for processbar extension module", category="Test Function (Processbar)")

@div.command(name="inloadtest")
def xh_inloadtest(client: Client):
    loading = indeterminateStatus(client)
    loading.start()
    time.sleep(5)
    loading.stop()

@div.command(name="loadtest")
def xh_loadtest(client: Client):
    l = LoadingProgress(client, total=100, color=True)
    l.start()
    for i in range(101):
        l.current = i
        l.status = f"loading {i}"
        time.sleep(0.05)
    l.stop()