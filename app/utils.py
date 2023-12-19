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
