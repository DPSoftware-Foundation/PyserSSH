from paramiko.server import InteractiveQuery
from paramiko.common import AUTH_FAILED, AUTH_SUCCESSFUL
import time

class InteractiveAuthManager:
    def __init__(self, title, description):
        self.data = {}
        self.idd = 0
        self.title = title
        self.desc = description

        self.is_inputted = False
        self.is_system_ready = False
        self.result = None

    def generateIQ(self):
        prompts = []
        for data in self.data.values():
            prompts.append((data["prompt"], data["show"]))

        return InteractiveQuery(self.title, self.desc, *prompts)

    def add_prompt(self, prompt, show=True):
        assigned_id = self.idd

        self.data[assigned_id] = {
            "prompt": prompt,
            "show": show,
            "input": None
        }

        self.idd += 1

        return assigned_id

    def set_response(self, responses):
        for i, data in enumerate(responses):
            self.data[i]["input"] = data

        time.sleep(0.1)
        self.is_inputted = True

    def get_response(self, id):
        return self.data[id]["input"]

    def wait_for_input(self):
        self.is_system_ready = True

        while not self.is_inputted:
            time.sleep(0.1)

    def wait_for_system(self):
        while not self.is_system_ready:
            time.sleep(0.1)

    def wait_for_result(self):
        while self.result is None:
            time.sleep(0.1)

    def is_authorized(self, allow):
        if allow:
            self.result = AUTH_SUCCESSFUL
        else:
            self.result = AUTH_FAILED