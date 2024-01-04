import json
import os
import socket
import logging
import threading
from typing import Literal
import uuid
from app import byte_utils
from dockerHandler import DockerHandler
from minecraftServerHandler import MinecraftServerHandler
from objects.minecraftServer import MinecraftServer
import byte_utils


class RequestHandler(threading.Thread):
    def __init__(self, port: str, docker_handler: DockerHandler, minecraft_server_handler: MinecraftServerHandler):
        logging.info(
            f'[RequestHandler:{port}] initializing request handler...')
        super().__init__()
        self.port: str = port

        if not self.port:
            logging.info(
                f'[RequestHandler:{self.port}] no port specified')
            return

        self.docker_handler: DockerHandler = docker_handler
        self.minecraft_server_handler: MinecraftServerHandler = minecraft_server_handler

        self.sock: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address: tuple[Literal['localhost'], str] = (
            'localhost', self.port)
        logging.info(
            f'[RequestHandler:{self.port}] starting up on {server_address[0]} port {server_address[1]}')
        self.sock.bind(server_address)
        self.sock.settimeout(5)
        self.sock.listen(30)
        logging.info(
            f'[RequestHandler:{self.port}] request handler initialized')

    def restart(self):
        logging.info(
            f'[RequestHandler:{self.port}] restarting request handler for port {self.port}')
        self.sock.close()
        self.__init__(self.port, self.docker_handler,
                      self.minecraft_server_handler)

    def run(self) -> None:
        while True:
            try:
                logging.info(
                    f'[RequestHandler:{self.port}] waiting for a connection on port {self.port}')
                self.connection, self.client_address = self.sock.accept()
                try:
                    logging.info(
                        f'[RequestHandler:{self.port}] connection from {self.client_address}')
                    self.handle_request()
                except Exception as e:
                    logging.info(
                        f'[RequestHandler:{self.port}] error in request handler for port {self.port}: {e}')
                    logging.info(
                        '[RequestHandler:{self.port}] restarting request handler...')
                    self.restart()
                finally:
                    self.connection.close()
                    self.restart()
            except Exception as e:
                logging.info(
                    f'[RequestHandler:{self.port}] error in request handler for port {self.port}: {e}')
                logging.info(
                    '[RequestHandler:{self.port}] restarting request handler...')
                self.restart()

    def handle_request(self) -> None:
        logging.info(
            f'[RequestHandler:{self.port}] handling request on port {self.port}')

        service_name = self.docker_handler.get_port_map().get(str(self.port))
        logging.info(
            f'[RequestHandler:{self.port}] service name: {service_name}')

        if service_name:
            minecraft_server: MinecraftServer = self.minecraft_server_handler.get_server(
                service_name)

            if not minecraft_server:
                logging.info(
                    f'[RequestHandler:{self.port}] no minecraft server found for service name {service_name}')
                return
            request = self.connection.recv(1024)
            logging.info(
                f'[RequestHandler:{self.port}] received request: {request}')
            # b'\x1b\x00\xfb\x05\x14mc.tealfire.de\x00FML3\x00c\xa0\x02\x1a\x00\x07DerTyp7\x01\xf2]\x9a\x18*\xeaJ\xed\xbe0g\x9c\x8aT\xa9t'
            if request[0] == 0x10 or request[0] == 0x15 or request[0] == 0x1b:
                if b'\x02' in request:
                    logging.info(
                        f'[RequestHandler:{self.port}] detected join/login request for {service_name}')
                    if minecraft_server.is_starting() == True:
                        logging.info(
                            f'[RequestHandler:{self.port}] container {service_name} is already starting...')
                        self.send_response(self.client_address)
                        # self.forward_request_to_placeholder(
                        #     request, minecraft_server)
                    else:
                        logging.info(
                            f'[RequestHandler:{self.port}] starting container {service_name}')
                        self.minecraft_server_handler.start_server(
                            service_name)
                elif b'\x01' in request:
                    logging.info(
                        f'[RequestHandler:{self.port}] detected ping request for {service_name}')
                    self.send_response(self.client_address)

                    # self.forward_request_to_placeholder(
                    #     request, minecraft_server)

            elif request[0] == 0xFE:
                logging.info(
                    f'[RequestHandler:{self.port}] detected legacy ping request for {service_name}')
                self.send_response(self.client_address)

                # self.forward_request_to_placeholder(request, minecraft_server)
            else:
                logging.info(
                    f'[RequestHandler:{self.port}] detected unknown request for {service_name}')
                self.send_response(self.client_address)

                # self.forward_request_to_placeholder(request, minecraft_server)

        else:
            logging.info(
                f'[RequestHandler:{self.port}] no container mapped to port {self.port}')

    def send_response(self, addr):
        client_socket = self.connection

        data = client_socket.recv(1024)
        client_ip = addr[0]

        fqdn = socket.getfqdn(client_ip)
        if self.show_hostname and client_ip != fqdn:
            client_ip = fqdn + "/" + client_ip

        try:
            (length, i) = byte_utils.read_varint(data, 0)
            (packetID, i) = byte_utils.read_varint(data, i)

            if packetID == 0:
                (version, i) = byte_utils.read_varint(data, i)
                (ip, i) = byte_utils.read_utf(data, i)

                ip = ip.replace('\x00', '').replace("\r", "\\r").replace(
                    "\t", "\\t").replace("\n", "\\n")
                is_using_fml = False

                if ip.endswith("FML"):
                    is_using_fml = True
                    ip = ip[:-3]

                (port, i) = byte_utils.read_ushort(data, i)
                (state, i) = byte_utils.read_varint(data, i)

                if state == 1:
                    self.logger.info(("[%s:%s] Received client " + ("(using ForgeModLoader) " if is_using_fml else "") +
                                      "ping packet (%s:%s).") % (client_ip, addr[1], ip, port))
                    motd = {}
                    motd["version"] = {}
                    motd["version"]["name"] = "testing"
                    motd["version"]["protocol"] = 2
                    motd["players"] = {}
                    motd["players"]["max"] = 0
                    motd["players"]["online"] = 0
                    motd["players"]["sample"] = []

                    for sample in self.samples:
                        motd["players"]["sample"].append(
                            {"name": sample, "id": str(uuid.uuid4())})

                    motd["description"] = {"text":  {
                        "1": "§4Maintensadfance!", "2": "§aCheck example.caom for more information!"}}

                    if self.server_icon and len(self.server_icon) > 0:
                        motd["favicon"] = self.server_icon

                    self.write_response(client_socket, json.dumps(motd))
                elif state == 2:
                    name = ""
                    if len(data) != i:
                        (some_int, i) = byte_utils.read_varint(data, i)
                        (some_int, i) = byte_utils.read_varint(data, i)
                        (name, i) = byte_utils.read_utf(data, i)
                    self.logger.info(
                        ("[%s:%s] " + (name + " t" if len(name) > 0 else "T") + "ries to connect to the server " +
                         ("(using ForgeModLoader) " if is_using_fml else "") + "(%s:%s).")
                        % (client_ip, addr[1], ip, port))
                    self.write_response(client_socket, json.dumps(
                        {"text": ["§bSorry", "", "§aThis servzzzer is offline!"]}))
                else:
                    self.logger.info(
                        "[%s:%d] Tried to request a login/ping with an unknown state: %d" % (client_ip, addr[1], state))
            elif packetID == 1:
                (long, i) = byte_utils.read_long(data, i)
                response = bytearray()
                byte_utils.write_varint(response, 9)
                byte_utils.write_varint(response, 1)
                bytearray.append(long)
                client_socket.sendall(bytearray)
                self.logger.info(
                    "[%s:%d] Responded with pong packet." % (client_ip, addr[1]))
            else:
                self.logger.warning("[%s:%d] Sent an unexpected packet: %d" % (
                    client_ip, addr[1], packetID))
        except (TypeError, IndexError):
            self.logger.warning(
                "[%s:%s] Received invalid data (%s)" % (client_ip, addr[1], data))
            return

    def write_response(self, client_socket, response):
        response_array = bytearray()
        byte_utils.write_varint(response_array, 0)
        byte_utils.write_utf(response_array, response)
        length = bytearray()
        byte_utils.write_varint(length, len(response_array))
        client_socket.sendall(length)
        client_socket.sendall(response_array)

    # def forward_request_to_placeholder(self, request, minecraft_server: MinecraftServer) -> None:
    #     logging.info(
    #         '[RequestHandler:{self.port}] forwarding request to placeholder server')
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    #         ip = "127.0.0.1"
    #         logging.info(
    #             f'[RequestHandler:{self.port}] placeholder server ip: {ip}')
    #         try:
    #             if minecraft_server.is_starting() == True:
    #                 logging.info(
    #                     '[RequestHandler:{self.port}] container is starting. Using placeholder port 20001')
    #                 server_socket.connect((ip, 20001))
    #             else:
    #                 logging.info(
    #                     '[RequestHandler:{self.port}] container is not starting. Using placeholder port 20000')
    #                 server_socket.connect((ip, 20000))

    #             server_socket.sendall(request)
    #             response = server_socket.recv(1024)
    #             self.connection.sendall(response)
    #         except Exception as e:
    #             logging.info(
    #                 f'[RequestHandler:{self.port}] error while handling request on port {self.port}: {e}')
    #             self.restart()
