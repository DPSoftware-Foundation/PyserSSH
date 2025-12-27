from PyserSSH.extensions.XHandler import Division
from PyserSSH.extensions.remodesk import RemoDesk

div = Division("remodesk", "Command for RemoDesk extension module", category="RemoDesk")
remotedesktopserver = RemoDesk()

@div.command(name="startremotedesktop", permissions=["remote_desktop"])
def xh_remotedesktop(client):
    remotedesktopserver.handle_new_client(client)

