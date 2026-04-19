import json  # importar librerias para leer cosas de terminal y JSON
import socket
import sys

from utils import *

# Nicole:
# IP VM : 172.20.144.24
# IP Host : 192.168.100.95

# Natalia:
# IP VM: 192.168.64.3
# IP HOST: 192.168.64.1

IP_HOST = "192.168.100.95"
IP_VM = "172.20.144.24"

estructura = 0  # aca va la estructura de datos que se le pasará a create_http_message para crear el mensaje HTTP a enviar al cliente

# agregar para recibir el nombre desde un archivo JSON
config_path = sys.argv[1]
with open(config_path, "r", encoding="utf-8") as file:
    data = json.load(file)
    NOMBRE = data["user"]
    print("El usuario es: " + NOMBRE +".\n")

# Cuerpo en HTML que se le enviará al cliente, se puede modificar para agregar el nombre del cliente
response_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>RESPUESTA</title>
</head>
<body>
    <h1>Hola hola!! yupiiii</h1>
    <h3>El usuario es {NOMBRE}</h3>
</body>
</html>
""".format(NOMBRE=NOMBRE)

# Respuesta HTTP que se le enviará al cliente, se puede modificar para agregar el nombre del cliente
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
    print('Socket Server creado')


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
        print(f"-> Se ha recibido una request del cliente con el siguiente mensaje:\n{recv_message}\n")

        # Visualizo el mensaje HTTP parseado
        http_message_parsed = parse_http_message(
        recv_message
        )  # print(f"Mensaje HTTP parseado\n")
        print(f"Mensaje HTTP parseado:\n{http_message_parsed}\n")
 
        # reconstruyo el mensaje http desde la estructura de datos
        http_message_parsed = create_http_message(http_message_parsed)
        print(f"Mensaje HTTP reconstruido:\n{http_message_parsed}\n")

        # creo una respuesta para la maquina virtual
        response = create_http_message(response_message).encode()
        client_socket.send(response)
        print(f"Respuesta enviada: \n{response.decode()}\n")

        # Cierro conexión
        client_socket.close()
        print(f"Conexión con {new_socket_address} ha sido cerrada\n")
