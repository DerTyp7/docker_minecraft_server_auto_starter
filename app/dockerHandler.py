import docker
import os
import logging


class DockerHandler:
    def __init__(self, base_url, port_ip_map):
        logging.info(
            f'Initializing docker handler with base url {base_url} and port ip map: {port_ip_map}')
        self.base_url = base_url
        self.client = docker.DockerClient(base_url=base_url)
        self.port_ip_map = port_ip_map
        self.current_network = self.get_current_network()

    def get_current_container(self):
        current_container_name = os.environ.get('HOSTNAME')
        try:
            return self.client.containers.get(current_container_name)
        except docker.errors.NotFound:
            logging.error(f'Container {current_container_name} not found')
            return None

    def get_current_container_ip(self):
        # Get IP of current container
        current_container = self.get_current_container()
        if current_container:
            networks = current_container.attrs['NetworkSettings']['Networks']
            current_network = list(networks.keys())[0]
            return networks[current_network]['IPAddress']
        return None

    def get_current_network(self):
        # Get network of current container
        current_container = self.get_current_container()
        if current_container:
            networks = current_container.attrs['NetworkSettings']['Networks']
            return list(networks.keys())[0]
        return None

    def get_container_by_ip(self, ip):
        try:
            containers = self.client.containers.list(all=True)
        except docker.errors.APIError as e:
            logging.error(f'Error getting container list: {e}')
            return None

        for container in containers:
            networks = container.attrs['NetworkSettings']['Networks']
            if self.current_network in networks and networks[self.current_network]['IPAMConfig']['IPv4Address'] == ip:
                logging.info(
                    f'Found container {container.name} with ip {ip} in network {self.current_network}')
                return container
        logging.info(
            f'No docker container found with ip {ip} in network {self.current_network}')
        return None

    def is_container_starting(self, container):
        if container:
            return container.attrs['State']['Health']['Status'] == 'starting'
        return False
