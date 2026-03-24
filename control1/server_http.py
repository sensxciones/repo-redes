import socket

from utils import *

# Nicole:
# IP VM : 172.20.144.24
# IP Host : 10.42.80.80

IP_VM = "172.20.144.24"
IP_HOST = "10.42.80.80"

estructura = 0  # aca va la estructura de datos que se le pasará a create_http_message para crear el mensaje HTTP a enviar al cliente


if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 1024
    end_of_message = "\n"
    new_socket_address = (IP_VM, 8000)

    print("Creando socket - Servidor")
    # armamos el socket
    # los parámetros que recibe el socket indican el tipo de conexión
    # socket.SOCK_STREAM = socket orientado a conexión
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    server_socket.bind(new_socket_address)

    # luego con listen (función de sockets de python) le decimos que puede
    # tener hasta 3 peticiones de conexión encoladas
    # si recibiera una 4ta petición de conexión la va a rechazar
    server_socket.listen(3)

    while True:
        print("... Esperando clientes")
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        new_socket, new_socket_address = server_socket.accept()

        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
        recv_message = receive_full_message(new_socket, buff_size, end_of_message)

        print(f" -> Se ha recibido el siguiente mensaje: {recv_message}")

        # cerramos la conexión
        # notar que la dirección que se imprime indica un número de puerto distinto al 5000
        new_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")

        # seguimos esperando por si llegan otras conexiones
