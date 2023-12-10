from math import log
import socket
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
        logging.info(f'Current network: {self.current_network}')

    def get_current_container(self):
        current_container_name = os.environ.get('HOSTNAME')
        try:
            return self.client.containers.get(current_container_name)
        except docker.errors.NotFound:
            logging.error(f'Container {current_container_name} not found')
            return None

    def get_current_container_name(self):
        # Get DNS name of current container
        current_container = self.get_current_container()
        if current_container:
            networks = current_container.attrs['NetworkSettings']['Networks']
            current_network = list(networks.keys())[0]
            if 'Aliases' in networks[current_network]:
                dns_name = networks[current_network]['Aliases'][0]
                return dns_name
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

    def get_container_by_name(self, name):
        try:
            return self.client.containers.get(name)
        except docker.errors.NotFound:
            logging.error(f'Container {name} not found')
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
                        f'Container ip: {networks[self.current_network]["IPAMConfig"]["IPv4Address"]}')
                else:
                    logging.info(f'Container ip: None')

        except docker.errors.APIError as e:
            logging.error(f'Error getting container list: {e}')
            return None

    def get_ip_by_dns_name(self, dns_name):
        # dEBUG Print all containers with their network ip and dns name
        for container in self.client.containers.list(all=True):
            networks = container.attrs['NetworkSettings']['Networks']
            if self.current_network in networks:
                logging.info(
                    f'Container {container.name} ip: {networks[self.current_network]["IPAMConfig"]["IPv4Address"]}, dns name: {networks[self.current_network]["Aliases"]}')

        try:
            containers = self.client.containers.list(
                all=True, filters={"network": self.current_network})

            if containers is None:
                logging.info('No containers found')
                return None

            for container in containers:
                networks = container.attrs['NetworkSettings']['Networks']
                if self.current_network in networks and dns_name in networks[self.current_network]['Aliases']:
                    logging.info(
                        f'Found container {container.name} with dns name {dns_name} in network {self.current_network}')
                    return networks[self.current_network]['IPAMConfig']['IPv4Address']
            logging.info(
                f'No docker container found with dns name {dns_name} in network {self.current_network}')
            return None

        except docker.errors.APIError as e:
            logging.error(f'Error getting container list: {e}')
            return None
