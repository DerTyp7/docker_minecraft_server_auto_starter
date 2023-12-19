import docker
import logging


from dockerHandler import DockerHandler


class MinecraftServer:
    def __init__(self, docker_handler: DockerHandler, service_name: str):
        self.docker_handler: DockerHandler = docker_handler
        self.service_name: str = service_name

    def get_container(self):
        return self.docker_handler.get_container_by_service_name(
            self.service_name)

    def start(self) -> None:
        self.docker_handler.start_container(
            self.get_container())

    def stop(self) -> None:
        self.docker_handler.stop_container(
            self.get_container())

    def is_starting(self) -> bool:
        if self.get_container():
            return self.get_container().attrs['State']['Health']['Status'] == 'starting'
        return False

    def is_running(self) -> bool:
        if self.get_container():
            return self.get_container().attrs['State']['Health']['Status'] == 'healthy'
        return False

    def get_ip(self) -> str | None:
        try:
            containers = self.docker_handler.client.containers.list(
                all=True, filters={"network": self.docker_handler.current_network})

            if containers is None:
                logging.info('[MinecraftServer] no containers found')
                return None
            for container in containers:
                networks = container.attrs['NetworkSettings']['Networks']
                if self.docker_handler.current_network in networks and self.service_name in networks[self.docker_handler.current_network]['Aliases']:
                    ip = networks[self.docker_handler.current_network]['IPAddress']
                    logging.info(
                        f'[MinecraftServer] found container {container.name} with service name {self.service_name} with ip {ip} in network {self.docker_handler.current_network}')
                    return ip
            logging.info(
                f'[MinecraftServer] no docker container found with service name {self.service_name} in network {self.docker_handler.current_network}')
            return None

        except docker.errors.APIError as e:
            logging.error(
                f'[MinecraftServer] error getting container list: {e}')
            return None
