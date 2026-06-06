import socket
import sys

# === variables globales
MAX_SIZE = 1024
NUM_RUTAS = 0

# ===

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


# ==================================== Paso 6 ====================================
# Revisa en orden la tabla de rutas para indicar la dirección del siguiente salto
# Recibe como parámetros el nombre del archivo que contiene las rutas routes_file_name y
# la dirección de destino destination_address
# debe retornar el par (next_hop_IP, next_hop_puerto) que indica por dónde se debe enviar
# un paquete que se dirige a la dirección de destino destination_address
# Si al recorrer la tabla de rutas no encuentra una ruta apropiada, la función deberá retornar None
def check_routes(routes_file_name: str, destination_address: tuple[str, int]):
    # creamos una lista para almacenar las posibles rutas
    rutas = []
    # primero abrimos routes_file_name
    with open(routes_file_name, "r") as file:
        # revisamos cada linea del archivo
        for line in file:
            # line = [Red (CIDR)] [Puerto_Inicial] [Puerto_final] [IP_Para_llegar] [Puerto_para_llegar]
            route = line.split(" ")
            puerto_inicial, puerto_final = int(route[1]), int(route[2])
            # si el puerto que buscamos esta en el rango de puertos, agregamos el par (ip, puerto) a rutas
            if destination_address[1] in range(puerto_inicial, puerto_final + 1):
                rutas.append((route[3], int(route[4])))
    if len(rutas) == 0:
        return None
    else:
        return rutas


# ================================================================================

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

    while True:
        name_socket = f"Router {tabla_rutas[6:8]}"
        print(f"... {name_socket} esperando mensaje ...")
        paquete_ip, _ = s.recvfrom(MAX_SIZE)  # esperamos que llegue el mensaje
        parsed_packet = parse_packet(paquete_ip)  # parseamos el mensaje recibido
        # obtenemos la direccion ip y el puerto del mensaje recibido
        destination_address = get_ip_from_parsed(parsed_packet)
        puerto = parsed_packet["puerto"]

        # si el mensaje recibido es para el router actual, imprimir mensaje
        if router_puerto == puerto:
            mensaje = parsed_packet["mensaje"]
            print("El mensaje es para este router!")
            print(f"Mensaje recibido: {mensaje}")
            continue

        # si no es para el socket acutal, revisamos si el socket tiene la ruta en el archivo
        rutas = check_routes(tabla_rutas, (destination_address, puerto))
        if rutas is None:
            print(
                f"No hay rutas hacia '{destination_address}' para paquete [paquete_ip]"
            )
        else:
            # ahora revisamos la cantidad de camino que tiene rutas
            if len(rutas) == 1:
                # solo una ruta definida -> un solo par (ip, puerto) en rutas[0]
                print(
                    f"redirigiendo paquete {paquete_ip.decode()} con destino final {(destination_address, puerto)} desde {(router_IP, router_puerto)} hacia {rutas[0]}"
                )
                s.sendto(paquete_ip, rutas[0])
            else:
                # en el caso de existir mas de una ruta -> round-robin
                print("CASO: ROUND-ROBIN")
                s.sendto(paquete_ip, rutas[0])
