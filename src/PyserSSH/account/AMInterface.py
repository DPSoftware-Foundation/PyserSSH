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
import time
from abc import ABC, abstractmethod

class IAccountManager(ABC):
    @abstractmethod
    def validate_credentials(self, username, password=None, public_key=None) -> bool:
        pass

    @abstractmethod
    def has_user(self, username) -> bool:
        pass

    @abstractmethod
    def has_sudo_user(self) -> bool:
        pass

    @abstractmethod
    def is_user_has_sudo(self, username) -> bool:
        pass

    @abstractmethod
    def get_prompt(self, username) -> list:
        pass

    @abstractmethod
    def get_allowed_auths(self, username) -> str:
        pass

    @abstractmethod
    def get_permissions(self, username) -> list:
        pass

    @abstractmethod
    def get_user_sftp_allow(self, username) -> bool:
        pass

    @abstractmethod
    def get_user_sftp_readonly(self, username) -> bool:
        pass

    @abstractmethod
    def get_user_sftp_root_path(self, username) -> str:
        pass

    @abstractmethod
    def get_user_enable_inputsystem(self, username) -> bool:
        pass

    @abstractmethod
    def get_user_enable_inputsystem_echo(self, username) -> bool:
        pass

    @abstractmethod
    def get_banner(self, username) -> str:
        pass

    @abstractmethod
    def get_user_timeout(self, username) -> int:
        pass

    @abstractmethod
    def get_user_last_login(self, username) -> dict:
        pass

    @abstractmethod
    def get_history(self, username, index, getall=False):
        pass

    @abstractmethod
    def get_lastcommand(self, username) -> str:
        pass

    @abstractmethod
    def get_env_variable(self, username, variable) -> str:
        pass

    @abstractmethod
    def get_all_env_variables(self, username) -> dict:
        pass

    @abstractmethod
    def get_root_user(self) -> str:
        pass

    @abstractmethod
    def list_users(self) -> list:
        pass

    @abstractmethod
    def add_account(self, username, password=None, public_key=None, interactive_auth=False, permissions:list=None, sudo=False) -> None:
        pass

    @abstractmethod
    def remove_account(self, username) -> None:
        pass

    @abstractmethod
    def remove_env_variable(self, username, variable) -> None:
        pass


    @abstractmethod
    def change_password(self, username, new_password) -> None:
        pass

    @abstractmethod
    def set_permissions(self, username, new_permissions) -> None:
        pass

    @abstractmethod
    def set_prompt(self, username) -> None:
        pass

    @abstractmethod
    def set_user_sftp_allow(self, username, allow=True) -> None:
        pass

    @abstractmethod
    def set_user_sftp_readonly(self, username, readonly=False) -> None:
        pass

    @abstractmethod
    def set_user_sftp_root_path(self, username, path="/") -> None:
        pass

    @abstractmethod
    def set_user_enable_inputsystem(self, username, enable=True) -> None:
        pass

    @abstractmethod
    def set_user_enable_inputsystem_echo(self, username, echo=True) -> None:
        pass

    @abstractmethod
    def set_banner(self, username, banner) -> None:
        pass

    @abstractmethod
    def set_user_timeout(self, username, timeout=None) -> None:
        pass

    @abstractmethod
    def set_user_last_login(self, username, ip, timelogin=time.time()) -> None:
        pass

    @abstractmethod
    def add_history(self, username, command) -> None:
        pass

    @abstractmethod
    def clear_history(self, username) -> None:
        pass

    @abstractmethod
    def set_env_variable(self, username, variable, value) -> None:
        pass
