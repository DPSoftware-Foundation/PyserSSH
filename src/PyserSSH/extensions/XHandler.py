"""
XHandler - eXternal Handler

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
import importlib
import inspect
import logging
import shlex
import sys
from typing import Dict, Optional, Any, List

from ..interactive import Send
from ..system import sysfunc

logger = logging.getLogger("PyserSSH.Ext.XHandler")

def are_permissions_met(permission_list, permission_require):
    return set(permission_require).issubset(set(permission_list))

class XHandler:
    def __init__(self, enablehelp=True, showusageonworng=True, sudo=True, sudo_prefix="!"):
        self.handlers = {}
        self.categories = {}
        self.enablehelp = enablehelp
        self.showUsageOnWrongFunc = showusageonworng
        self.serverself = None
        self.commandNotFoundFunc = None
        self.preSudoActionFunc = None
        self.sudo = sudo
        self.sudo_prefix = sudo_prefix

    def command(self, category=None, name=None, aliases=None, permissions: list = None):
        """
        Decorator to register a function as a command with optional category, name, aliases, and permissions.

        Parameters:
            category (str): The category under which the command falls (default: None).
            name (str): The name of the command (default: None).
            aliases (list): A list of command aliases (default: None).
            permissions (list): A list of permissions required to execute the command (default: None).

        Returns:
            function: The wrapped function.
        """
        logger.debug(f"Registering command: {name} in category: {category} with aliases: {aliases} and permissions: {permissions}")
        def decorator(func):
            nonlocal name, category
            if name is None:
                name = func.__name__
            command_name = name
            command_description = func.__doc__  # Read the docstring
            parameters = inspect.signature(func).parameters
            command_args = []
            has_args = False
            has_kwargs = False
            
            for param in list(parameters.values())[1:]:  # Exclude first parameter (client)
                if param.kind == inspect.Parameter.VAR_POSITIONAL:
                    has_args = True
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    has_kwargs = True
                elif param.default != inspect.Parameter.empty:  # Check if parameter has default value
                    if param.annotation == bool:
                        command_args.append(f"--{param.name}")
                    else:
                        command_args.append((f"{param.name}", param.default))
                else:
                    command_args.append(param.name)
            
            if category is None:
                category = 'No Category'
            if category not in self.categories:
                self.categories[category] = {}
            self.categories[category][command_name] = {
                'description': command_description.strip() if command_description else "",
                'args': command_args,
                "permissions": permissions,
                'has_args': has_args,
                'has_kwargs': has_kwargs
            }
            self.handlers[command_name] = func
            if aliases:
                for alias in aliases:
                    self.handlers[alias] = func
            return func

        logger.debug(f"Registered command: {name} in category: {category} with aliases: {aliases} and permissions: {permissions}")

        return decorator

    def call(self, client, command_string):
        tokens = shlex.split(command_string)
        if not tokens:
            return

        command_name = tokens[0]
        args = tokens[1:]
        authorized = True
        is_sudo = False

        if command_name == "help" and self.enablehelp:
            if args:
                Send(client, self.get_help_command_info(args[0]))
            else:
                Send(client, self.get_help_message())
                Send(client, "Type 'help <command>' for more info on a command.")
            return

        if self.sudo and command_name.startswith(self.sudo_prefix):
            is_sudo = True
            command_name = command_name[len(self.sudo_prefix):]

            if not command_name:
                Send(client, f"'{self.sudo_prefix}<command>' for command with root.")
                return

            # Permission check
            if self.serverself.accounts.is_user_has_sudo(client.get_name()):
                authorized = True
            elif self.preSudoActionFunc:
                authorized = self.preSudoActionFunc(client, command_name)
            else:
                authorized = True # if no root account and no pre sudo action function

        if not authorized:
            return

        # execute command here
        if command_name in self.handlers:
            command_func = self.handlers[command_name]
            command_info = self.get_command_info(command_name)
            if command_info and command_info.get('permissions'):
                if not is_sudo:
                    if not are_permissions_met(self.serverself.accounts.get_permissions(client.get_name()), command_info.get('permissions')):
                        Send(client, f"Permission denied. You do not have permission to execute '{command_name}'.")
                        return

            command_args = inspect.signature(command_func).parameters
            final_args = {}
            final_kwargs = {}
            i = 0

            while i < len(args):
                arg = args[i]
                if arg.startswith('-'):
                    arg_name = arg.lstrip('-')
                    if arg_name not in command_args:
                        if self.showUsageOnWrongFunc:
                            Send(client, self.get_help_command_info(command_name))
                        Send(client, f"Invalid flag '{arg_name}' for command '{command_name}'.")
                        return
                    if command_args[arg_name].annotation == bool:
                        final_args[arg_name] = True
                        i += 1
                    else:
                        if i + 1 < len(args):
                            final_args[arg_name] = args[i + 1]
                            i += 2
                        else:
                            if self.showUsageOnWrongFunc:
                                Send(client, self.get_help_command_info(command_name))
                            Send(client, f"Missing value for flag '{arg_name}' for command '{command_name}'.")
                            return
                else:
                    if command_info['has_args']:
                        final_args.setdefault('args', []).append(arg)
                    elif command_info['has_kwargs']:
                        final_kwargs[arg] = args[i + 1] if i + 1 < len(args) else None
                        i += 1
                    else:
                        if len(final_args) + 1 < len(command_args):
                            param = list(command_args.values())[len(final_args) + 1]
                            final_args[param.name] = arg
                        else:
                            if self.showUsageOnWrongFunc:
                                Send(client, self.get_help_command_info(command_name))
                            Send(client, f"Unexpected argument '{arg}' for command '{command_name}'.")
                            return
                    i += 1

            # Check for required positional arguments
            for param in list(command_args.values())[1:]:  # Skip client argument
                if param.name not in final_args and param.default == inspect.Parameter.empty:
                    if self.showUsageOnWrongFunc:
                        Send(client, self.get_help_command_info(command_name))
                    Send(client, f"Missing required argument '{param.name}' for command '{command_name}'")
                    return

            final_args_list = [final_args.get(param.name, param.default) for param in list(command_args.values())[1:]]

            if command_info['has_kwargs']:
                final_args_list.append(final_kwargs)

            return command_func(client, *final_args_list)
        else:
            if self.commandNotFoundFunc:
                self.commandNotFoundFunc(client, command_name)
                return
            else:
                Send(client, f"{command_name} not found")
                return

    def get_command_info(self, command_name):
        """
        Retrieves information about a specific command, including its description, arguments, and permissions.

        Parameters:
            command_name (str): The name of the command.

        Returns:
            dict: A dictionary containing command details such as name, description, args, and permissions.
        """
        found_command = None
        for category, commands in self.categories.items():
            if command_name in commands:
                found_command = commands[command_name]
                break
            else:
                for cmd, cmd_info in commands.items():
                    if 'aliases' in cmd_info and command_name in cmd_info['aliases']:
                        found_command = cmd_info
                        break
                if found_command:
                    break

        if found_command:
            return {
                'name': command_name,
                'description': found_command['description'].strip() if found_command['description'] else "",
                'args': found_command['args'],
                'category': category,
                'permissions': found_command['permissions'],
                'has_args': found_command['has_args'],
                'has_kwargs': found_command['has_kwargs']
            }

    def get_help_command_info(self, command):
        """
        Generates a detailed help message for a specific command.

        Parameters:
           command (str): The name of the command.

        Returns:
           str: The formatted help message for the command.
        """
        command_info = self.get_command_info(command)
        aliases = command_info.get('aliases', [])
        help_message = f"{command_info['name']}"
        if aliases:
            help_message += f" ({', '.join(aliases)})"
        help_message += "\n"
        help_message += f"{command_info['description']}\n"
        help_message += f"Usage: {command_info['name']}"
        for arg in command_info['args']:
            if isinstance(arg, tuple):
                if isinstance(arg[1], bool):
                    help_message += f" [--{arg[0]}]"
                else:
                    help_message += f" [-{arg[0]} {arg[1]}]"
            else:
                help_message += f" <{arg}>"
        if command_info['has_args']:
            help_message += " [<args>...]"
        if command_info['has_kwargs']:
            help_message += " [--<key>=<value>...]"
        return help_message

    def get_help_message(self):
        """
        Generates a general help message listing all categories and their associated commands.

        Returns:
            str: The formatted help message containing all commands and categories.
        """
        help_message = ""
        for category, commands in self.categories.items():
            help_message += f"{category}:\n"
            for command_name, command_info in commands.items():
                help_message += f"  {command_name}"
                if command_info['description']:
                    help_message += f" - {command_info['description']}"
                help_message += "\n"
        return help_message

    def get_all_commands(self):
        """
        Retrieves all registered commands, grouped by category.

        Returns:
            dict: A dictionary where each key is a category name and the value is a
                  dictionary of commands within that category.
        """
        all_commands = {}
        for category, commands in self.categories.items():
            all_commands[category] = commands
        return all_commands

class Division:
    """
    Represents a division (module/service) that can contain multiple commands.
    Similar to Flask blueprints or Discord cogs.
    """

    def __init__(self, name: str, description: str = "", permissions: List[str] = None, category: str = None):
        """
        Initialize a division.

        Parameters:
            name (str): The name of the division
            description (str): Description of the division
            permissions (list): Required permissions for the entire division
            category (str): Category this division belongs to
        """
        self.name = name
        self.description = description
        self.permissions = permissions or []
        self.category = category or "General"
        self.commands = {}
        self.enabled = True
        self.handler = None  # Reference to XHandler

    def command(self, name: str = None, aliases: List[str] = None, permissions: List[str] = None):
        """
        Decorator to register a command within this division.

        Parameters:
            name (str): Command name (defaults to function name)
            aliases (list): Command aliases
            permissions (list): Additional permissions for this specific command
        """
        logger.debug(f"Registering command '{name}' in division '{self.name}' with aliases {aliases} and permissions {permissions}")
        def decorator(func):
            nonlocal name
            if name is None:
                name = func.__name__

            # Combine division permissions with command-specific permissions
            combined_permissions = self.permissions.copy()
            if permissions:
                combined_permissions.extend(permissions)

            command_info = {
                'function': func,
                'name': name,
                'aliases': aliases or [],
                'permissions': combined_permissions,
                'division': self.name,
                'description': func.__doc__
            }

            self.commands[name] = command_info

            # If division is already registered with a handler, register the command
            if self.handler and self.enabled:
                self._register_command_to_handler(command_info)

            return func

        logger.debug(f"Registered command '{name}' in division '{self.name}' with aliases {aliases} and permissions {permissions}")

        return decorator

    def _register_command_to_handler(self, command_info):
        """Register a single command to the XHandler"""
        if self.handler:
            # Use the XHandler's command decorator to register
            self.handler.command(
                category=self.category,
                name=command_info['name'],
                aliases=command_info['aliases'],
                permissions=command_info['permissions']
            )(command_info['function'])

    def _unregister_command_from_handler(self, command_name):
        """Unregister a single command from the XHandler"""
        if self.handler:
            # Remove from handlers
            if command_name in self.handler.handlers:
                del self.handler.handlers[command_name]

            # Remove from categories
            for category, commands in self.handler.categories.items():
                if command_name in commands:
                    del commands[command_name]
                    break

class DivisionHandler:
    """
    Manages divisions (modules/services) that contain commands.
    Provides functionality to register, enable, disable, and unregister divisions.
    """

    def __init__(self, xhandler):
        """
        Initialize the division handler.

        Parameters:
            xhandler (XHandler): The main command handler instance
        """
        self.xhandler = xhandler
        self.divisions: Dict[str, Division] = {}
        self.module_cache: Dict[str, Any] = {}

    def create_division(self, name: str, description: str = "", permissions: List[str] = None,
                        category: str = None) -> Division:
        """
        Create a new division.

        Parameters:
            name (str): Division name
            description (str): Division description
            permissions (list): Required permissions for the division
            category (str): Category for the division's commands

        Returns:
            Division: The created division instance
        """
        division = Division(name, description, permissions, category)
        division.handler = self.xhandler
        return division

    def register_division(self, division: Division) -> bool:
        """
        Register a division with the handler.

        Parameters:
            division (Division): The division to register

        Returns:
            bool: True if successful, False if division already exists
        """
        if division.name in self.divisions:
            return False

        logger.info(f"Registering division: {division.name}")

        self.divisions[division.name] = division
        division.handler = self.xhandler

        # Register all commands if division is enabled
        if division.enabled:
            self._register_division_commands(division)

        logger.info(f"Registered division: {division.name} with {len(division.commands)} commands")

        return True

    def register_division_from_module(self, module_path: str, division_name: str = None) -> bool:
        """
        Register a division from a Python module file.

        Parameters:
            module_path (str): Path to the Python module (e.g., "modules.admin")
            division_name (str): Name for the division (defaults to module name)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Loading division from module: {module_path}")

            package_path = ".".join(module_path.split(".")[:-1])
            # Import or reload the module
            if package_path in sys.modules:
                module = importlib.reload(sys.modules[package_path])
            else:
                module = importlib.import_module(package_path)

            self.module_cache[package_path] = [module, module_path.split(".")[-1]]

            # Look for a division instance or setup function
            division = getattr(module, module_path.split(".")[-1])

            if division and isinstance(division, Division):
                if division_name:
                    division.name = division_name
                return self.register_division(division)
        except Exception as e:
            logger.error(f"Failed to load division from {module_path}: {e}")

        return False

    def unregister_division(self, division_name: str) -> bool:
        """
        Unregister a division and remove all its commands.

        Parameters:
            division_name (str): Name of the division to unregister

        Returns:
            bool: True if successful, False if division not found
        """
        if division_name not in self.divisions:
            return False

        logger.info(f"Unregistering division: {division_name}")

        division = self.divisions[division_name]
        self._unregister_division_commands(division)
        del self.divisions[division_name]

        logger.info(f"Unregistered division: {division_name}")

        return True

    def enable_division(self, division_name: str) -> bool:
        """
        Enable a division and register its commands.

        Parameters:
            division_name (str): Name of the division to enable

        Returns:
            bool: True if successful, False if division not found
        """
        if division_name not in self.divisions:
            return False

        division = self.divisions[division_name]
        if not division.enabled:
            division.enabled = True
            self._register_division_commands(division)

        return True

    def disable_division(self, division_name: str) -> bool:
        """
        Disable a division and unregister its commands.

        Parameters:
            division_name (str): Name of the division to disable

        Returns:
            bool: True if successful, False if division not found
        """
        if division_name not in self.divisions:
            return False

        division = self.divisions[division_name]
        if division.enabled:
            division.enabled = False
            self._unregister_division_commands(division)

        return True

    def reload_division(self, division_name: str, module_path: str = None) -> bool:
        """
        Reload a division from its module.

        Parameters:
            division_name (str): Name of the division to reload

        Returns:
            bool: True if successful, False otherwise
        """
        if division_name not in self.divisions:
            return False

        logger.info(f"Reloading division: {division_name}")

        # Find the module path
        varname = "div"
        if not module_path:
            # Try to find it in cache
            for path, module in self.module_cache.items():
                if hasattr(module[0], module[1]) and getattr(module[0], module[1]).name == division_name:
                    module_path = path
                    varname = module[1]
                    break

        if not module_path and not varname:
            return False

        # Unregister current division
        self.unregister_division(division_name)

        # Register from module again
        return self.register_division_from_module(module_path+"."+varname, division_name)

    def get_division_info(self, division_name: str) -> Optional[Dict]:
        """
        Get information about a division.

        Parameters:
            division_name (str): Name of the division

        Returns:
            dict: Division information or None if not found
        """
        if division_name not in self.divisions:
            return None

        division = self.divisions[division_name]
        return {
            'name': division.name,
            'description': division.description,
            'permissions': division.permissions,
            'category': division.category,
            'enabled': division.enabled,
            'commands': list(division.commands.keys()),
            'command_count': len(division.commands)
        }

    def list_divisions(self) -> Dict[str, Dict]:
        """
        List all registered divisions.

        Returns:
            dict: Dictionary of division information
        """
        return {name: self.get_division_info(name) for name in self.divisions.keys()}

    def _register_division_commands(self, division: Division):
        """Register all commands from a division to the XHandler"""
        for command_info in division.commands.values():
            division._register_command_to_handler(command_info)

    def _unregister_division_commands(self, division: Division):
        """Unregister all commands from a division from the XHandler"""
        for command_name in division.commands.keys():
            division._unregister_command_from_handler(command_name)
            # Also remove aliases
            command_info = division.commands[command_name]
            for alias in command_info.get('aliases', []):
                division._unregister_command_from_handler(alias)