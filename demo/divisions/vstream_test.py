import code
import subprocess
import sys
import threading

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