import code
import subprocess
import sys
import threading
import time
import requests
import rich
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
from rich.markdown import Markdown
from rich.live import Live
from rich.syntax import Syntax
import asciichartpy as acp
from markdownify import markdownify
import numpy as np

from PyserSSH.extensions.XHandler import Division
from PyserSSH.extensions.virtualSTD import StreamSTD
from PyserSSH.system.clientype import Client

div = Division("virtualSTD", "Test command for virtualSTD extension module", category="Test Function (VirtualSTD)")

@div.command(name="repl", permissions=["root"])
def xh_repl(client: Client):
    # Start a REPL session
    original_stdin = sys.stdin
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    stream = StreamSTD(client)

    sys.stdin = stream.stdin
    sys.stdout = stream.stdout
    sys.stderr = stream.stderr

    try:
        # Start the interactive interpreter
        code.interact(banner="--- Remote REPL Connected ---", local=locals())
    except Exception as e:
        # Restore original streams
        sys.stdin = original_stdin
        sys.stdout = original_stdout
        sys.stderr = original_stderr
    finally:
        # Restore original streams
        sys.stdin = original_stdin
        sys.stdout = original_stdout
        sys.stderr = original_stderr

@div.command(name="sysshell", permissions=["root"])
def xh_sysshell(client: Client):
    stream = StreamSTD(client)

    proc = subprocess.Popen(
        ["cmd"],  # or ["bash"] on Linux
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,  # treat as text, not raw bytes
        bufsize=1  # line-buffered
    )

    def forward_output(src, dest):
        for line in iter(src.readline, ''):
            dest.write(line)
        src.close()

    threading.Thread(target=forward_output, args=(proc.stdout, stream.stdout), daemon=True).start()
    threading.Thread(target=forward_output, args=(proc.stderr, stream.stderr), daemon=True).start()

    # Forward input
    def forward_input(src, dest):
        for line in iter(src.readline, ''):
            dest.write(line)
        dest.close()

    threading.Thread(target=forward_input, args=(stream.stdin, proc.stdin), daemon=True).start()

    proc.wait()
    stream.deactivate()

@div.command(name="streamtest")
def xh_streamtest(client: Client):
    # Create your virtual STD streams
    stream = StreamSTD(client)

    # stdin test → read 5 chars
    client.sendln(">>> Testing stdin.read(5)")
    data = stream.stdin.read(5)
    client.sendln(f"stdin returned: {repr(data)}")

    # readline test
    client.sendln("\n>>> Testing stdin.readline() (enter a line and press Enter)")
    line = stream.stdin.readline()
    client.sendln(f"stdin.readline returned: {repr(line)}")

    # stdout test
    client.sendln("\n>>> Testing stdout.write()")
    stream.stdout.write("Hello from stdout!\n")
    stream.stdout.flush()

    # stderr test
    client.sendln("\n>>> Testing stderr.write()")
    stream.stderr.write("This is an error message!\n")
    stream.stderr.flush()

    # cleanup
    stream.deactivate()
    client.sendln("\n>>> Stream deactivated")

@div.command(name="rich")
def xh_rich(client: Client):
    # Create your virtual STD streams
    stream = StreamSTD(client)

    width, height = client.get_terminal_size()

    console = rich.console.Console(
        file=stream.stdout,
        force_terminal=True,
        color_system="truecolor",
        width=width,
        height=height
    )

    console.print("Rich with PyserSSH via StreamSTD! 👨‍💻")

    console.print("[bold red]Error:[/] Something went wrong!")
    console.print("[green]Success![/] Operation completed.")
    console.print("[cyan]Hello[/], [magenta]world[/]!")

    console.print("This is [bold blue]blue bold text[/].")
    console.print("This is [yellow on red]warning background[/].")

    table = Table(title="Humvee Loadout")

    table.add_column("Part", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    table.add_column("Weight", justify="right", style="green")

    table.add_row("Armor", "Level 3 Kevlar plating", "250kg")
    table.add_row("Engine", "Turbo-diesel V8", "400kg")
    table.add_row("Weapons", "M2 Browning .50 cal", "200kg")

    console.print(table)

    console.print(Panel.fit("[bold green]Mission Status: ONLINE[/]"))
    console.print(Panel("[yellow]Warning: Enemy UAV Detected![/]", title="⚠ ALERT"))

    for step in track(range(10), description="Deploying Humvee...", console=console):
        time.sleep(0.3)

    md = """
# Mission Briefing
- **Objective:** Secure the area
- **Assets:** 1x Humvee, 2x Rifle squads
- **Risk Level:** :fire: High

Proceed with caution.
    """
    console.print(Markdown(md))

    table = Table()
    table.add_column("Unit")
    table.add_column("Status")

    with Live(table, refresh_per_second=4, console=console) as live:
        for i in range(5):
            table.add_row(f"Squad {i + 1}", "Moving")
            time.sleep(1)

    code = """
def tactical_scan(target):
    if target == "enemy":
        return "Engage"
    return "Standby"
    """

    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)

    with console.status("Please wait - solving global problems...", spinner="material"):
        time.sleep(5.0)  # Simulates a long process

    console.print("Mission Status: [bold green]Success[/] ✅")
    console.print("Vehicle: Humvee M1151 🪖🚙💥")
    console.print("Air Support: Apache AH-64 🚁🔥")

    def simple_sine(s):
        return np.sin(2 * np.pi * (0.1 * s))

    def get_panel(data):
        return Panel(acp.plot(data), expand=False, title="~~ [bold][yellow]waves[/bold][/yellow] ~~")

    with Live(refresh_per_second=24, console=console) as live:
        d = []
        for i in range(240):
            time.sleep(1/24)
            d.append(simple_sine(i))
            # pass only X latest
            live.update(get_panel(d[-50:]))

    console.print("Demo success! 👨‍💻✔️")

    # cleanup
    del console
    stream.deactivate()

@div.command(name="vieweb2")
def xh_rich_vieweb(client: Client, URL):
    # Create your virtual STD streams
    stream = StreamSTD(client)

    width, height = client.get_terminal_size()

    console = rich.console.Console(
        file=stream.stdout,
        force_terminal=True,
        color_system="truecolor",
        width=width,
        height=height
    )

    status = console.status(f"Requesting to {URL}", spinner="material")
    status.start()

    req = requests.get(URL, timeout=10)
    status.update("Convert HTML to Markdown")
    markdown = markdownify(req.content)
    status.update("Convert Markdown to Rich format")
    contentOut = Markdown(markdown)
    status.update("Creating panel...")
    contentOut = Panel(contentOut, title=URL, title_align="left")
    status.stop()

    console.print(contentOut)

    # cleanup
    del console
    stream.deactivate()

