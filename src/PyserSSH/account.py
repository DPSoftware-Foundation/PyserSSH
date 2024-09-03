"""
PyserSSH - A Scriptable SSH server. For more info visit https://github.com/DPSoftware-Foundation/PyserSSH
Copyright (C) 2023-2024 DPSoftware Foundation (MIT)

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
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os
import pickle
import time
import atexit
import threading
import hashlib

class AccountManager:
    def __init__(self, allow_guest=False, historylimit=10, autosave=False, autosavedelay=60, autoload=False, autoloadfile="autosave_session.ses"):
        self.accounts = {}
        self.allow_guest = allow_guest
        self.historylimit = historylimit
        self.autosavedelay = autosavedelay

        self.__autosavework = False
        self.__autosaveworknexttime = 0

        if autoload:
            self.load(autoloadfile)

        if autosave:
            self.__autosavethread = threading.Thread(target=self.__autosave, daemon=True)
            self.__autosavethread.start()
            atexit.register(self.__saveexit)

    def __autosave(self):
        self.save("autosave_session.ses")
        self.__autosaveworknexttime = time.time() + self.autosavedelay
        self.__autosavework = True
        while self.__autosavework:
            if int(self.__autosaveworknexttime) == int(time.time()):
                self.save("autosave_session.ses")
                self.__autosaveworknexttime = time.time() + self.autosavedelay

            time.sleep(1) # fix cpu load

    def __saveexit(self):
        self.__autosavework = False
        self.save("autosave_session.ses")
        self.__autosavethread.join()

    def validate_credentials(self, username, password=None, public_key=None):
        if self.allow_guest and not self.has_user(username):
            return True

        allowed_auth_list = str(self.accounts[username].get("allowed_auth", "")).split(",")

        # Check password authentication
        if password is not None and "password" in allowed_auth_list:
            stored_password = self.accounts[username].get("password", "")
            return stored_password == hashlib.md5(password.encode()).hexdigest()

        # Check public key authentication
        if public_key is not None and "publickey" in allowed_auth_list:
            stored_public_key = self.accounts[username].get("public_key", "")
            return stored_public_key == public_key

        # Check if 'none' authentication is allowed
        if "none" in allowed_auth_list:
            return True

        return False

    def has_user(self, username):
        return username in self.accounts

    def get_allowed_auths(self, username):
        if self.has_user(username) and "allowed_auth" in self.accounts[username]:
            return self.accounts[username]["allowed_auth"]
        return "none"

    def get_permissions(self, username):
        if self.has_user(username):
            return self.accounts[username]["permissions"]
        return []

    def set_prompt(self, username, prompt=">"):
        if self.has_user(username):
            self.accounts[username]["prompt"] = prompt

    def get_prompt(self, username):
        if self.has_user(username) and "prompt" in self.accounts[username]:
            return self.accounts[username]["prompt"]
        return ">"  # Default prompt if not set for the user

    def add_account(self, username, password=None, public_key=None, permissions:list=None):
        if not self.has_user(username):
            allowedlist = []
            accountkey = {}

            if permissions is None:
                permissions = []

            if password != None:
                allowedlist.append("password")
                accountkey["password"] = hashlib.md5(password.encode()).hexdigest()

            if public_key != None:
                allowedlist.append("publickey")
                accountkey["public_key"] = public_key

            if password is None and public_key is None:
                allowedlist.append("none")

            accountkey["permissions"] = permissions
            accountkey["allowed_auth"] = ",".join(allowedlist)

            self.accounts[username] = accountkey
        else:
            raise Exception(f"{username} is exist")

    def remove_account(self, username):
        if self.has_user(username):
            del self.accounts[username]

    def change_password(self, username, new_password):
        if self.has_user(username):
            self.accounts[username]["password"] = new_password

    def set_permissions(self, username, new_permissions):
        if self.has_user(username):
            self.accounts[username]["permissions"] = new_permissions

    def save(self, filename="session.ses"):
        with open(filename, 'wb') as file:
            pickle.dump(self.accounts, file)

    def load(self, filename):
        try:
            with open(filename, 'rb') as file:
                self.accounts = pickle.load(file)
        except FileNotFoundError:
            print("File not found. No accounts loaded.")
        except Exception as e:
            print(f"An error occurred: {e}. No accounts loaded.")

    def set_user_sftp_allow(self, username, allow=True):
        if self.has_user(username):
            self.accounts[username]["sftp_allow"] = allow

    def get_user_sftp_allow(self, username):
        if self.has_user(username) and "sftp_allow" in self.accounts[username]:
            return self.accounts[username]["sftp_allow"]
        return False

    def set_user_sftp_readonly(self, username, readonly=False):
        if self.has_user(username):
            self.accounts[username]["sftp_readonly"] = readonly

    def get_user_sftp_readonly(self, username):
        if self.has_user(username) and "sftp_readonly" in self.accounts[username]:
            return self.accounts[username]["sftp_readonly"]
        return False

    def set_user_sftp_root_path(self, username, path="/"):
        if self.has_user(username):
            if path == "/":
                self.accounts[username]["sftp_root_path"] = os.getcwd()
            else:
                self.accounts[username]["sftp_root_path"] = path

    def get_user_sftp_root_path(self, username):
        if self.has_user(username) and "sftp_root_path" in self.accounts[username]:
            return self.accounts[username]["sftp_root_path"]
        return os.getcwd()

    def set_user_enable_inputsystem(self, username, enable=True):
        if self.has_user(username):
            self.accounts[username]["inputsystem"] = enable

    def get_user_enable_inputsystem(self, username):
        if self.has_user(username) and "inputsystem" in self.accounts[username]:
            return self.accounts[username]["inputsystem"]
        return True

    def set_user_enable_inputsystem_echo(self, username, echo=True):
        if self.has_user(username):
            self.accounts[username]["inputsystem_echo"] = echo

    def get_user_enable_inputsystem_echo(self, username):
        if self.has_user(username) and "inputsystem_echo" in self.accounts[username]:
            return self.accounts[username]["inputsystem_echo"]
        return True

    def set_banner(self, username, banner):
        if self.has_user(username):
            self.accounts[username]["banner"] = banner

    def get_banner(self, username):
        if self.has_user(username) and "banner" in self.accounts[username]:
            return self.accounts[username]["banner"]
        return None

    def get_user_timeout(self, username):
        if self.has_user(username) and "timeout" in self.accounts[username]:
            return self.accounts[username]["timeout"]
        return None

    def set_user_timeout(self, username, timeout=None):
        if self.has_user(username):
            self.accounts[username]["timeout"] = timeout

    def get_user_last_login(self, username):
        if self.has_user(username) and "lastlogin" in self.accounts[username]:
            return self.accounts[username]["lastlogin"]
        return None

    def set_user_last_login(self, username, ip, timelogin=time.time()):
        if self.has_user(username):
            self.accounts[username]["lastlogin"] = {
                "ip": ip,
                "time": timelogin
            }

    def add_history(self, username, command):
        if self.has_user(username):
            if "history" not in self.accounts[username]:
                self.accounts[username]["history"] = []  # Initialize history list if it doesn't exist

            history_limit = self.historylimit if self.historylimit is not None else float('inf')
            self.accounts[username]["history"].append(command)
            self.accounts[username]["lastcommand"] = command
            # Trim history to the specified limit
            if self.historylimit != None:
                if len(self.accounts[username]["history"]) > history_limit:
                    self.accounts[username]["history"] = self.accounts[username]["history"][-history_limit:]

    def clear_history(self, username):
        if self.has_user(username):
            self.accounts[username]["history"] = []  # Initialize history list if it doesn't exist

    def get_history(self, username, index, getall=False):
        if self.has_user(username) and "history" in self.accounts[username]:
            history = self.accounts[username]["history"]
            history.reverse()
            if getall:
                return history
            else:
                if index < len(history):
                    return history[index]
                else:
                    return None  # Index out of range
        return None  # User or history not found

    def get_lastcommand(self, username):
        if self.has_user(username) and "lastcommand" in self.accounts[username]:
            command = self.accounts[username]["lastcommand"]
            return command
        return None  # User or history not found
