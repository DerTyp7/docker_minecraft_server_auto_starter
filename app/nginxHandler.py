import os
import time


class NginxHandler:
    def __init__(self, config_path):
        self.config_path = config_path

    def start(self):
        print('Starting NGINX...')
        os.system('nginx > /dev/null 2>&1 &')
        print('NGINX started')

    def stop(self):
        print('Stopping NGINX...')
        os.system('nginx -s stop')
        print('NGINX stopped')

    def restart(self):
        self.stop()
        self.start()

    def print_config(self):
        with open(self.config_path, 'r') as f:
            print(f.read())

    def setup_config_file(self, port_ip_map, current_container_ip):
        proxy_timeout = "5s"
        self.stop()
        print('Setting up NGINX config file...')
        print('port_ip_map: {}'.format(port_ip_map))
        nginx_conf = open(self.config_path, 'w+')
        nginx_conf.truncate()
        nginx_conf.write('events { }\n')
        nginx_conf.write('stream {\n')

        for port in port_ip_map:
            nginx_conf.write('    upstream upstream_{} {{\n'.format(port))
            nginx_conf.write('        server {}:25565;\n'.format(
                port_ip_map[port]))
            nginx_conf.write(
                '        server 127.0.0.1:{} backup;\n'.format(port))

            nginx_conf.write('    }\n')

            nginx_conf.write('    server {\n')
            nginx_conf.write('        listen {}:{};\n'.format(
                current_container_ip, port))

            nginx_conf.write('        proxy_connect_timeout {};\n'.format(
                proxy_timeout))
            nginx_conf.write('        proxy_timeout {};\n'.format(
                proxy_timeout))

            nginx_conf.write('        proxy_pass upstream_{};\n'.format(port))
            nginx_conf.write('    }\n')
        nginx_conf.write('}\n')
        nginx_conf.close()
        print('NGINX config file setup')
        self.start()
