"""
PyserSSH - A Scriptable SSH server. For more info visit https://github.com/damp11113/PyserSSH
Copyright (C) 2023-2024 damp11113 (MIT)

Visit https://github.com/damp11113/PyserSSH

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

import pickle
import time
import atexit
import threading

class AccountManager:
    def __init__(self, anyuser=False, historylimit=10, autosave=False, autosavedelay=60, autoload=False, autoloadfile="autosave_session.ses"):
        self.accounts = {}
        self.anyuser = anyuser
        self.historylimit = historylimit
        self.autosavedelay = autosavedelay

        self.__autosavework = False
        self.__autosaveworknexttime = 0

        if self.anyuser:
            print("history system can't work if 'anyuser' is enable")

        if autoload:
            self.load(autoloadfile)

        if autosave:
            self.__autosavethread = threading.Thread(target=self.__autosave)
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

    def validate_credentials(self, username, password):
        if username in self.accounts and self.accounts[username]["password"] == password or self.anyuser:
            return True
        return False

    def get_permissions(self, username):
        if username in self.accounts:
            return self.accounts[username]["permissions"]
        return []

    def set_prompt(self, username, prompt=">"):
        if username in self.accounts:
            self.accounts[username]["prompt"] = prompt

    def get_prompt(self, username):
        if username in self.accounts and "prompt" in self.accounts[username]:
            return self.accounts[username]["prompt"]
        return ">"  # Default prompt if not set for the user

    def add_account(self, username, password, permissions={}):
        self.accounts[username] = {"password": password, "permissions": permissions}

    def change_password(self, username, new_password):
        if username in self.accounts:
            self.accounts[username]["password"] = new_password

    def set_permissions(self, username, new_permissions):
        if username in self.accounts:
            self.accounts[username]["permissions"] = new_permissions

    def save(self, filename="session.ssh"):
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
        if username in self.accounts:
            self.accounts[username]["sftp_allow"] = allow

    def get_user_sftp_allow(self, username):
        if username in self.accounts and "sftp_allow" in self.accounts[username]:
            if self.anyuser:
                return True
            return self.accounts[username]["sftp_allow"]
        return True

    def set_user_sftp_readonly(self, username, readonly=False):
        if username in self.accounts:
            self.accounts[username]["sftp_readonly"] = readonly

    def get_user_sftp_readonly(self, username):
        if username in self.accounts and "sftp_readonly" in self.accounts[username]:
            return self.accounts[username]["sftp_readonly"]
        return False

    def set_user_sftp_path(self, username, path="/"):
        if username in self.accounts:
            if path == "/":
                self.accounts[username]["sftp_path"] = ""
            else:
                self.accounts[username]["sftp_path"] = path

    def get_user_sftp_path(self, username):
        if username in self.accounts and "sftp_path" in self.accounts[username]:
            return self.accounts[username]["sftp_path"]
        return ""

    def set_banner(self, username, banner):
        if username in self.accounts:
            self.accounts[username]["banner"] = banner

    def get_banner(self, username):
        if username in self.accounts and "banner" in self.accounts[username]:
            return self.accounts[username]["banner"]
        return None

    def get_user_timeout(self, username):
        if username in self.accounts and "timeout" in self.accounts[username]:
            return self.accounts[username]["timeout"]
        return None

    def set_user_timeout(self, username, timeout=None):
        if username in self.accounts:
            self.accounts[username]["timeout"] = timeout

    def get_user_last_login(self, username):
        if username in self.accounts and "lastlogin" in self.accounts[username]:
            return self.accounts[username]["lastlogin"]
        return None

    def set_user_last_login(self, username, ip, timelogin=time.time()):
        if username in self.accounts:
            self.accounts[username]["lastlogin"] = {
                "ip": ip,
                "time": timelogin
            }

    def add_history(self, username, command):
        if not self.anyuser:
            if username in self.accounts:
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
        if not self.anyuser:
            if username in self.accounts:
                self.accounts[username]["history"] = []  # Initialize history list if it doesn't exist

    def get_history(self, username, index, getall=False):
        if not self.anyuser:
            if username in self.accounts and "history" in self.accounts[username]:
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
        if not self.anyuser:
            if username in self.accounts and "lastcommand" in self.accounts[username]:
                command = self.accounts[username]["lastcommand"]
                return command
            return None  # User or history not found
