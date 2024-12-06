"""
PyserSSH - A Scriptable SSH server. For more info visit https://github.com/DPSoftware-Foundation/PyserSSH
Copyright (C) 2023-present DPSoftware Foundation (MIT)

Visit https://github.com/DPSoftware-Foundation/PyserSSH

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WA3RRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import shlex

from ..interactive import Send, Clear, Title, wait_choose

def system_account_command(client, accounts, action):
    banner = "accman adduser <username> <password>\naccman deluser <username>\naccman passwd <username> <new password>\naccman list"
    try:
        if action[0] == "adduser":
            accounts.add_account(action[1], action[2])
            Send(client, f"Added {action[1]}")
        elif action[0] == "deluser":
            if accounts.has_user(action[1]):
                if not accounts.is_user_has_sudo(action[1]):
                    if wait_choose(client, ["No", "Yes"], prompt="Sure? ") == 1:
                        accounts.remove_account(action[1])
                        Send(client, f"Removed {action[1]}")
                else:
                    Send(client, f"{action[1]} isn't removable.")
            else:
                Send(client, f"{action[1]} not found")
        elif action[0] == "passwd":
            if accounts.has_user(action[1]):
                accounts.change_password(action[1], action[2])
                Send(client, f"Password updated successfully.")
            else:
                Send(client, f"{action[1]} not found")
        elif action[0] == "list":
            for user in accounts.list_users():
                Send(client, user)
        else:
            Send(client, banner)
    except:
        Send(client, banner)

def systemcommand(client, command, serverself):
    if command == "whoami":
        Send(client, client["current_user"])
        return True
    elif command.startswith("title"):
        args = shlex.split(command)
        title = args[1]
        Title(client, title)
        return True
    elif command.startswith("accman"):
        args = shlex.split(command)
        if serverself.accounts.is_user_has_sudo(client.current_user):
            system_account_command(client, serverself.accounts, args[1:])
        else:
            Send(client, "accman: Permission denied.")
        return True
    elif command == "exit":
        client["channel"].close()
        return True
    elif command == "clear":
        Clear(client)
        return True
    else:
        return False