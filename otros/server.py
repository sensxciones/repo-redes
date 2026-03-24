import socket
import json
import sys
from utils import *

# definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
buff_size = 4
end_of_message = "\r\n\r\n"
new_socket_address = ('localhost', 8000)

# Leo usuario desde archivo JSON
# sys.argv[0] es el nombre del script, sys.argv[1] será el primer argumento 
config_path = sys.argv[1]

with open(config_path, "r", encoding="utf-8") as file:
    data = json.load(file)
    NOMBRE_SERVER = data["user"]
    print("El usuario es: " + NOMBRE_SERVER +".\n")


# Armo el socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket Server creado')

# Bind para atender peticiones en la dirección address
server_socket.bind(new_socket_address)

# Puede tener hasta 3 peticiones de conexión encoladas
server_socket.listen(3)
print('Esperando clientes\n')

# Acepta peticion cuando llega y se crea un nuevo socket que se comunicará con el cliente
new_socket, new_socket_address = server_socket.accept()
print(f'Conexión aceptada desde {new_socket_address}\n')

# Recibo msj usando receive_full_message: entrega el mensaje en string (no en bytes) y sin el end_of_message
recv_message = receive_full_message(new_socket, buff_size, end_of_message) 
print(f'-> Se ha recibido el siguiente mensaje: \n{recv_message}\n')

# Visualizo el mensaje HTTP parseado
http_message_parsed = parse_HTTP_message(recv_message) 
print(f"Mensaje HTTP parseado:\n{http_message_parsed}\n")

# Reconstruyo el mensaje HTTP desde la estructura de datos
http_message = create_HTTP_message(http_message_parsed) 
print(f"Mensaje HTTP reconstruido:\n{http_message}\n")

# Responde indicando que recibimos el mensaje con send, y se pasa a bytes con encode
# 1) Body
body_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>RESPUESTA</title>
</head>
<body>
    <h1>Hola hola!! yupiiii</h1>
    <h3>El usuario es {NOMBRE_SERVER}</h3>
</body>
</html>
""".format(NOMBRE_SERVER=NOMBRE_SERVER)

# 2) Armo el mensaje HTTP de respuesta con header y body
response_http_message = {
    "method": "HTTP/1.1",
    "path": "200 OK",
    "version": "",
    "headers": {
        "Content-Type": "text/html; charset=UTF-8",
        "Content-Length": str(len(body_html.encode("utf-8"))), # a bytes
        "Connection": "close",
        "X-ElQuePregunta": NOMBRE_SERVER
    },
    "body": body_html
}

response_message = create_HTTP_message(response_http_message)
print(f"Mensaje HTTP de respuesta:\n{response_message}\n")
new_socket.send(response_message.encode())


# Cierro conexión
new_socket.close()
print(f"Conexión con {new_socket_address} ha sido cerrada\n")



