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

import socket
import threading
import brotli
import numpy as np
import cv2
from PIL import ImageGrab
import struct
import queue
import pickle
import mouse
import keyboard
import logging

from ..system.clientype import Client

logger = logging.getLogger("RemoDeskSSH")

class Protocol:
    def __init__(self, server):
        self.listclient = []
        self.first = True
        self.running = False
        self.server = server
        self.buffer = queue.Queue(maxsize=10)

    def _handle_client(self):
        try:
            while self.running:
                data2send = self.buffer.get()

                for iclient in self.listclient:
                    try:
                        iclient[2].sendall(data2send)
                    except Exception as e:
                        iclient[2].close()
                        self.listclient.remove(iclient)

                if not self.listclient:
                    self.running = False
                    self.first = True
                    logger.info("No clients connected. Server is standby")
                    break

        except socket.error:
            pass
        except Exception as e:
            logger.error(f"Error in handle_client: {e}")

    def _handle_client_commands(self, client, id):
        try:
            while True:
                client_socket = client.get_subchannel(id)

                try:
                    # Receive the length of the data
                    data_length = self._receive_exact(client_socket, 4)
                    if not data_length:
                        break

                    commandmetadata = struct.unpack('!I', data_length)
                    command_data = self._receive_exact(client_socket, commandmetadata[0])
                    command = pickle.loads(command_data)

                    if command:
                        self.handle_commands(command, client)

                except socket.error:
                    break
        except Exception as e:
            logger.error(f"Error in handle_client_commands: {e}")

    def handle_commands(self, command, client):
        pass

    def _receive_exact(self, socket, n):
        """Helper function to receive exactly n bytes."""
        data = b''
        while len(data) < n:
            packet = socket.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def init(self, client):
        pass

    def handle_new_client(self, client: Client, directchannel=None):
        if directchannel:
            id = directchannel.get_id()
            channel = directchannel
        else:
            logger.info("waiting remote channel")
            id, channel = client.open_new_subchannel(5)
            if id == None or channel == None:
                logger.info("client is not connect in 5 sec")
                return

        self.listclient.append([client, id, channel])

        if self.first:
            self.running = True
            handle_client_thread = threading.Thread(target=self._handle_client, daemon=True)
            handle_client_thread.start()

            self.init(client)

            self.first = False

        command_thread = threading.Thread(target=self._handle_client_commands, args=(client, id), daemon=True)
        command_thread.start()

class RemoDesk(Protocol):
    def __init__(self, server=None, quality=50, compression=50, format="jpeg", resolution: set[int, int] = None, activity_threshold=None, second_compress=True):
        """
        Args:
            server: ssh server
            quality: quality of remote
            compression: percent of compression 0-100 %
            format: jpeg, webp, avif
            resolution: resolution of remote
        """

        super().__init__(server)

        self.quality = quality
        self.compression = compression
        self.format = format
        self.resolution = resolution
        self.threshold = activity_threshold
        self.compress2 = second_compress
        self.screensize = ()
        self.previous_frame = None

    def _capture_screen(self):
        try:
            screenshot = ImageGrab.grab()
            self.screensize = screenshot.size
            img_np = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            return img_bgr
        except:
            return b""

    def _detect_activity(self, current_frame):
        if self.threshold:
            if self.previous_frame is None:
                self.previous_frame = current_frame
                return False  # No previous frame to compare to

            # Compute the absolute difference between the current frame and the previous frame
            diff = cv2.absdiff(current_frame, self.previous_frame)

            # Convert the difference to grayscale
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

            # Apply a threshold to get a binary image
            _, thresh = cv2.threshold(gray_diff, self.threshold, 255, cv2.THRESH_BINARY)

            # Calculate the number of non-zero pixels in the thresholded image
            non_zero_count = np.count_nonzero(thresh)

            # Update the previous frame
            self.previous_frame = current_frame

            # If there are enough non-zero pixels, we consider it as activity
            return non_zero_count > 500  # You can adjust the threshold as needed
        else:
            return True

    def _imagenc(self, image):
        if self.format == "webp":
            retval, buffer = cv2.imencode('.webp', image, [int(cv2.IMWRITE_WEBP_QUALITY), self.quality])
        elif self.format == "jpeg":
            retval, buffer = cv2.imencode('.jpeg', image, [int(cv2.IMWRITE_JPEG_QUALITY), self.quality])
        elif self.format == "avif":
            retval, buffer = cv2.imencode('.avif', image, [int(cv2.IMWRITE_AVIF_QUALITY), self.quality])

        else:
            raise TypeError(f"{self.format} is not supported")

        if not retval:
            raise ValueError("image encoding failed.")

        return np.array(buffer).tobytes()

    def _translate_coordinates(self, x, y):
        if self.resolution:
            translated_x = int(x * (self.screensize[0] / self.resolution[0]))
            translated_y = int(y * (self.screensize[1] / self.resolution[1]))
        else:
            translated_x = int(x * (self.screensize[0] / 1920))
            translated_y = int(y * (self.screensize[1] / 1090))
        return translated_x, translated_y

    def _convert_quality(self, quality):
        brotli_quality = int(quality / 100 * 11)
        lgwin = int(10 + (quality / 100 * (24 - 10)))

        return brotli_quality, lgwin

    def _capture(self):
        while self.running:
            screen_image = self._capture_screen()

            if self._detect_activity(screen_image):
                if self.resolution:
                    screen_image = cv2.resize(screen_image, self.resolution, interpolation=cv2.INTER_NEAREST)
                else:
                    self.resolution = self.screensize

                data = self._imagenc(screen_image)

                if self.compress2:
                    bquality, lgwin = self._convert_quality(self.compression)
                    data = brotli.compress(data, quality=bquality, lgwin=lgwin)

                data_length = struct.pack('!III', len(data), self.resolution[0], self.resolution[1])
                data2send = data_length + data

                print(f"Sending data length: {len(data2send)}")
                self.buffer.put(data2send)

    def handle_commands(self, command, client):
        action = command["action"]
        data = command["data"]

        if action == "move_mouse":
            x, y = data["x"], data["y"]
            rx, ry = self._translate_coordinates(x, y)
            mouse.move(rx, ry)

        elif action == "click_mouse":
            button = data["button"]
            state = data["state"]

            if button == 1:
                if state == "down":
                    mouse.press()
                else:
                    mouse.release()
            elif button == 2:
                if state == "down":
                    mouse.press(mouse.MIDDLE)
                else:
                    mouse.release(mouse.MIDDLE)
            elif button == 3:
                if state == "down":
                    mouse.press(mouse.RIGHT)
                else:
                    mouse.release(mouse.RIGHT)
            # elif button == 4:
            #    mouse.wheel()
            # elif button == 5:
            #    mouse.wheel(-1)
        elif action == "keyboard":
            key = data["key"]
            state = data["state"]

            if state == "down":
                keyboard.press(key)
            else:
                keyboard.release(key)

    def init(self, client):
        capture_thread = threading.Thread(target=self._capture, daemon=True)
        capture_thread.start()