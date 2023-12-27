import os
import time
from dockerHandler import DockerHandler
from nginxHandler import NginxHandler
from minecraftServerHandler import MinecraftServerHandler
from requestHandler import RequestHandler
import logging
from FakeMCServer.fake_mc_server import FakeMCServer
import threading

logging.basicConfig(level=logging.INFO)


def init_placeholder_servers():
    sleeping = FakeMCServer(port=20000, motd={
        "1": "sleeping!", "2": "§aCheck example.com for more information!"})
    starting = FakeMCServer(port=20001, motd={
        "1": "starting!", "2": "§aCheck example.com for more information!"})

    # Create threads for each server initialization
    sleeping_thread = threading.Thread(target=sleeping.start_server)
    starting_thread = threading.Thread(target=starting.start_server)

    # Start the threads
    sleeping_thread.start()
    starting_thread.start()


def main() -> None:
    try:
        logging.info('[INIT] initializing placeholder servers...')
        init_placeholder_servers()
        logging.info('[INIT] placeholder servers initialized')

        logging.info('[INIT] initializing auto starter...')
        logging.info('[INIT] initializing docker handler...')
        docker_handler: DockerHandler = DockerHandler(
            'unix://var/run/docker.sock')
        logging.info('[INIT] docker handler initialized')

        logging.info('[INIT] initializing nginx handler...')
        nginx_handler: NginxHandler = NginxHandler('/etc/nginx/nginx.conf')

        nginx_handler.update_config_file(
            docker_handler)

        logging.info('[INIT] nginx handler initialized')

        logging.info('[INIT] initializing minecraft server handler...')
        minecraft_server_handler: MinecraftServerHandler = MinecraftServerHandler(
            docker_handler, nginx_handler)

        # Find all Minecraft servers and add them to the MinecraftServerHandler instance
        for service_name in docker_handler.get_port_map().values():
            minecraft_server_handler.add_server(service_name)

        logging.info('[INIT] wait 20 seconds before stopping all servers...')
        time.sleep(20)
        minecraft_server_handler.stop_all_servers()
        logging.info('[INIT] minecraft server handler initialized')

        logging.info('[INIT] initializing request handlers...')
        # Create a RequestHandler instance for each port
        for port in docker_handler.get_port_map().keys():
            logging.info(f'[INIT] creating request handler for port {port}')
            request_handler: RequestHandler = RequestHandler(
                int(port), docker_handler, minecraft_server_handler)
            request_handler.start()
        logging.info('[INIT] request handlers initialized')

    except Exception as e:
        logging.error(f'An error occurred: {e}')


if __name__ == "__main__":
    main()
