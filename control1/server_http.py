import json  # importar librerias para leer cosas de terminal y JSON
import socket
import sys

from utils import *

# Nicole:
# IP VM : 172.20.144.24
# IP Host : 10.42.80.80

# Natalia:
# IP VM: 192.168.64.3
# IP HOST: 192.168.64.1

IP_HOST = "192.168.64.1"
IP_VM = "192.168.64.3"

estructura = 0  # aca va la estructura de datos que se le pasará a create_http_message para crear el mensaje HTTP a enviar al cliente

# agregar para recibir el nombre desde un archivo JSON
config_path = sys.argv[1]
with open(config_path, "r", encoding="utf-8") as file:
    data = json.load(file)
    NOMBRE = data["user"]

response_html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>CC4303</title>
</head>
<body>
    <h1>Bienvenide ... oh? no puedo ver tu nombre :c!</h1>
    <h3><a href="replace">¿Qué es un proxy?</a></h3>
</body>
</html>
"""

response_message = {
    "method": "HTTP/1.1",
    "path": "200 OK",
    "version": "",
    "headers": {
        "Content-Type": "text/html; charset=UTF-8",
        "Content-Length": str(len(response_html.encode("utf-8"))),  # a bytes
        "Connection": "close",
        "X-ElQuePregunta": NOMBRE,  # modificar para pedir el nombre dps
    },
    "body": response_html,
}


if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 1024
    end_of_message = "\r\n\r\n"
    new_socket_address = (IP_VM, 8000)

    print("Creando socket Proxy")
    # armamos el socket que estara en el proxy esperando peticiones del cliente los parámetros que recibe
    # el socket indican el tipo de conexión (socket.SOCK_STREAM = socket orientado a conexión)
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # le indicamos al proxy socket que debe atender peticiones en la dirección address para ello usamos bind
    proxy_socket.bind(new_socket_address)

    # luego con listen (función de sockets de python) le decimos que puede
    # tener hasta 3 peticiones de conexión encoladas
    proxy_socket.listen(3)

    while True:
        print("... Esperando clientes ...\n")
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        client_socket, client_socket_address = proxy_socket.accept()
        print(f"Conexión aceptada desde {new_socket_address}\n")

        # Recibimos el mensaje del cliente
        recv_message = receive_full_message(client_socket, buff_size, end_of_message)
        print(f"-> Se ha recibido una request del cliente:\n{recv_message}\n")

        # creo una respuesta para la maquina virtual
        # response = create_http_message(response_message).encode()
        # new_socket.send(response)
        # print(f"Respuesta enviada: \n{response.decode()}\n")
        http_message_parsed = parse_http_message(
            recv_message
        )  # print(f"Mensaje HTTP parseado\n")
        print(f"Mensaje HTTP parseado:\n{http_message_parsed}\n")

        print(" ... Conectando al servidor ...")
        # extraemos host y puerto del header
        http_host = http_message_parsed["headers"][
            "Host"
        ]  # Extrae solo el host sin el puerto
        ip_host = socket.gethostbyname(http_host)  # Obtengo la IP del host
        protocol = (
            http_message_parsed["version"].split("/")[0].lower()
        )  # Extrae el protocolo (HTTP/1.1 -> HTTP)
        http_path = http_message_parsed["path"]  # Extrae el path

        # creamos un nuevo socket para la conexion
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((ip_host, 80))  # hay que modificar y definir host

        # reenviamos la request al servidor
        server_socket.send(recv_message.encode())
        print(" ... Response enviada al servidor ...\n")

        server_response = receive_full_message(server_socket, buff_size, end_of_message)
        print(" ... Responde recibida por el servidor ...\n")

        # reenviamos la response del cliente sin modificar
        client_socket.send(server_response)

        # cerramos la conexión de ambos sockets
        # notar que la dirección que se impri
        client_socket.close()
        server_socket.close()
        print("-> Conexión de ambos sockets ha sido cerrada")

        # seguimos esperando por si llegan otras conexiones
