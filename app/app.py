import logging

from requestHandler import RequestHandler
from utils import docker_container_mapping
from dockerHandler import DockerHandler
from nginxHandler import NginxHandler

logging.basicConfig(level=logging.INFO)


def main():
    try:
        port_map = docker_container_mapping()

        # Create a DockerHandler instance
        docker_handler = DockerHandler(
            'unix://var/run/docker.sock', port_map)

        # Create an NginxHandler instance
        nginx_handler = NginxHandler('/etc/nginx/nginx.conf')
        docker_handler.get_ip_by_dns_name(
            docker_handler.get_current_container_name())

        nginx_handler.setup_config_file(
            port_map, docker_handler.get_ip_by_dns_name(docker_handler.get_current_container_name()), docker_handler)

        nginx_handler.print_config()

        # Create a RequestHandler instance for each port
        for port in port_map.keys():
            logging.info(f'Creating request handler for port {port}')
            request_handler = RequestHandler(int(port), docker_handler)
            request_handler.start()

        # DEBUG
        logging.info(
            '-----------------------------DEBUG--------------------------------')
        logging.info(
            f'Current container: {docker_handler.get_current_container_name()}')
        logging.info(
            f'Current container ip: {docker_handler.get_ip_by_dns_name(docker_handler.get_current_container_name())}')
        logging.info(
            f'Current network: {docker_handler.get_current_network()}')

        docker_handler.print_all_container_names()
        logging.info(
            '-----------------------------DEBUG END--------------------------------')

    except Exception as e:
        logging.error(f'An error occurred: {e}')


if __name__ == "__main__":
    main()
