import docker
import os


class DockerHandler:
    def __init__(self, base_url, port_ip_map):
        print(
            f'Initializing docker handler with base url {base_url} and port ip map: {port_ip_map}')
        self.base_url = base_url
        self.client = docker.DockerClient(base_url=base_url)
        self.port_ip_map = port_ip_map
        self.current_network = self.get_current_network()

    def get_current_container_ip(self):
        # Get IP of current container
        current_container_name = os.environ.get('HOSTNAME')
        current_container = self.client.containers.get(current_container_name)
        networks = current_container.attrs['NetworkSettings']['Networks']
        current_network = list(networks.keys())[0]
        current_container_ip = networks[current_network]['IPAddress']
        return current_container_ip

    def get_current_network(self):
        # Get network of current container
        current_container_name = os.environ.get('HOSTNAME')
        current_container = self.client.containers.get(current_container_name)
        networks = current_container.attrs['NetworkSettings']['Networks']
        current_network = list(networks.keys())[0]
        return current_network

    def get_container_by_ip(self, ip):
        containers = self.client.containers.list(all=True)

        for container in containers:
            networks = container.attrs['NetworkSettings']['Networks']
            if self.current_network in networks and networks[self.current_network]['IPAMConfig']['IPv4Address'] == ip:
                print(
                    f'Found container {container.name} with ip {ip} in network {self.current_network}')
                return container
        print(
            f'No docker container found with ip {ip} in network {self.current_network}')
        return None

    def is_container_starting(self, container):
        return container.attrs['State']['Health']['Status'] == 'starting'
