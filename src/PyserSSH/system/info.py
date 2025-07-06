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

version = "5.2"

system_banner = (
    f"\033[36mPyserSSH V{version} \033[0m"
    #"\033[33m!!Warning!! This is Testing Version of PyserSSH \033[0m\n"
    #"\033[35mUse Putty and WinSCP (SFTP) for best experience \033[0m"
)

def Flag_TH(returnlist=False):


    Flags = [
        "\n",
        f"\033[31m  =======   ==    ==   ======   =======  ======     ======    ======   ==    ==  \033[0m\n",
        f"\033[37m  ==    ==   ==  ==   ==        ===      ==   ==   ==        ==        ==    ==  \033[0m\n",
        f"\033[34m  =======     ====    =======   =======  ======    =======   =======   ========  \033[0m\n",
        f"\033[34m  =====        ==      =====    ====     === ==      =====     =====   ========  \033[0m\n",
        f"\033[37m  ==           ==          ===  ===      ==   ==        ===       ===  ==    ==  \033[0m\n",
        f"\033[31m  ==           ==     ======    =======  ==    ==  ======    ======    ==    ==  \033[0m\n",
        "                 Made by \033[33mD\033[38;2;255;126;1mP\033[38;2;43;205;150mSoftware\033[0m \033[38;2;204;208;43mFoundation\033[0m from Thailand\n",
        "\n"
    ]

    if returnlist:
        return Flags
    else:
        exporttext = ""

        for line in Flags:
            exporttext += line
        return exporttext