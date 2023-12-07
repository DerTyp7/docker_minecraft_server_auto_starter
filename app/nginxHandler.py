import os
import logging


class NginxHandler:
    def __init__(self, config_path):
        self.config_path = config_path

    def start(self):
        logging.info('Starting NGINX...')
        os.system('nginx > /dev/null 2>&1 &')
        logging.info('NGINX started')

    def stop(self):
        logging.info('Stopping NGINX...')
        os.system('nginx -s stop')
        logging.info('NGINX stopped')

    def restart(self):
        self.stop()
        self.start()

    def print_config(self):
        with open(self.config_path, 'r') as f:
            logging.info(f.read())

    def setup_config_file(self, port_ip_map, current_container_ip):
        proxy_timeout = "5s"
        self.stop()
        logging.info('Setting up NGINX config file...')
        logging.info('port_ip_map: {}'.format(port_ip_map))
        nginx_conf = open(self.config_path, 'w+')
        nginx_conf.truncate()
        nginx_conf.write('worker_processes 5;\n')
        nginx_conf.write('events { \n')
        nginx_conf.write('    worker_connections 1024;\n')
        nginx_conf.write('    multi_accept on;\n')
        nginx_conf.write('}\n')
        nginx_conf.write('stream {\n')

        # This looks confusing, but the nginx.conf looks good when it's done
        # Example for the nginx-example.conf file is in the repo root directory
        for port in port_ip_map:
            nginx_conf.write(f'    upstream upstream_{port} {{\n')
            nginx_conf.write(f'        server {port_ip_map[port]}:25565;\n')
            nginx_conf.write(f'        server 127.0.0.1:{port} backup;\n')
            nginx_conf.write('    }\n')

            nginx_conf.write('    server {\n')
            nginx_conf.write(
                f'        listen {current_container_ip}:{port};\n')

            nginx_conf.write(
                f'        proxy_connect_timeout {proxy_timeout};\n')
            nginx_conf.write(f'        proxy_timeout {proxy_timeout};\n')

            nginx_conf.write(f'        proxy_pass upstream_{port};\n')
            nginx_conf.write('    }\n')
        nginx_conf.write('}\n')
        nginx_conf.close()
        logging.info('NGINX config file setup complete')
        self.start()
