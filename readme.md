# Minecraft Server Auto Starter for Docker Compose

This container will manage the access to your Minecraft server. It will start the Minecraft server when a player tries to connect.  
This container is designed to work with the [itzg/minecraft-server](https://hub.docker.com/r/itzg/minecraft-server) container.  
It uses the AutoStop feature of the [itzg/minecraft-server](https://hub.docker.com/r/itzg/minecraft-server) container to stop the Minecraft server when no player is connected.

## Usage

See the [docker-compose.yml](https://github.com/DerTyp7/docker_minecraft_server_auto_starter/blob/main/docker-compose.yml) file for an example.

## Environment Variables

| Variable                         | Description                                                                                                 | Default | Example        |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------- | -------------- |
| `PLACEHOLDER_SERVER_SLEEPING_IP` | (optional) The internal docker-compose IP for the placeholder server when a server is sleeping                         | `""`    | `"172.20.0.3"` |
| `PLACEHOLDER_SERVER_STARTING_IP` | (optional) The internal docker-compose IP for the placeholder server when a server is starting                         | `""`    | `"172.20.0.4"` |
| `PORT_IP_MAP`                    | Map which matches the external Minecraft ports to the internal docker-compose IPs for the Minecraft-Servers |         | ![image](https://github.com/DerTyp7/docker_minecraft_server_auto_starter/assets/76851529/4319a42c-7fc4-4be6-8e9d-710475dfde9a)|
