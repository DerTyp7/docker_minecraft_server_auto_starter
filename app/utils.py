import logging
import os
import socket


def docker_container_mapping():
    port_map_str = os.environ.get('PORT_MAP')

    port_map = {}
    for line in port_map_str.split('\n'):
        if line:
            port, name = line.split(':')
            port_map[port.strip()] = name.strip().replace(
                "'", "").replace('"', "").strip()

    # print port map for debugging
    logging.info('PORT_MAP:')
    for port in port_map:
        logging.info(f'{port} -> {port_map[port]}')
    return port_map


def get_ip_by_dns_name(dns_name):
    try:
        return socket.gethostbyname(dns_name, resolver='127.0.0.1')
    except socket.gaierror:
        logging.error(f'Could not resolve dns name {dns_name}')
        return None
