import socket
import threading
import os
import docker

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


def setup_nginx_config():
    # Stop nginx
    os.system('nginx -s stop')
    # open nginx.conf for write create if not exist
    nginx_conf = open('/etc/nginx/nginx.conf', 'w+')
    nginx_conf.truncate()
    nginx_conf.write('events { }\n')
    nginx_conf.write('stream {\n')

    port_ip_map = docker_container_mapping()
    for port in port_ip_map:
        nginx_conf.write('    upstream upstream_{} {{\n'.format(port))
        nginx_conf.write('        server {}:{};\n'.format(
            port_ip_map[port], port))
        nginx_conf.write('        server 127.0.0.1:{} backup;\n'.format(port))
        nginx_conf.write('    }\n')

        nginx_conf.write('    server {\n')
        nginx_conf.write('        listen {}:{};\n'.format(
            get_current_container_ip(), port))
        nginx_conf.write('        proxy_pass upstream_{};\n'.format(port))
        nginx_conf.write('    }\n')
    nginx_conf.write('}\n')
    nginx_conf.close()
    os.system('nginx > /dev/null 2>&1 &')


def get_current_container_ip():
    # Get IP of current container
    current_container_name = os.environ.get('HOSTNAME')
    current_container = client.containers.get(current_container_name)
    networks = current_container.attrs['NetworkSettings']['Networks']
    current_network = list(networks.keys())[0]
    current_container_ip = networks[current_network]['IPAddress']
    return current_container_ip


def get_current_network():
    # Get network of current container
    current_container_name = os.environ.get('HOSTNAME')
    current_container = client.containers.get(current_container_name)
    networks = current_container.attrs['NetworkSettings']['Networks']
    current_network = list(networks.keys())[0]
    return current_network


def get_docker_container_by_ip(ip):
    current_network = get_current_network()
    print('getting docker container by ip {} in network {}'.format(
        ip, current_network))
    containers = client.containers.list(all=True)

    for container in containers:
        print('current network: {}'.format(current_network))
        print('checking container {}'.format(container.name))
        print('container networks: {}'.format(
            container.attrs['NetworkSettings']['Networks']))
        print('container ip: {}'.format(
            container.attrs['NetworkSettings']['Networks'][current_network]['IPAMConfig']['IPv4Address']))

        networks = container.attrs['NetworkSettings']['Networks']
        if current_network in networks and networks[current_network]['IPAMConfig']['IPv4Address'] == ip:
            print('found docker container {} with ip {} in network {}'.format(
                container.name, ip, current_network))
            return container
    print('no docker container found with ip {} in network {}'.format(
        ip, current_network))
    return None


def docker_container_mapping():
    # Get the PORT_IP_MAP environment variable
    port_ip_map_str = os.getenv('PORT_IP_MAP')

    # Convert the environment variable to a Python dictionary
    port_ip_map = {}
    for line in port_ip_map_str.split('\n'):
        if line:  # ignore empty lines
            port, ip = line.split(':')
            port_ip_map[port.strip()] = ip.strip()

    return port_ip_map


class RequestHandler(threading.Thread):
    def __init__(self, port):
        super().__init__()
        self.port = port
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
            get_docker_container_by_ip(container_ip).start()
            # Send a response
            self.connection.sendall(b'Request handled')
        else:
            print('no docker container mapped to this port')


for port in range(25560, 25571):
    handler = RequestHandler(port)
    handler.start()

setup_nginx_config()
