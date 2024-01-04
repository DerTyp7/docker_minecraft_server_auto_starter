import json
import socket
import uuid
import logging
from threading import Thread
import utils as utils


class SocketServer:
    def __init__(self, port: int, ip: str = "0.0.0.0", motd: dict = {"1": "§4Maintenance!", "2": "§aCheck example.com for more information!"},
                 version_text: str = "§4Maintenance", kick_message: list = ["§bSorry", "", "§aThis server is offline!"],
                 server_icon: str = "server_icon.png", samples: list = ["§bexample.com", "", "§4Maintenance"], show_hostname_if_available: bool = True,
                 player_max: int = 0, player_online: int = 0, protocol: int = 2):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.motd = motd
        self.version_text = version_text
        self.kick_message = kick_message
        self.samples = samples
        self.server_icon = server_icon
        self.show_hostname = show_hostname_if_available
        self.player_max = player_max
        self.player_online = player_online
        self.protocol = protocol

    def is_server_list_ping(self, request, service_name):
        if request[0] == 0xFE:
            logging.info(
                f'[RequestHandler:{self.port}] detected legacy ping request for {service_name}')
            self.send_response(self.client_address)
        elif b'\x01' in request:
            logging.info(
                f'[RequestHandler:{self.port}] detected ping request for {service_name}')
            self.send_response(self.client_address)
        else:
            logging.info(
                f'[RequestHandler:{self.port}] detected unknown request for {service_name}')
            self.send_response(self.client_address)

    def is_join_attempt(self, request, service_name, minecraft_server):
        if request[0] == 0x10 or request[0] == 0x15 or request[0] == 0x1b:
            if b'\x02' in request:
                logging.info(
                    f'[RequestHandler:{self.port}] detected join/login request for {service_name}')
                if minecraft_server.is_starting() == True:
                    logging.info(
                        f'[RequestHandler:{self.port}] container {service_name} is already starting...')
                    self.send_response(self.client_address)
                else:
                    logging.info(
                        f'[RequestHandler:{self.port}] starting container {service_name}')
                    self.minecraft_server_handler.start_server(service_name)

    def on_new_client(self, client_socket, addr):
        data = client_socket.recv(1024)
        client_ip = addr[0]

        if self.is_server_list_ping(data):
            fqdn = socket.getfqdn(client_ip)
            if self.show_hostname and client_ip != fqdn:
                client_ip = fqdn + "/" + client_ip

            try:
                (length, i) = utils.read_varint(data, 0)
                (packetID, i) = utils.read_varint(data, i)

                if packetID == 0:
                    (version, i) = utils.read_varint(data, i)
                    (ip, i) = utils.read_utf(data, i)

                    ip = ip.replace('\x00', '').replace("\r", "\\r").replace(
                        "\t", "\\t").replace("\n", "\\n")
                    is_using_fml = False

                    if ip.endswith("FML"):
                        is_using_fml = True
                        ip = ip[:-3]

                    (port, i) = utils.read_ushort(data, i)
                    (state, i) = utils.read_varint(data, i)

                    if state == 1:
                        logging.info(("[%s:%s] Received client " + ("(using ForgeModLoader) " if is_using_fml else "") +
                                      "ping packet (%s:%s).") % (client_ip, addr[1], ip, port))
                        motd = {}
                        motd["version"] = {}
                        motd["version"]["name"] = self.version_text
                        motd["version"]["protocol"] = self.protocol
                        motd["players"] = {}
                        motd["players"]["max"] = self.player_max
                        motd["players"]["online"] = self.player_online
                        motd["players"]["sample"] = []

                        for sample in ["§bexamplaaaaaaaae.com", "", "§4Maintaaaaaaaaaaaaaaenance"]:
                            motd["players"]["sample"].append(
                                {"name": sample, "id": str(uuid.uuid4())})

                        motd["description"] = {"text": self.motd}

                        if self.server_icon and len(self.server_icon) > 0:
                            motd["favicon"] = self.server_icon

                        self.write_response(client_socket, json.dumps(motd))
                    elif state == 2:
                        name = ""
                        if len(data) != i:
                            (some_int, i) = utils.read_varint(data, i)
                            (some_int, i) = utils.read_varint(data, i)
                            (name, i) = utils.read_utf(data, i)
                        logging.info(
                            ("[%s:%s] " + (name + " t" if len(name) > 0 else "T") + "ries to connect to the server " +
                             ("(using ForgeModLoader) " if is_using_fml else "") + "(%s:%s).")
                            % (client_ip, addr[1], ip, port))
                        self.write_response(client_socket, json.dumps(
                            {"text": "kicked"}))
                    else:
                        logging.info(
                            "[%s:%d] Tried to request a login/ping with an unknown state: %d" % (client_ip, addr[1], state))
                elif packetID == 1:
                    (long, i) = utils.read_long(data, i)
                    response = bytearray()
                    utils.write_varint(response, 9)
                    utils.write_varint(response, 1)
                    bytearray.append(long)
                    client_socket.sendall(bytearray)
                    logging.info(
                        "[%s:%d] Responded with pong packet." % (client_ip, addr[1]))
                else:
                    logging.warning("[%s:%d] Sent an unexpected packet: %d" % (
                        client_ip, addr[1], packetID))
            except (TypeError, IndexError):
                logging.warning(
                    "[%s:%s] Received invalid data (%s)" % (client_ip, addr[1], data))
                return

    def write_response(self, client_socket, response):
        response_array = bytearray()
        utils.write_varint(response_array, 0)
        utils.write_utf(response_array, response)
        length = bytearray()
        utils.write_varint(length, len(response_array))
        client_socket.sendall(length)
        client_socket.sendall(response_array)

    def start(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.ip, self.port))
        self.sock.settimeout(5)
        self.sock.listen(30)
        logging.info("Server started on %s:%s! Waiting for incoming connections..." % (
            self.ip, self.port))
        while 1:
            try:
                (client, address) = self.sock.accept()
            except socket.timeout:
                continue  # timeouts may occur but shouldn't worry uns server-side

            Thread(target=self.on_new_client, daemon=True,
                   args=(client, address,)).start()

    def close(self):
        self.sock.close()
