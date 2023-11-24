from requestHandler import RequestHandler
from utils import docker_container_mapping
from dockerHandler import DockerHandler
from nginxHandler import NginxHandler


def main():
    # Create a DockerHandler instance
    docker_handler = DockerHandler(
        'unix://var/run/docker.sock', docker_container_mapping())

    # Create a RequestHandler instance for each port
    for port in range(25560, 25571):
        request_handler = RequestHandler(port, docker_handler)
        request_handler.start()

    # Create an NginxHandler instance
    nginx_handler = NginxHandler('/etc/nginx/nginx.conf')
    nginx_handler.setup_config_file(
        docker_container_mapping(), docker_handler.get_current_container_ip())
    nginx_handler.print_config()


main()
