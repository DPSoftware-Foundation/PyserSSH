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

import inspect
import shlex

from ..interactive import Send

class XHandler:
    def __init__(self, enablehelp=True, showusageonworng=True):
        self.handlers = {}
        self.categories = {}
        self.enablehelp = enablehelp
        self.showusageonworng = showusageonworng

        self.commandnotfound = None

    def command(self, category=None, name=None, aliases=None):
        def decorator(func):
            nonlocal name, category
            if name is None:
                name = func.__name__
            command_name = name
            command_description = func.__doc__  # Read the docstring
            parameters = inspect.signature(func).parameters
            command_args = []
            for param in list(parameters.values())[1:]:  # Exclude first parameter (client)
                if param.default != inspect.Parameter.empty:  # Check if parameter has default value
                    if param.annotation == bool:
                        command_args.append(f"-{param.name}")
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
                'args': command_args
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
                command_args = inspect.signature(command_func).parameters
                if len(args) % 2 != 0 and not args[0].startswith("--"):
                    if self.showusageonworng:
                        Send(client, self.get_help_command_info(command_name))
                    else:
                        Send(client, f"Invalid number of arguments for command '{command_name}'.")
                    return
                # Parse arguments
                final_args = {}
                for i in range(0, len(args), 2):
                    if args[i].startswith("--"):
                        arg_name = args[i].lstrip('--')
                        if arg_name not in command_args:
                            if self.showusageonworng:
                                Send(client, self.get_help_command_info(command_name))
                            else:
                                Send(client, f"Invalid flag '{arg_name}' for command '{command_name}'.")
                            return
                        try:
                            args[i + 1]
                        except:
                            pass
                        else:
                            if self.showusageonworng:
                                Send(client, self.get_help_command_info(command_name))
                            else:
                                Send(client, f"value '{args[i + 1]}' not available for '{arg_name}' flag for command '{command_name}'.")
                            return
                        final_args[arg_name] = True
                    else:
                        arg_name = args[i].lstrip('-')
                        if arg_name not in command_args:
                            if self.showusageonworng:
                                Send(client, self.get_help_command_info(command_name))
                            else:
                                Send(client, f"Invalid argument '{arg_name}' for command '{command_name}'.")
                            return
                        arg_value = args[i + 1]
                        final_args[arg_name] = arg_value
                # Match parsed arguments to function parameters
                final_args_list = []
                for param in list(command_args.values())[1:]:  # Skip client argument
                    if param.name in final_args:
                        final_args_list.append(final_args[param.name])
                    elif param.default != inspect.Parameter.empty:
                        final_args_list.append(param.default)
                    else:
                        if self.showusageonworng:
                            Send(client, self.get_help_command_info(command_name))
                        else:
                            Send(client, f"Missing required argument '{param.name}' for command '{command_name}'")
                        return
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
                'category': category
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