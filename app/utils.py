import logging
import os
import json
import json
from typing import List, Dict


def docker_container_mapping() -> Dict[str, str]:
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


# motd = {
#     "1": "§4Maintenance!",
#     "2": "§aCheck example.com for more information!"
# }
# version_text = "§4Maintenance"
# samples = ["§bexample.com", "", "§4Maintenance"]
# kick_message = ["§bSorry", "", "§aThis server is offline!"]

def generate_placeholder_server_config_file(path: str, ip: str, port: int, motd: Dict[str, str], version_text: str, samples: List[str], kick_message: List[str]) -> None:
    config = {
        "ip": ip,
        "kick_message": kick_message,
        "motd": motd,
        "player_max": 0,
        "player_online": 0,
        "port": port,
        "protocol": 2,
        "samples": samples,
        "server_icon": "server_icon.png",
        "show_hostname_if_available": True,
        "show_ip_if_hostname_available": True,
        "version_text": version_text
    }

    with open(path, 'w') as f:
        json.dump(config, f, indent=4)
