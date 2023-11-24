import os
import socket
import threading
from utils import docker_container_mapping


class RequestHandler(threading.Thread):
    def __init__(self, port, docker_handler):
        super().__init__()
        self.port = port
        self.docker_handler = docker_handler
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', self.port)
        print(f'Starting up on {server_address[0]} port {server_address[1]}')
        self.sock.bind(server_address)
        self.sock.listen(1)

    def run(self):
        while True:
            print(f'Waiting for a connection on port {self.port}')
            self.connection, self.client_address = self.sock.accept()
            try:
                print('Connection from', self.client_address)
                self.handle_request()
            finally:
                self.connection.close()

    def handle_request(self):
        print(f'Handling request on port {self.port}')
        container_ip = docker_container_mapping().get(str(self.port))
        if container_ip:
            container = self.docker_handler.get_container_by_ip(
                container_ip)
            isStarting = self.docker_handler.is_container_starting(container)
            request = self.connection.recv(1024)
            if request[0] == 0x10:
                if b'\x01' in request:
                    print(f'Detected ping request for {container_ip}')
                    self.forward_request_to_server(request, isStarting)
                elif b'\x02' in request:
                    print(f'Detected join/login request for {container_ip}')
                    if isStarting:
                        print(
                            f'Container {container_ip} is already starting...')
                        self.forward_request_to_server(request, isStarting)
                    else:
                        print(f'Starting container {container_ip}')
                        container.start()

            elif request[0] == 0xFE:
                print(f'Detected legacy ping request for {container_ip}')
                self.forward_request_to_server(request, isStarting)

            else:
                print(f'No container mapped to port {self.port}')

    def forward_request_to_server(self, request, isStarting=False):
        print('Forwarding request to placeholder server')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            ip = os.environ.get('PLACEHOLDER_SERVER_SLEEPING_IP')
            if isStarting:
                print('Container is starting. Using starting placeholder IP')
                ip = os.environ.get('PLACEHOLDER_SERVER_STARTING_IP')

            server_socket.connect(
                (ip, 25565))
            server_socket.sendall(request)
            response = server_socket.recv(1024)
            self.connection.sendall(response)