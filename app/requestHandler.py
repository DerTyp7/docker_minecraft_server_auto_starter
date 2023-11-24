import os
import socket
import threading
from utils import docker_container_mapping


class RequestHandler(threading.Thread):
    def __init__(self, port, docker_handler):
        super().__init__()
        self.port = port
        self.docker_handler = docker_handler
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the port
        server_address = ('localhost', self.port)
        print('starting up on {} port {}'.format(*server_address))
        self.sock.bind(server_address)
        # Listen for incoming connections
        self.sock.listen(1)

    def run(self):
        while True:
            print('waiting for a connection on port {}'.format(self.port))
            self.connection, self.client_address = self.sock.accept()
            try:
                print('connection from', self.client_address)
                self.handle_request()
            finally:
                self.connection.close()

    def handle_request(self):
        print('handling request on port {}'.format(self.port))
        container_ip = docker_container_mapping().get(str(self.port))
        if container_ip:
            container = self.docker_handler.get_container_by_ip(
                container_ip)
            isStarting = self.docker_handler.is_container_starting(container)
            request = self.connection.recv(1024)
            if request[0] == 0x10:
                if b'\x01' in request:
                    print('ping')
                    self.forward_request_to_server(request, isStarting)
                elif b'\x02' in request:
                    print('join')
                    if isStarting:
                        print('container is starting, waiting for 5 seconds')
                        self.forward_request_to_server(request, isStarting)
                    else:
                        print('starting docker container {}'.format(container_ip))
                        container.start()

            elif request[0] == 0xFE:
                print('legacy server list ping')
                self.forward_request_to_server(request, isStarting)

            else:
                print('no docker container mapped to this port')

    def forward_request_to_server(self, request, isStarting=False):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            ip = os.environ.get('PLACEHOLDER_SERVER_SLEEPING_IP')
            if isStarting:
                print('----------------container is starting, waiting for 5 seconds')
                ip = os.environ.get('PLACEHOLDER_SERVER_STARTING_IP')

            server_socket.connect(
                (ip, 25565))
            server_socket.sendall(request)
            response = server_socket.recv(1024)
            self.connection.sendall(response)
