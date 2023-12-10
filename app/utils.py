import logging
import os
import socket
import socket


def docker_container_mapping():
    port_ip_map_str = os.environ.get('PORT_MAP')
    # Convert the environment variable to a Python dictionary
    port_ip_map = {}
    for line in port_ip_map_str.split('\n'):
        if line:  # ignore empty lines
            port, ip = line.split(':')
            port_ip_map[port.strip()] = ip.strip()

    return port_ip_map


def get_ip_by_dns_name(dns_name):
    try:
        return socket.gethostbyname(dns_name, resolver='127.0.0.1')
    except socket.gaierror:
        logging.error(f'Could not resolve dns name {dns_name}')
        return None
