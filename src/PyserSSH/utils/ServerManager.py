import time
import logging

logger = logging.getLogger("PyserSSH.Utils.ServerManager")

class ServerManager:
    def __init__(self):
        self.servers = {}

    def add_server(self, name, server, *args, **kwargs):
        """
        Adds a server to the manager with the specified name. Raises an error if a server with the same name already exists.

        Args:
            name (str): The name of the server.
            server (object): The server instance to be added.
            *args: Arguments for server initialization.
            **kwargs: Keyword arguments for server initialization.

        Raises:
            ValueError: If a server with the same name already exists.
        """
        if name in self.servers:
            raise ValueError(f"Server with name '{name}' already exists.")
        self.servers[name] = {"server": server, "args": args, "kwargs": kwargs, "status": "stopped"}
        logger.info(f"Server '{name}' added.")

    def remove_server(self, name):
        """
        Removes a server from the manager by name. Raises an error if the server does not exist.

        Args:
            name (str): The name of the server to be removed.

        Raises:
            ValueError: If no server with the specified name exists.
        """
        if name not in self.servers:
            raise ValueError(f"No server found with name '{name}'.")
        del self.servers[name]
        logger.info(f"Server '{name}' removed.")

    def get_server(self, name):
        """
        Retrieves a server by its name.

        Args:
            name (str): The name of the server to retrieve.

        Returns:
            dict: A dictionary containing the server instance, arguments, keyword arguments, and its status, or None if the server is not found.
        """
        return self.servers.get(name, None)

    def start_server(self, name):
        """
        Starts a server with the specified name if it is not already running. Blocks until the server starts.

        Args:
            name (str): The name of the server to start.

        Raises:
            ValueError: If no server with the specified name exists or the server cannot be started.
        """
        server_info = self.get_server(name)
        if not server_info:
            raise ValueError(f"No server found with name '{name}'.")

        if server_info["status"] == "running":
            logger.info(f"Server '{name}' is already running.")
            return

        server = server_info["server"]
        args, kwargs = server_info["args"], server_info["kwargs"]

        logger.info(f"Starting server '{name}' with arguments {args}...")
        server_info["status"] = "starting"
        server.run(*args, **kwargs)

        while not server.isrunning:
            logger.debug(f"Waiting for server '{name}' to start...")
            time.sleep(0.1)

        server_info["status"] = "running"
        logger.info(f"Server '{name}' is now running.")

    def stop_server(self, name):
        """
        Stops a server with the specified name if it is running. Blocks until the server stops.

        Args:
            name (str): The name of the server to stop.

        Raises:
            ValueError: If no server with the specified name exists or the server cannot be stopped.
        """
        server_info = self.get_server(name)
        if not server_info:
            raise ValueError(f"No server found with name '{name}'.")

        if server_info["status"] == "stopped":
            logger.info(f"Server '{name}' is already stopped.")
            return

        server = server_info["server"]

        logger.info(f"Shutting down server '{name}'...")
        server_info["status"] = "shutting down"
        server.stop_server()

        while server.isrunning:
            logger.debug(f"Waiting for server '{name}' to shut down...")
            time.sleep(0.1)

        server_info["status"] = "stopped"
        logger.info(f"Server '{name}' has been stopped.")

    def start_all_servers(self):
        """
        Starts all servers managed by the ServerManager. Blocks until each server starts.
        """
        for name, server_info in self.servers.items():
            if server_info["status"] == "running":
                logger.info(f"Server '{name}' is already running.")
                continue
            server, args, kwargs = server_info["server"], server_info["args"], server_info["kwargs"]
            logger.info(f"Starting server '{name}' with arguments {args}...")
            server_info["status"] = "starting"
            server.run(*args, **kwargs)

            while not server.isrunning:
                logger.debug(f"Waiting for server '{name}' to start...")
                time.sleep(0.1)

            server_info["status"] = "running"
            logger.info(f"Server '{name}' is now running.")

    def stop_all_servers(self):
        """
        Stops all servers managed by the ServerManager. Blocks until each server stops.
        """
        for name, server_info in self.servers.items():
            if server_info["status"] == "stopped":
                logger.info(f"Server '{name}' is already stopped.")
                continue
            server = server_info["server"]
            logger.info(f"Shutting down server '{name}'...")
            server_info["status"] = "shutting down"
            server.stop_server()

            while server.isrunning:
                logger.debug(f"Waiting for server '{name}' to shut down...")
                time.sleep(0.1)

            server_info["status"] = "stopped"
            logger.info(f"Server '{name}' has been stopped.")

    def get_status(self, name):
        """
        Retrieves the status of a server by name.

        Args:
            name (str): The name of the server to get the status of.

        Returns:
            str: The current status of the server (e.g., 'running', 'stopped', etc.).

        Raises:
            ValueError: If no server with the specified name exists.
        """
        server_info = self.get_server(name)
        if not server_info:
            raise ValueError(f"No server found with name '{name}'.")
        return server_info["status"]
