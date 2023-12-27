import os
import socket
import logging
import threading
from typing import Literal
from dockerHandler import DockerHandler
from minecraftServerHandler import MinecraftServerHandler
from objects.minecraftServer import MinecraftServer


class RequestHandler(threading.Thread):
    def __init__(self, port: str, docker_handler: DockerHandler, minecraft_server_handler: MinecraftServerHandler):
        logging.info(
            f'[RequestHandler:{port}] initializing request handler...')
        super().__init__()
        self.port: str = port

        if not self.port:
            logging.info(
                f'[RequestHandler:{self.port}] no port specified')
            return

        self.docker_handler: DockerHandler = docker_handler
        self.minecraft_server_handler: MinecraftServerHandler = minecraft_server_handler

        self.sock: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address: tuple[Literal['localhost'], str] = (
            'localhost', self.port)
        logging.info(
            f'[RequestHandler:{self.port}] starting up on {server_address[0]} port {server_address[1]}')
        self.sock.bind(server_address)
        self.sock.settimeout(5)
        self.sock.listen(30)
        logging.info(
            f'[RequestHandler:{self.port}] request handler initialized')

    def restart(self):
        logging.info(
            f'[RequestHandler:{self.port}] restarting request handler for port {self.port}')
        self.sock.close()
        self.__init__(self.port, self.docker_handler,
                      self.minecraft_server_handler)

    def run(self) -> None:
        while True:
            try:
                logging.info(
                    f'[RequestHandler:{self.port}] waiting for a connection on port {self.port}')
                self.connection, self.client_address = self.sock.accept()
                try:
                    logging.info(
                        f'[RequestHandler:{self.port}] connection from {self.client_address}')
                    self.handle_request()
                except Exception as e:
                    logging.info(
                        f'[RequestHandler:{self.port}] error in request handler for port {self.port}: {e}')
                    logging.info(
                        '[RequestHandler:{self.port}] restarting request handler...')
                    self.restart()
                finally:
                    self.connection.close()
                    self.restart()
            except Exception as e:
                logging.info(
                    f'[RequestHandler:{self.port}] error in request handler for port {self.port}: {e}')
                logging.info(
                    '[RequestHandler:{self.port}] restarting request handler...')
                self.restart()

    def handle_request(self) -> None:
        logging.info(
            f'[RequestHandler:{self.port}] handling request on port {self.port}')

        service_name = self.docker_handler.get_port_map().get(str(self.port))
        logging.info(
            f'[RequestHandler:{self.port}] service name: {service_name}')

        if service_name:
            minecraft_server: MinecraftServer = self.minecraft_server_handler.get_server(
                service_name)

            if not minecraft_server:
                logging.info(
                    f'[RequestHandler:{self.port}] no minecraft server found for service name {service_name}')
                return
            request = self.connection.recv(1024)
            logging.info(
                f'[RequestHandler:{self.port}] received request: {request}')
            # b'\x1b\x00\xfb\x05\x14mc.tealfire.de\x00FML3\x00c\xa0\x02\x1a\x00\x07DerTyp7\x01\xf2]\x9a\x18*\xeaJ\xed\xbe0g\x9c\x8aT\xa9t'
            if request[0] == 0x10 or request[0] == 0x15 or request[0] == 0x1b:
                if b'\x02' in request:
                    logging.info(
                        f'[RequestHandler:{self.port}] detected join/login request for {service_name}')
                    if minecraft_server.is_starting() == True:
                        logging.info(
                            f'[RequestHandler:{self.port}] container {service_name} is already starting...')
                        self.forward_request_to_placeholder(
                            request, minecraft_server)
                    else:
                        logging.info(
                            f'[RequestHandler:{self.port}] starting container {service_name}')
                        self.minecraft_server_handler.start_server(
                            service_name)
                elif b'\x01' in request:
                    logging.info(
                        f'[RequestHandler:{self.port}] detected ping request for {service_name}')
                    self.forward_request_to_placeholder(
                        request, minecraft_server)

            elif request[0] == 0xFE:
                logging.info(
                    f'[RequestHandler:{self.port}] detected legacy ping request for {service_name}')
                self.forward_request_to_placeholder(request, minecraft_server)
            else:
                logging.info(
                    f'[RequestHandler:{self.port}] detected unknown request for {service_name}')
                self.forward_request_to_placeholder(request, minecraft_server)

        else:
            logging.info(
                f'[RequestHandler:{self.port}] no container mapped to port {self.port}')

    def forward_request_to_placeholder(self, request, minecraft_server: MinecraftServer) -> None:
        logging.info(
            '[RequestHandler:{self.port}] forwarding request to placeholder server')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            ip = "127.0.0.1"
            logging.info(
                f'[RequestHandler:{self.port}] placeholder server ip: {ip}')
            try:
                if minecraft_server.is_starting() == True:
                    logging.info(
                        '[RequestHandler:{self.port}] container is starting. Using placeholder port 20001')
                    server_socket.connect((ip, 20001))
                else:
                    logging.info(
                        '[RequestHandler:{self.port}] container is not starting. Using placeholder port 20000')
                    server_socket.connect((ip, 20000))

                server_socket.sendall(request)
                response = server_socket.recv(1024)
                self.connection.sendall(response)
            except Exception as e:
                logging.info(
                    f'[RequestHandler:{self.port}] error while handling request on port {self.port}: {e}')
                self.restart()
