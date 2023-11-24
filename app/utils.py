import os


def docker_container_mapping():
    port_ip_map_str = os.environ.get('PORT_IP_MAP')
    # Convert the environment variable to a Python dictionary
    port_ip_map = {}
    for line in port_ip_map_str.split('\n'):
        if line:  # ignore empty lines
            port, ip = line.split(':')
            port_ip_map[port.strip()] = ip.strip()

    return port_ip_map
