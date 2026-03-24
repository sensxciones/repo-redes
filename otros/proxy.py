import socket
import json
import sys
from utils import *

# Nicole Charun

# Leo usuario desde archivo JSON
# sys.argv[0] es el nombre del script, sys.argv[1] será el primer argumento 
config_path = sys.argv[1]
with open(config_path, "r", encoding="utf-8") as file:
    data = json.load(file)
    NOMBRE_SERVER = data["user"]

# definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
buff_size = 4096
end_of_message = "\r\n\r\n"

# Armar html de error
error_body_html = """<!DOCTYPE html> 
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Error 403</title>
</head>
<body>
    <h1>Error 403 yupiiii</h1>
    <h3>El usuario {NOMBRE_SERVER} ha bloqueado esta pagina</h3>
    <img src="file:///C:/Users/Nicole/OneDrive%20-%20Universidad%20de%20Chile/Stress/2025%20Primavera/Redes/act1http/gato.jpg">
</body>
</html>
""".format(NOMBRE_SERVER=NOMBRE_SERVER)
response_blocked_error = {
    "method": "HTTP/1.1",
    "path": "403 Forbidden",
    "version": "",
    "headers": {
        "Content-Type": "text/html; charset=UTF-8",
        "Content-Length": str(len(error_body_html.encode("utf-8"))), # a bytes
        "Connection": "close",
        "X-ElQuePregunta": NOMBRE_SERVER
    },
    "body": error_body_html
}


# Armo y conecto el socket a CLIENTE
proxy_socket_A = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_A_address = ('127.0.0.1', 8000) # direccion cliente
print('Creando socket - Cliente -> Proxy\n')
proxy_socket_A.bind(socket_A_address) # Bind para atender peticiones en la dirección address
proxy_socket_A.listen(3) # Puede tener hasta 3 peticiones de conexión 



while True:
    print('Esperando clientes\n')
    
    # Acepto petición cuando llega
    socket_A, socket_A_address = proxy_socket_A.accept()  #socket_A es el socket que se comunica con el cliente
    print(f'Conexión aceptada desde {socket_A_address}\n')

    # 1) CLIENTE -> PROXY

    #Recibe mensaje del cliente
    recv_message = receive_full_message(socket_A, buff_size, end_of_message)  
    print(f'Request de cliente recibida:\n{recv_message}\n')

    # Parseo el mensaje HTTP recibido
    http_message_parsed = parse_HTTP_message(recv_message) #print(f"Mensaje HTTP parseado\n")
    print(f"Mensaje HTTP parseado:\n{http_message_parsed}\n")

    # Extraigo el host, ip y el path del mensaje HTTP
    http_host = http_message_parsed['headers']['Host'] # Extrae solo el host sin el puerto
    ip_host = socket.gethostbyname(http_host) # Obtengo la IP del host
    protocol = http_message_parsed['version'].split('/')[0].lower() # Extrae el protocolo (HTTP/1.1 -> HTTP)
    http_path = http_message_parsed['path'] # Extrae el path

    # Si la página está bloqueada, enviar error 403
    if is_blocked(http_path, data["blocked"]):
        print("La pagina está bloqueada, enviando error 403\n")
        error_message = create_HTTP_message(response_blocked_error)
        response = error_message.encode()

    else:
        # Armo y conecto el socket a Destino
        proxy_socket_B = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #        print('Creando socket - Proxy -> Destino\n')
        socket_B_address = (ip_host, 80) # direccion destino
        proxy_socket_B.connect(socket_B_address) # Conecto el socket al address #        print('Conectado al servidor destino\n')
        
        # Reconstruyo el mensaje HTTP 
        http_message_parsed["headers"]["X-ElQuePregunta"] = "PROOOXY"
        http_message = create_HTTP_message(http_message_parsed) #print(f"Mensaje HTTP reconstruido \n")

        # 2) PROXY -> DESTINO
        proxy_socket_B.send(http_message.encode()) # Envio el mensaje HTTP reconstruido al servidor destino
        print(f"Request enviada al servidor destino\n")


        # 3) PROXY <- DESTINO
        #response_raw = proxy_socket_B.recv(buff_size) #BUFFER NORMAL
        response_raw = recv_http_message(proxy_socket_B, 128)  #BUFFER PEQUEÑO
        print(f"Respuesta del servidor destino recibida:\n{response_raw.decode()}\n")

        response_raw_parsed = parse_HTTP_message(response_raw.decode())
        # saco el body (html) de la respuesta
        body_html = response_raw_parsed["body"]


        # Verifico si el html tiene palabras prohibidas
        # Si tiene no hago nada
        if sum(count_forbidden_words(data["forbidden_words"], body_html)) == 0:
            print("Todo bien\n")
            response = response_raw
        
        # Si no, las reemplazo y armo nuevo mensaje HTTP
        else:
            print("Se encontraron palabras prohibidas en el HTML\n")
            censored_html = procesar_html(body_html, data["forbidden_words"])
            # Armo nuevo mensaje HTTP con el HTML censurado y actualizo Content-Length
            censored_http_parsed_message = replace_body_http(response_raw_parsed, censored_html)
            response = create_HTTP_message(censored_http_parsed_message).encode()


        proxy_socket_B.close() # cierro conexion con servidor destino
        print(f"Conexión con {socket_B_address} ha sido cerrada\n")


    # 4) CLIENTE <- PROXY
    socket_A.send(response) # mando en bytes
    print(f"Respuesta al cliente enviada \n{response.decode()}\n")

    socket_A.close() # print(f"Conexión con {socket_A_address} ha sido cerrada\n")
    print(f"Conexión con {socket_A_address} ha sido cerrada\n")

