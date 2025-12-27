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
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import logging
import os
import time
import hashlib
import pymongo

from .AMInterface import IAccountManager

logger = logging.getLogger("PyserSSH.mongoAM")


class MongoDBAccountManager(IAccountManager):
    def __init__(self, server, database="PyserSSH", allow_guest=False, historylimit=10):
        self.allow_guest = allow_guest
        self.historylimit = historylimit

        logger.info("connecting to mongodb server...")
        self.server = pymongo.MongoClient(server)
        logger.info("connected! loading data...")

        self.db = self.server[database]
        self.usersDB = self.db["users"]
        self.historyDB = self.db["history"]

        # Create indexes for better performance
        self.usersDB.create_index("username", unique=True)
        self.historyDB.create_index([("username", 1), ("timestamp", -1)])

        logger.info("ready")

    def validate_credentials(self, username, password=None, public_key=None):
        if self.allow_guest and not self.has_user(username):
            return True

        if not self.has_user(username):
            logger.error(f"{username} does not exist")
            return False

        user_data = self.usersDB.find_one({"username": username})
        if not user_data:
            return False

        allowed_auth_list = str(user_data.get("allowed_auth", "")).split(",")

        # Check password authentication
        if password is not None and "password" in allowed_auth_list:
            stored_password = user_data.get("password", "")
            return stored_password == hashlib.md5(password.encode()).hexdigest()

        # Check public key authentication
        if public_key is not None and "publickey" in allowed_auth_list:
            stored_public_key = user_data.get("public_key", "")
            return stored_public_key == public_key

        # Check if 'none' authentication is allowed
        if "none" in allowed_auth_list:
            return True

        return False

    def has_user(self, username):
        return self.usersDB.find_one({"username": username}) is not None

    def list_users(self):
        return [user["username"] for user in self.usersDB.find({}, {"username": 1, "_id": 0})]

    def get_allowed_auths(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "allowed_auth" in user_data:
            return user_data["allowed_auth"]
        return "none"

    def get_permissions(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data:
            return user_data.get("permissions", [])
        return []

    def set_prompt(self, username, prompt=">"):
        if self.has_user(username):
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"prompt": prompt}}
            )

    def get_prompt(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "prompt" in user_data:
            return user_data["prompt"]
        return ">"  # Default prompt if not set for the user

    def add_account(self, username, password=None, public_key=None, interactive_auth=False, permissions=None, sudo=False):
        if self.has_user(username):
            raise Exception(f"{username} already exists")

        allowedlist = []
        accountkey = {"username": username}

        if permissions is None:
            permissions = []

        if password is not None:
            allowedlist.append("password")
            accountkey["password"] = hashlib.md5(password.encode()).hexdigest()

        if public_key is not None:
            allowedlist.append("publickey")
            accountkey["public_key"] = public_key

        if interactive_auth:
            allowedlist.append("keyboard-interactive")

        if password is None and public_key is None and not interactive_auth:
            allowedlist.append("none")

        if sudo:
            if self.has_sudo_user():
                raise Exception("sudo user already exists")
            accountkey["sudo"] = sudo
            permissions.append("root")

        accountkey["permissions"] = permissions
        accountkey["allowed_auth"] = ",".join(allowedlist)
        accountkey["created_at"] = time.time()

        self.usersDB.insert_one(accountkey)

    def has_sudo_user(self):
        return self.usersDB.find_one({"sudo": True}) is not None

    def is_user_has_sudo(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "sudo" in user_data:
            return user_data["sudo"]
        return False

    def remove_account(self, username):
        if self.has_user(username):
            self.usersDB.delete_one({"username": username})
            # Also remove user's history
            self.historyDB.delete_many({"username": username})

    def change_password(self, username, new_password):
        if self.has_user(username):
            hashed_password = hashlib.md5(new_password.encode()).hexdigest()
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"password": hashed_password}}
            )

    def set_permissions(self, username, new_permissions):
        if self.has_user(username):
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"permissions": new_permissions}}
            )

    def set_user_sftp_allow(self, username, allow=True):
        if self.has_user(username):
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"sftp_allow": allow}}
            )

    def get_user_sftp_allow(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "sftp_allow" in user_data:
            return user_data["sftp_allow"]
        return False

    def set_user_sftp_readonly(self, username, readonly=False):
        if self.has_user(username):
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"sftp_readonly": readonly}}
            )

    def get_user_sftp_readonly(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "sftp_readonly" in user_data:
            return user_data["sftp_readonly"]
        return False

    def set_user_sftp_root_path(self, username, path="/"):
        if self.has_user(username):
            if path == "/":
                path = os.getcwd()
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"sftp_root_path": path}}
            )

    def get_user_sftp_root_path(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "sftp_root_path" in user_data:
            return user_data["sftp_root_path"]
        return os.getcwd()

    def set_user_enable_inputsystem(self, username, enable=True):
        if self.has_user(username):
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"inputsystem": enable}}
            )

    def get_user_enable_inputsystem(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "inputsystem" in user_data:
            return user_data["inputsystem"]
        return True

    def set_user_enable_inputsystem_echo(self, username, echo=True):
        if self.has_user(username):
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"inputsystem_echo": echo}}
            )

    def get_user_enable_inputsystem_echo(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "inputsystem_echo" in user_data:
            return user_data["inputsystem_echo"]
        return True

    def set_banner(self, username, banner):
        if self.has_user(username):
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"banner": banner}}
            )

    def get_banner(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "banner" in user_data:
            return user_data["banner"]
        return None

    def get_user_timeout(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "timeout" in user_data:
            return user_data["timeout"]
        return None

    def set_user_timeout(self, username, timeout=None):
        if self.has_user(username):
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"timeout": timeout}}
            )

    def get_user_last_login(self, username):
        user_data = self.usersDB.find_one({"username": username})
        if user_data and "lastlogin" in user_data:
            return user_data["lastlogin"]
        return None

    def set_user_last_login(self, username, ip, timelogin=None):
        if timelogin is None:
            timelogin = time.time()

        if self.has_user(username):
            login_data = {
                "ip": ip,
                "time": timelogin
            }
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"lastlogin": login_data}}
            )

    def add_history(self, username, command):
        if not self.has_user(username):
            return

        history_entry = {
            "username": username,
            "command": command,
            "timestamp": time.time()
        }

        self.historyDB.insert_one(history_entry)

        # Update last command in user document
        self.usersDB.update_one(
            {"username": username},
            {"$set": {"lastcommand": command}}
        )

        # Trim history to the specified limit if set
        if self.historylimit is not None:
            # Count current history entries
            current_count = self.historyDB.count_documents({"username": username})
            if current_count > self.historylimit:
                # Find oldest entries to remove
                excess_count = current_count - self.historylimit
                oldest_entries = self.historyDB.find(
                    {"username": username}
                ).sort("timestamp", 1).limit(excess_count)

                # Delete oldest entries
                oldest_ids = [entry["_id"] for entry in oldest_entries]
                if oldest_ids:
                    self.historyDB.delete_many({"_id": {"$in": oldest_ids}})

    def clear_history(self, username):
        if self.has_user(username):
            self.historyDB.delete_many({"username": username})

    def get_history(self, username, index=None, getall=False):
        if not self.has_user(username):
            return None

        if getall:
            # Return all history in reverse chronological order (newest first)
            history_cursor = self.historyDB.find(
                {"username": username}
            ).sort("timestamp", -1)
            return [entry["command"] for entry in history_cursor]
        else:
            if index is None:
                return None

            # Get history in reverse chronological order and return specific index
            history_cursor = self.historyDB.find(
                {"username": username}
            ).sort("timestamp", -1).skip(index).limit(1)

            history_list = list(history_cursor)
            if history_list:
                return history_list[0]["command"]
            return None

    def get_lastcommand(self, username):
        if not self.has_user(username):
            return None

        user_data = self.usersDB.find_one({"username": username})
        if user_data and "lastcommand" in user_data:
            return user_data["lastcommand"]
        return None

    def set_env_variable(self, username, variable, value) -> None:
        if self.has_user(username):
            env_variables = {}
            user_data = self.usersDB.find_one({"username": username})
            if user_data and "env_variables" in user_data:
                env_variables = user_data["env_variables"]
            env_variables[variable] = value
            self.usersDB.update_one(
                {"username": username},
                {"$set": {"env_variables": env_variables}}
            )

    def get_env_variable(self, username, variable):
        if not self.has_user(username):
            return None

        user_data = self.usersDB.find_one({"username": username})
        if user_data and "env_variables" in user_data:
            env_variables = user_data["env_variables"]
            return env_variables.get(variable, None)
        return None

    def remove_env_variable(self, username, variable):
        if self.has_user(username):
            user_data = self.usersDB.find_one({"username": username})
            if user_data and "env_variables" in user_data:
                env_variables = user_data["env_variables"]
                if variable in env_variables:
                    del env_variables[variable]
                    self.usersDB.update_one(
                        {"username": username},
                        {"$set": {"env_variables": env_variables}}
                    )

    def get_all_env_variables(self, username):
        if not self.has_user(username):
            return None

        user_data = self.usersDB.find_one({"username": username})
        if user_data and "env_variables" in user_data:
            return user_data["env_variables"]
        return {}

    def get_root_user(self):
        sudo_user = self.usersDB.find_one({"sudo": True})
        if sudo_user:
            return sudo_user["username"]
        return None