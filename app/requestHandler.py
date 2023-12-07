import os
import socket
import logging
import threading
from utils import docker_container_mapping


class RequestHandler(threading.Thread):
    def __init__(self, port, docker_handler):
        super().__init__()
        self.port = port
        self.docker_handler = docker_handler
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = ('localhost', self.port)
        logging.info(
            f'Starting up on {server_address[0]} port {server_address[1]}')
        self.sock.bind(server_address)
        self.sock.listen(1)

    def restart(self):
        logging.info(f'Restarting request handler for port {self.port}')
        self.sock.close()
        self.__init__(self.port, self.docker_handler)

    def run(self):
        while True:
            try:
                logging.info(f'Waiting for a connection on port {self.port}')
                self.connection, self.client_address = self.sock.accept()
                try:
                    logging.info('Connection from', self.client_address)
                    self.handle_request()
                except Exception as e:
                    logging.info(
                        f'Error in request handler for port {self.port}: {e}')
                    logging.info('Restarting request handler...')
                    self.restart()
                finally:
                    self.connection.close()
                    self.restart()
            except Exception as e:
                logging.info(
                    f'Error in request handler for port {self.port}: {e}')
                logging.info('Restarting request handler...')
                self.restart()

    def handle_request(self):
        logging.info(f'Handling request on port {self.port}')
        container_ip = docker_container_mapping().get(str(self.port))
        if container_ip:
            container = self.docker_handler.get_container_by_ip(
                container_ip)
            isStarting = self.docker_handler.is_container_starting(container)
            request = self.connection.recv(1024)
            logging.info(f'Received request: {request}')
            # b'\x1b\x00\xfb\x05\x14mc.tealfire.de\x00FML3\x00c\xa0\x02\x1a\x00\x07DerTyp7\x01\xf2]\x9a\x18*\xeaJ\xed\xbe0g\x9c\x8aT\xa9t'
            if request[0] == 0x10 or request[0] == 0x15 or request[0] == 0x1b:
                if b'\x02' in request:
                    logging.info(
                        f'Detected join/login request for {container_ip}')
                    if isStarting:
                        logging.info(
                            f'Container {container_ip} is already starting...')
                        self.forward_request_to_placeholder(
                            request, isStarting)
                    else:
                        logging.info(f'Starting container {container_ip}')
                        container.start()
                elif b'\x01' in request:
                    logging.info(f'Detected ping request for {container_ip}')
                    self.forward_request_to_placeholder(request, isStarting)

            elif request[0] == 0xFE:
                logging.info(
                    f'Detected legacy ping request for {container_ip}')
                self.forward_request_to_placeholder(request, isStarting)
            else:
                logging.info(f'Detected unknown request for {container_ip}')
                self.forward_request_to_placeholder(request, isStarting)

        else:
            logging.info(f'No container mapped to port {self.port}')

    def forward_request_to_placeholder(self, request, isStarting=False):
        logging.info('Forwarding request to placeholder server')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            ip = os.environ.get('PLACEHOLDER_SERVER_SLEEPING_IP')
            if isStarting:
                logging.info(
                    'Container is starting. Using starting placeholder IP')
                ip = os.environ.get('PLACEHOLDER_SERVER_STARTING_IP')

            if not ip:
                logging.info('No placeholder server IP found')
                return
            try:
                server_socket.connect((ip, 25565))
                server_socket.sendall(request)
                response = server_socket.recv(1024)
                self.connection.sendall(response)
            except Exception as e:
                logging.info(
                    f'Error while handling request on port {self.port}: {e}')
                self.restart()
