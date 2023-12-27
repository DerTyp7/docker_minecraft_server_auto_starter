import os
import logging
from typing import TextIO, Dict

from dockerHandler import DockerHandler


class NginxHandler:
    def __init__(self, config_path: str):
        logging.info('[NginxHandler] initializing nginx handler...')
        self.config_path: str = config_path

    def start(self) -> None:
        logging.info('[NginxHandler] starting nginx...')
        os.system('nginx > /dev/null 2>&1 &')
        logging.info('[NginxHandler] nginx started')

    def stop(self) -> None:
        logging.info('[NginxHandler] stopping nginx...')
        os.system('nginx -s stop')
        logging.info('[NginxHandler] nginx stopped')

    def restart(self) -> None:
        self.stop()
        self.start()

    def print_config(self) -> None:
        logging.info('[NginxHandler] printing nginx config file...')
        logging.info('========================================')
        with open(self.config_path, 'r') as f:
            logging.info(f.read())
        logging.info('========================================')
        logging.info('[NginxHandler] nginx config file printed')

    def update_config_file(self, docker_handler: DockerHandler) -> None:
        logging.info('[NginxHandler] updating nginx config file...')
        self.stop()
        port_map: Dict[str, str] = docker_handler.get_port_map()
        if port_map is None:
            logging.error('[NginxHandler] port_map is None')
            return

        proxy_timeout: str = "5s"
        logging.info('[NginxHandler] setting up NGINX config file...')
        logging.info('[NginxHandler] port_map: {}'.format(port_map))
        nginx_conf: TextIO = open(self.config_path, 'w+')
        nginx_conf.truncate()
        nginx_conf.write('worker_processes 5;\n')
        nginx_conf.write('events { \n')
        nginx_conf.write('    worker_connections 1024;\n')
        nginx_conf.write('    multi_accept on;\n')
        nginx_conf.write('}\n')
        nginx_conf.write('stream {\n')

        # This looks confusing, but the nginx.conf looks good when it's done
        # Example for the nginx-example.conf file is in the repo root directory
        if isinstance(port_map, dict):
            for port in port_map:
                ip = docker_handler.get_ip_by_service_name(port_map[port])

                nginx_conf.write(
                    f'    # docker service {port_map[port]} on port {port}\n')
                nginx_conf.write(f'    upstream upstream_{port} {{\n')

                if ip == "":
                    nginx_conf.write(f'        server 127.0.0.1:{port};\n')
                else:
                    nginx_conf.write(f'        server {ip}:25565;\n')
                    nginx_conf.write(
                        f'        server 127.0.0.1:{port} backup;\n')
                nginx_conf.write('    }\n')

                nginx_conf.write('    server {\n')
                nginx_conf.write(
                    f'        listen {docker_handler.get_auto_starter_container_ip()}:{port};\n')

                nginx_conf.write(
                    f'        proxy_connect_timeout {proxy_timeout};\n')
                nginx_conf.write(f'        proxy_timeout {proxy_timeout};\n')

                nginx_conf.write(f'        proxy_pass upstream_{port};\n')
                nginx_conf.write('    }\n')
        else:
            logging.error('port_map is not a dictionary')

        nginx_conf.write('}\n')
        nginx_conf.close()
        logging.info('[NginxHandler] nginx config file setup complete')
        self.start()

        # Restart for good measure. Add inconsistency issues with nginx
        self.restart()
