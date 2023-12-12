import docker
import os
import logging


class DockerHandler:
    def __init__(self, base_url, port_map):
        logging.info(
            f'Initializing docker handler with base url {base_url} and port ip map: {port_map}')
        self.base_url = base_url
        self.client = docker.DockerClient(base_url=base_url)
        self.port_map = port_map
        self.current_network = self.get_current_network()
        logging.info('Docker handler initialized')
        logging.info(
            f'Current container name: {self.get_current_container_name()}')
        logging.info(f'Current network: {self.current_network}')

    def get_current_container(self):
        hostname = self.get_current_container_name()
        if hostname:
            return self.client.containers.get(hostname)
        return None

    def get_current_container_name(self):
        return os.environ.get('HOSTNAME')

    def get_current_network(self):
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
            if self.current_network in networks and networks[self.current_network]['IPAddress'] == ip:
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

    def print_all_container_names(self):
        try:
            containers = self.client.containers.list(
                all=True, filters={"network": self.current_network})

            if containers is None:
                logging.info('No containers found')
                return None

            for container in containers:
                logging.info(f'Container name: {container.name}')
                # get docker compose dns name
                networks = container.attrs['NetworkSettings']['Networks']
                if self.current_network in networks:
                    logging.info(
                        f'Container ip: {networks[self.current_network]["IPAddress"]}')
                else:
                    logging.info(f'Container ip: None')

        except docker.errors.APIError as e:
            logging.error(f'Error getting container list: {e}')
            return None

    def get_ip_by_dns_name(self, dns_name):
        try:
            containers = self.client.containers.list(
                all=True, filters={"network": self.current_network})

            if containers is None:
                logging.info('No containers found')
                return None
            for container in containers:
                networks = container.attrs['NetworkSettings']['Networks']
                if self.current_network in networks and dns_name in networks[self.current_network]['Aliases']:
                    ip = networks[self.current_network]['IPAddress']
                    logging.info(
                        f'Found container {container.name} with dns name {dns_name} with ip {ip} in network {self.current_network}')
                    return ip
            logging.info(
                f'No docker container found with dns name {dns_name} in network {self.current_network}')
            return None

        except docker.errors.APIError as e:
            logging.error(f'Error getting container list: {e}')
            return None
