import socket

import dnslib
from dnslib import DNSRecord

# Natalia:
# IP VM: 192.168.64.3
# IP HOST: 192.168.64.1

IP_HOST = "192.168.64.1"
IP_VM = "192.168.64.3"
# ========================================== funcion extra ==========================================
# Programe una función para parsear mensajes DNS. Es decir, programe una función que sea
# capaz de tomar un mensaje DNS y transformarlo a alguna estructura de datos manejable.
# Para esta parte podrá usar tanto hexadecimal con binascii como dnslib. Para crear sus
# funciones puede usar como guía la información y código presentado en la sección anterior
# Programando DNS con sockets.
# Si decide utilizar dnslib se recomienda revisar el material provisto más abajo en la sección
# Material e indicacciones para la actividad.
# Nota: Se recomienda guardar la siguiente información en su estructura:
# Qname, ANCOUNT, NSCOUNT, ARCOUNT, la sección Answer, la sección Authority y la sección Additional.
# =====================================================================================================
# creamos un socket no orientado a conexión
print(" ... Creando Socket ...\n")
socket_resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_address = (IP_HOST, 8000)

# recordar descargar dnslib con pip install dnslib

# Al igual que los servidores HTTP, los servidores DNS ocupan un puerto reservado,
# en este caso este corresponde al puerto 53.

if __name__ == "__main__":
    buffer_size = 4096
    # la idea es conectar el socket a (IP_VM, 8000)
    socket_resolver.bind(socket_address)
    print(f"Socket de DNS escuchando en {socket_address}\n")

    while True:
        message_bytes, client_addres = socket_resolver.recvfrom(buffer_size)
        print(f"Longitud del mensaje: {len(message_bytes)}\n")
        print(f"Mensaje recibido: \n{message_bytes}\n")
        break

    print(" ... Cerrando socket DNS ... ")
    socket_resolver.close()
