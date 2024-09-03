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

import inspect
import shlex

from ..interactive import Send

def are_permissions_met(permission_list, permission_require):
    return set(permission_require).issubset(set(permission_list))

class XHandler:
    def __init__(self, enablehelp=True, showusageonworng=True):
        self.handlers = {}
        self.categories = {}
        self.enablehelp = enablehelp
        self.showusageonworng = showusageonworng
        self.serverself = None
        self.commandnotfound = None

    def command(self, category=None, name=None, aliases=None, permissions: list = None):
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

        return decorator

    def call(self, client, command_string):
        tokens = shlex.split(command_string)
        command_name = tokens[0]
        args = tokens[1:]
        
        if command_name == "help" and self.enablehelp:
            if args:
                Send(client, self.get_help_command_info(args[0]))
            else:
                Send(client, self.get_help_message())
                Send(client, "Type 'help <command>' for more info on a command.")
        else:
            if command_name in self.handlers:
                command_func = self.handlers[command_name]
                command_info = self.get_command_info(command_name)
                if command_info and command_info.get('permissions'):
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
                            if self.showusageonworng:
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
                                if self.showusageonworng:
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
                                if self.showusageonworng:
                                    Send(client, self.get_help_command_info(command_name))
                                Send(client, f"Unexpected argument '{arg}' for command '{command_name}'.")
                                return
                        i += 1

                # Check for required positional arguments
                for param in list(command_args.values())[1:]:  # Skip client argument
                    if param.name not in final_args and param.default == inspect.Parameter.empty:
                        if self.showusageonworng:
                            Send(client, self.get_help_command_info(command_name))
                        Send(client, f"Missing required argument '{param.name}' for command '{command_name}'")
                        return

                final_args_list = [final_args.get(param.name, param.default) for param in list(command_args.values())[1:]]

                if command_info['has_kwargs']:
                    final_args_list.append(final_kwargs)

                return command_func(client, *final_args_list)
            else:
                if self.commandnotfound:
                    self.commandnotfound(client, command_name)
                    return
                else:
                    Send(client, f"{command_name} not found")
                    return

    def get_command_info(self, command_name):
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
        all_commands = {}
        for category, commands in self.categories.items():
            all_commands[category] = commands
        return all_commands

