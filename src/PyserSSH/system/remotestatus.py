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
import logging
import os
import socket
import threading
import time
import sys
import psutil
from datetime import datetime
import platform

from ..interactive import Send
from .info import __version__

if platform.system() == "Windows":
    import ctypes

logger = logging.getLogger("PyserSSH")

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_uint),
        ('dwTime', ctypes.c_uint),
    ]

def get_idle_time():
    if platform.system() == "Windows":
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
        millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0
    elif platform.system() == "Linux":
        with open('/proc/stat') as f:
            for line in f:
                if line.startswith('btime'):
                    boot_time = float(line.split()[1])
                    break

        with open('/proc/uptime') as f:
            uptime_seconds = float(f.readline().split()[0])
            idle_time_seconds = uptime_seconds - (time.time() - boot_time)

        return idle_time_seconds
    else:
        return time.time() - psutil.boot_time()

def get_system_uptime():
    if platform.system() == "Windows":
        kernel32 = ctypes.windll.kernel32
        uptime = kernel32.GetTickCount64() / 1000.0
        return uptime
    elif platform.system() == "Linux":
        with open('/proc/uptime') as f:
            uptime_seconds = float(f.readline().split()[0])

        return uptime_seconds
    else:
        return 0

def get_folder_size(folder_path):
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def get_folder_usage(folder_path, limit_size):
    folder_size = get_folder_size(folder_path)
    used_size = folder_size
    free_size = limit_size - folder_size
    percent_used = (folder_size / limit_size) * 100 if limit_size > 0 else 0
    return used_size, free_size, limit_size, percent_used

librarypath = os.path.abspath(__file__).replace("\\", "/").split("/system/remotestatus.py")[0]

def remotestatus(serverself, channel, oneloop=False):
    try:
        while True:
            # Get RAM information
            mem = psutil.virtual_memory()

            ramoutput = f"""\
==> /proc/meminfo <==
MemTotal:        {mem.total // 1024} kB
MemFree:         {mem.free // 1024} kB
MemAvailable:    {mem.available // 1024} kB
Buffers:         0 kB
Cached:          0 kB
SwapCached:      0 kB
Active:          0 kB
Inactive:        0 kB"""

            cpu_data = []

            #currentprocess = psutil.Process().cpu_times()

            #cpu_data.append(["cpu", int(currentprocess.user), 0, int(currentprocess.system), 0, 0, 0, 0])

            #if platform.system() == "Linux":
            io_counters = psutil.disk_io_counters(perdisk=False)
            io_wait_time = io_counters.read_time + io_counters.write_time
            for idx, cpu_time in enumerate(psutil.cpu_times(True), start=-1):
                if idx == -1:
                    cpu_data.append(["cpu", int(cpu_time.user), 0, int(cpu_time.system), int(cpu_time.idle), io_wait_time, int(cpu_time.interrupt), 0, 0, 0, 0])
                else:
                    cpu_data.append(
                        [f"cpu{idx}", int(cpu_time.user), 0, int(cpu_time.system), int(cpu_time.idle), io_wait_time, int(cpu_time.interrupt), 0, 0, 0, 0])

            # Calculate maximum widths for formatting (optional)
            max_widths = [max(len(str(row[i])) for row in cpu_data) for i in range(len(cpu_data[0]))]

            disk_data = [
                ["Filesystem", "1K-blocks", "Used", "Available", "Use%", "Mounted on"],
            ]

            for disk in psutil.disk_partitions(True):
                usage = psutil.disk_usage(disk.device)
                mountpoint = disk.mountpoint

                if mountpoint == "C:\\":
                    mountpoint = "/"

                disk_data.append(
                    [disk.device.replace('\\', '/'), usage.total // 1024, usage.used // 1024, usage.free // 1024, f"{int(usage.percent)}%",
                     mountpoint])

            libused, libfree, libtotal, libpercent = get_folder_usage(librarypath, 1024*1024)

            disk_data.append(["/dev/pyserssh", libtotal // 1024, libused // 1024, libfree // 1024, f"{int(libpercent)}%", "/python/pyserssh"])

            max_widths3 = [max(len(str(row[i])) for row in disk_data) for i in range(len(disk_data[0]))]

            """
            network_data = [
                ["Inter-|", "   Receive", "", "", "", "", "", "", "         |", "   Transmit" "", "", "", "", "", "", "", ""],
                [" face |", "bytes", "packets", "errs", "drop", "fifo", "frame", "compressed", "multicast|", "bytes", "packets",
                 "errs", "drop", "fifo", "colls", "carrier", "compressed"]
            ]

            for interface, stats in psutil.net_io_counters(pernic=True).items():
                network_data.append(
                    [f"{interface}:", stats.bytes_recv, stats.packets_recv, stats.errin, stats.dropin, 0, 0, 0, 0,
                     stats.bytes_sent, stats.packets_sent, stats.errout, stats.dropout, 0, 0, 0, 0])

            max_widths2 = [max(len(str(row[i])) for row in network_data) for i in range(len(network_data[0]))]
            
            protocol_names = {
                (socket.AF_INET, socket.SOCK_STREAM): 'tcp',
                (socket.AF_INET, socket.SOCK_DGRAM): 'udp',
                (socket.AF_INET6, socket.SOCK_STREAM): 'tcp6',
                (socket.AF_INET6, socket.SOCK_DGRAM): 'udp6',
            }

            netstat_data = [
                ["Proto", "Recv-Q", "Send-Q", "Local Address", "Foreign Address", "State", "PID/Program name"],
            ]

            for conn in psutil.net_connections("all"):
                if conn.status in ['TIME_WAIT', 'CLOSING', "NONE"]:
                    continue

                laddr_ip, laddr_port = conn.laddr if conn.laddr else ('', '')
                raddr_ip, raddr_port = conn.raddr if conn.raddr else ('', '')

                protocol = protocol_names.get((conn.family, conn.type), 'Unknown')

                try:
                    process = psutil.Process(conn.pid)
                    processname = f"{conn.pid}/{process.name()}"
                except psutil.NoSuchProcess:
                    processname = conn.pid

                netstat_data.append(
                    [protocol, 0, 0, f"{laddr_ip}:{laddr_port}", f"{raddr_ip}:{raddr_port}", conn.status, processname])

            max_widths4 = [max(len(str(row[i])) for row in netstat_data) for i in range(len(netstat_data[0]))]
            """

            who_data = []

            for idx, client in enumerate(serverself.client_handlers.values()):
                last_login_date = datetime.utcfromtimestamp(client.last_login_time).strftime('%Y-%m-%d %H:%M')
                who_data.append([client.current_user, f"pty/{idx}", last_login_date, f"({client.peername[0]})"])

            max_widths5 = [max(len(str(row[i])) for row in who_data) for i in range(len(who_data[0]))]

            Send(channel, ramoutput, directchannel=True)
            Send(channel, "", directchannel=True)

            # only support for CPU status current python process
            Send(channel, "==> /proc/stat <==", directchannel=True)
            for row in cpu_data:
                Send(channel, " ".join("{:<{width}}".format(item, width=max_widths[i]) for i, item in enumerate(row)), directchannel=True)

            Send(channel, "", directchannel=True)
            Send(channel, "==> /proc/version <==", directchannel=True)
            Send(channel, f"PyserSSH v{__version__} run on {platform.platform()} {platform.machine()} {platform.architecture()[0]} with python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} {sys.version_info.releaselevel} {platform.python_build()[0]} {platform.python_build()[1]} {platform.python_compiler()} {platform.python_implementation()} {platform.python_revision()}", directchannel=True)

            Send(channel, "", directchannel=True)
            Send(channel, "==> /proc/uptime <==", directchannel=True)
            Send(channel, f"{get_system_uptime()} {get_idle_time()}", directchannel=True)

            Send(channel, "", directchannel=True)
            Send(channel, "==> /proc/sys/kernel/hostname <==", directchannel=True)
            Send(channel, platform.node(), directchannel=True)

            # fixing later for network status
            #Send(channel, "", directchannel=True)
            #Send(channel, "==> /proc/net/dev <==", directchannel=True)
            #for row in network_data:
            #    Send(channel, " ".join("{:<{width}}".format(item, width=max_widths2[i]) for i, item in enumerate(row)), directchannel=True)

            Send(channel, "", directchannel=True)
            Send(channel, "==> /proc/df <==", directchannel=True)
            for row in disk_data:
                Send(channel, " ".join("{:<{width}}".format(item, width=max_widths3[i]) for i, item in enumerate(row)), directchannel=True)

            # fixing later for network status
            #Send(channel, "", directchannel=True)
            #Send(channel, "==> /proc/netstat <==", directchannel=True)
            #for row in netstat_data:
            #    Send(channel, " ".join("{:<{width}}".format(item, width=max_widths4[i]) for i, item in enumerate(row)), directchannel=True)

            Send(channel, "", directchannel=True)
            Send(channel, "==> /proc/who <==", directchannel=True)
            for row in who_data:
                Send(channel, " ".join("{:<{width}}".format(item, width=max_widths5[i]) for i, item in enumerate(row)), directchannel=True)

            Send(channel, "", directchannel=True)
            Send(channel, "==> /proc/end <==", directchannel=True)
            Send(channel, "##Moba##", directchannel=True)

            if oneloop:
                break

            time.sleep(1)
    except socket.error:
        pass
    except Exception as e:
        logger.error(e)

def startremotestatus(serverself, channel):
    t = threading.Thread(target=remotestatus, args=(serverself, channel), daemon=True)
    t.start()