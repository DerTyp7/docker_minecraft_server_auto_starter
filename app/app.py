import socket
import threading
import os
from dockerHandler import DockerHandler
from nginxHandler import NginxHandler


def docker_container_mapping():
    port_ip_map_str = os.environ.get('PORT_IP_MAP')
    # Convert the environment variable to a Python dictionary
    port_ip_map = {}
    for line in port_ip_map_str.split('\n'):
        if line:  # ignore empty lines
            port, ip = line.split(':')
            port_ip_map[port.strip()] = ip.strip()

    return port_ip_map


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
        # Get the Docker container name for this port
        container_ip = docker_container_mapping().get(str(self.port))
        if container_ip:
            # Start the Docker container
            print('starting docker container {}'.format(container_ip))
            self.docker_handler.get_container_by_ip(container_ip).start()
            # Send a response
            self.connection.sendall(b'Request handled')
        else:
            print('no docker container mapped to this port')


def main():
    docker_handler = DockerHandler(
        'unix://var/run/docker.sock', docker_container_mapping())

    for port in range(25560, 25571):
        request_handler = RequestHandler(port, docker_handler)
        request_handler.start()

    nginx_handler = NginxHandler('/etc/nginx/nginx.conf')
    nginx_handler.setup_config_file(
        docker_container_mapping(), docker_handler.get_current_container_ip())
    nginx_handler.print_config()


main()
