import socket
import sys

# la idea es crear un diccionario que tenga la siguiente estructura:
# ["IP"] -> ["a"], ["b"], ["c"], ["d"] que represente a la direccion IP a.b.c.d
# ["Puerto"] -> que represente el pruerto (int -> bytes)
# ["mensaje"]
# Para esta actividad usaremos la siguiente estructura para nuestros paquetes IP:
# [Dirección IP];[Puerto];[mensaje]


# Permite extraer los headers y datos del paquete recibido,
# y lo pase a una estructura de datos conveniente
def parse_packet(IP_packet: bytes):
    # creamos el diccionario
    parsed_ip_packet = {"ip": {}, "Puerto": ""}
    # hay que dividir según ";" para obtener [Dirección IP];[Puerto];[mensaje]
    raw_data = IP_packet.split(b";")
    ip_raw, puerto_raw, msg_raw = raw_data[0], raw_data[1], raw_data[2]
    # dividimos la ip segun .
    ip_num = ip_raw.split(b".")
    # extraemos los valores de la direccion ip a.b.c.d -> primeros 4 elementos
    parsed_ip_packet["ip"]["a"] = int(ip_num[0])
    parsed_ip_packet["ip"]["b"] = int(ip_num[1])
    parsed_ip_packet["ip"]["c"] = int(ip_num[2])
    parsed_ip_packet["ip"]["d"] = int(ip_num[3])

    # extraemos el valor del puerto -> decodificar
    parsed_ip_packet["Puerto"] = int(puerto_raw.decode())

    # extraemos el mensaje que se envia
    parsed_ip_packet["mensaje"] = msg_raw.decode("utf-8")
    return parsed_ip_packet


# recibe la estructura de datos conveniente parsed_IP_packet que
# retorna la función parse_packet y crea un paquete IP de acuerdo
# a la estructura que usted definió
def create_packet(parsed_IP_packet):
    # extremos toda la informacion de la estructura
    a = parsed_IP_packet["ip"]["a"]
    b = parsed_IP_packet["ip"]["b"]
    c = parsed_IP_packet["ip"]["c"]
    d = parsed_IP_packet["ip"]["d"]
    puerto = str(parsed_IP_packet["Puerto"])
    mensaje = str(parsed_IP_packet["mensaje"])
    # armamos la ip y la codificamos
    ip = f"{a}.{b}.{c}.{d}"
    # la idea es que el paquete quede de la forma: [Dirección IP];[Puerto];[mensaje]
    ip_packet = f"{ip};{puerto};{mensaje}"
    # retornamos el mensaje codificado en bytes
    return ip_packet.encode()


if __name__ == "__main__":
    # chequeo si efectivamente tengo las tres cosas
    if len(sys.argv) < 3:
        raise Exception(
            "El formato de uso corresponde: python3 router.py router_IP router_puerto router_rutas.txt"
        )
    # extraemos los elementos
    router_IP = sys.argv[1]
    router_puerto = int(sys.argv[2])
    tabla_rutas = sys.argv[3]

    # creamos socket bloqueante en el par (router_IP, router_puerto)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((router_IP, router_puerto))

    # ==== TEST ====
    # IP_packet_v1 = "127.0.0.1;8881;hola".encode()
    # esto lo deben crear de forma manual de acuerdo a la estructura que hayan definido
    # parsed_IP_packet = parse_packet(IP_packet_v1)
    # IP_packet_v2 = create_packet(parsed_IP_packet)
    # print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
