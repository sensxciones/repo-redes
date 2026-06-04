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
    parsed_ip_packet["puerto"] = int(puerto_raw.decode())

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
    puerto = str(parsed_IP_packet["puerto"])
    mensaje = str(parsed_IP_packet["mensaje"])
    # armamos la ip y la codificamos
    ip = f"{a}.{b}.{c}.{d}"
    # la idea es que el paquete quede de la forma: [Dirección IP];[Puerto];[mensaje]
    ip_packet = f"{ip};{puerto};{mensaje}"
    # retornamos el mensaje codificado en bytes
    return ip_packet.encode()


# =============== EXTRAS ===============
def get_ip_from_parsed(parsed_IP_packet):
    ip_raw = parsed_IP_packet["ip"]
    a, b, c, d = ip_raw["a"], ip_raw["b"], ip_raw["c"], ip_raw["d"]
    ip = f"{a}.{b}.{c}.{d}"
    return ip


# =======================================

# ==== Paso 6 ====


# Revisa en orden la tabla de rutas para indicar la dirección del siguiente salto
# Recibe como parámetros el nombre del archivo que contiene las rutas routes_file_name y
# la dirección de destino destination_address
# debe retornar el par (next_hop_IP, next_hop_puerto) que indica por dónde se debe enviar
# un paquete que se dirige a la dirección de destino destination_address
# Si al recorrer la tabla de rutas no encuentra una ruta apropiada, la función deberá retornar None
def check_routes(
    routes_file_name: str, destination_address: tuple[str, int]
) -> tuple[str, int] | None:
    # primero abrimos routes_file_name
    with open(routes_file_name, "r") as file:
        # revisamos cada linea del archivo
        for line in file:
            # line = [Red (CIDR)] [Puerto_Inicial] [Puerto_final] [IP_Para_llegar] [Puerto_para_llegar]
            route = line.split(" ")
            puerto_inicial, puerto_final = int(route[1]), int(route[2])
            # si el puerto que buscamos esta en el rango de la tabla de rutas, retornamos el siguiente paso
            if destination_address[1] in range(puerto_inicial, puerto_final + 1):
                return (route[3], int(route[4]))
    return None


# ================

if __name__ == "__main__":
    # chequeo si efectivamente tengo las tres cosas
    if len(sys.argv) < 4:
        raise Exception(
            "Formato: python3 router.py [router_IP] [router_puerto] [router_rutas.txt]"
        )
    # extraemos los elementos
    router_IP = sys.argv[1]
    router_puerto = int(sys.argv[2])
    tabla_rutas = sys.argv[3]

    # creamos socket bloqueante en el par (router_IP, router_puerto)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((router_IP, router_puerto))

    # ====================================== TEST ======================================
    # IP_packet_v1 = "127.0.0.1;8881;hola".encode()
    # esto lo deben crear de forma manual de acuerdo a la estructura que hayan definido
    # parsed_IP_packet = parse_packet(IP_packet_v1)
    # IP_packet_v2 = create_packet(parsed_IP_packet)
    # print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
    # ====================================================================================
    while True:
        name_socket = f"socket {tabla_rutas[6:8]}"
        print(f"... {name_socket} esperando mensaje ...")
        paquete_ip, _ = s.recvfrom(1024)  # esperamos que llegue el mensaje
        parsed_packet = parse_packet(paquete_ip)  # parseamos
        destination_address = get_ip_from_parsed(parsed_packet)
        puerto = parsed_packet["puerto"]
        # si el mensaje es para el router, imprimir mensaje
        if router_puerto == puerto:
            print("El mensaje es para este router!")
            break

        # revisamos si el socket tiene la ruta en el archivo
        if check_routes(tabla_rutas, (destination_address, puerto)) is None:
            print(
                f"No hay rutas hacia '{destination_address}' para paquete [paquete_ip]"
            )
            print(check_routes(tabla_rutas, (destination_address, puerto)))
        else:
            # si no: llame a la función check_routes y use la dirección que esta retorna para hacer forward del paquete
            pair = check_routes(tabla_rutas, (destination_address, puerto))
            print(
                f"redirigiendo paquete {paquete_ip} con destino final {destination_address} desde {router_IP} hacia {pair}"
            )
            s.sendto(paquete_ip, pair)
