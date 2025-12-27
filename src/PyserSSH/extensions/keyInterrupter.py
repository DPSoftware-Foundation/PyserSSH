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
from threading import Thread, Event
from ..system.clientype import Client


class attachInterrupt:
    def __init__(self, client: Client, on_interrupt=None):
        self.client = client
        self.on_interrupt = on_interrupt

        self._running = Event()
        self._thread: Thread | None = None

        self.start()

    def _wait_thread(self):
        try:
            while self._running.is_set():
                try:
                    byte = self.client.channel.recv(1)
                except EOFError:
                    break
                except Exception as exc:
                    break

                if not byte:
                    break

                if byte == b"\x03":
                    self.client.key_interrupted = True

                    if self.on_interrupt is not None:
                        try:
                            self.on_interrupt()
                        except Exception as exc:
                            pass
                    else:
                        raise KeyboardInterrupt()

                    break
        finally:
            self._running.clear()

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return

        self._running.set()
        self._thread = Thread(target=self._wait_thread, daemon=True)
        self._thread.start()

    def stop(self, join: bool = True, timeout: float | None = None):
        self._running.clear()

        if self._thread is not None and self._thread.is_alive():
            if join:
                self._thread.join(timeout)