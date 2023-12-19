import logging
from typing import Dict, Optional
from nginxHandler import NginxHandler
from dockerHandler import DockerHandler
from objects.minecraftServer import MinecraftServer


class MinecraftServerHandler:
    def __init__(self, docker_handler: DockerHandler, nginx_handler: NginxHandler):
        logging.info(
            '[MinecraftServerHandler] initializing minecraft server handler...')
        self.minecraft_servers: Dict[str, MinecraftServer] = {}
        self.docker_handler: DockerHandler = docker_handler
        self.nginx_handler: NginxHandler = nginx_handler

        self.active_service_name: str | None = None
        logging.info(
            '[MinecraftServerHandler] minecraft server handler initialized')

    def add_server(self, service_name: str) -> None:
        logging.info(
            f'[MinecraftServerHandler] adding server {service_name}')
        self.minecraft_servers[service_name] = MinecraftServer(
            self.docker_handler, service_name)
        logging.info(
            f'[MinecraftServerHandler] added server {service_name}')

    def get_server(self, service_name: str) -> MinecraftServer | None:
        logging.info(f'[MinecraftServerHandler] getting server {service_name}')
        return self.minecraft_servers.get(service_name)

    def stop_all_servers(self, exclude_service_name: Optional[str] = None) -> None:
        logging.info(f'[MinecraftServerHandler] stopping all servers')
        for service_name, server in self.minecraft_servers.items():
            logging.info(
                f'[MinecraftServerHandler] stopping server {service_name}')
            server.stop()

    def start_server(self, service_name: str) -> None:
        logging.info(
            f'[MinecraftServerHandler] starting server {service_name}')
        self.stop_all_servers()
        server = self.get_server(service_name)
        if server:
            server.start()
            logging.info(
                f'[MinecraftServerHandler] started server {service_name}')
            self.nginx_handler.update_config_file(
                self.docker_handler)
            self.nginx_handler.print_config()
        else:
            logging.info(
                f'[MinecraftServerHandler] No server found with service name {service_name}')
