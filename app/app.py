from requestHandler import RequestHandler
from utils import docker_container_mapping
from dockerHandler import DockerHandler
from nginxHandler import NginxHandler
import time


def main():
    port_ip_map = docker_container_mapping()

    # Create a DockerHandler instance
    docker_handler = DockerHandler(
        'unix://var/run/docker.sock', port_ip_map)

    # Create an NginxHandler instance
    nginx_handler = NginxHandler('/etc/nginx/nginx.conf')
    nginx_handler.setup_config_file(
        docker_container_mapping(), docker_handler.get_current_container_ip())
    nginx_handler.print_config()

    # Create a RequestHandler instance for each port
    for port in port_ip_map.keys():
        print(f'Creating request handler for port {port}')
        request_handler = RequestHandler(int(port), docker_handler)
        request_handler.start()


main()
