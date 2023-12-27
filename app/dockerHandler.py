from typing import Dict
import docker
from docker import DockerClient
from docker.models.networks import Network
import os
import logging

from utils import docker_container_mapping


class DockerHandler:
    def __init__(self, base_url: str):
        logging.info(
            f'[DockerHandler] initializing docker handler with base url {base_url} and port ip map: {self.get_port_map()}...')
        self.base_url: str = base_url
        self.client: DockerClient = DockerClient(base_url=base_url)
        self.current_network: Network = self.get_current_network()
        logging.info('[DockerHandler] docker handler initialized')
        logging.info(
            f'[DockerHandler] current container name: {self.get_auto_starter_container_name()}')
        logging.info(
            f'[DockerHandler] current network: {str(self.current_network)}')

    def get_port_map(self) -> Dict[str, str]:
        return docker_container_mapping()

    def stop_container(self, container) -> None:
        if container:
            logging.info(
                f'[DockerHandler] stopping container {str(container.name)}')
            container.stop()
            logging.info(f'[DockerHandler] container {container.name} stopped')
        else:
            logging.info('[DockerHandler] no container to stop')

    def start_container(self, container) -> None:
        if container:
            logging.info(
                f'[DockerHandler] starting container {container.name}')
            container.start()
            logging.info(f'[DockerHandler] container {container.name} started')
        else:
            logging.info('[DockerHandler] no container to start')

    def get_container_by_service_name(self, service_name):
        logging.info(
            f'[DockerHandler] getting container by service name {service_name}...')
        try:
            containers = self.client.containers.list(
                all=True, filters={"network": self.current_network})

            if containers is None:
                logging.info('[DockerHandler] no containers found in network')
                return None

            for container in containers:
                networks = container.attrs['NetworkSettings']['Networks']
                if self.current_network in networks and service_name in networks[self.current_network]['Aliases']:
                    logging.info(
                        f'[DockerHandler] found container {container.name} with service name {service_name} in network {self.current_network}')
                    return container
            logging.info(
                f'[DockerHandler] no docker container found with service name {service_name} in network {self.current_network}')
            return None

        except docker.errors.APIError as e:
            logging.error(f'Error getting container list: {e}')
            return None

    def get_auto_starter_container_name(self) -> str | None:
        return os.environ.get('HOSTNAME')

    def get_auto_starter_container(self):
        hostname = os.environ.get('HOSTNAME')
        if hostname:
            return self.client.containers.get(hostname)
        return None

    def get_current_network(self) -> Network:
        current_container = self.get_auto_starter_container()
        if current_container:
            networks = current_container.attrs['NetworkSettings']['Networks']
            return list(networks.keys())[0]
        return None

    def get_ip_by_service_name(self, service_name: str) -> str:
        container = self.get_container_by_service_name(service_name)
        if container:
            networks = container.attrs['NetworkSettings']['Networks']
            return networks[self.current_network]['IPAddress']
        return ""

    def get_auto_starter_container_ip(self) -> str:
        container = self.get_auto_starter_container()
        if container:
            networks = container.attrs['NetworkSettings']['Networks']
            return networks[self.current_network]['IPAddress']
        return ""
