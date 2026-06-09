import socket
import sys

# === variables globales
MAX_SIZE = 1024

# la idea es crear un diccionario que tenga la siguiente estructura:
# ["IP"] -> ["a"], ["b"], ["c"], ["d"] que represente a la direccion IP a.b.c.d
# ["Puerto"] -> que represente el pruerto (int -> bytes)
# ["mensaje"]
# Para esta actividad usaremos la siguiente estructura para nuestros paquetes IP: [Dirección IP][Puerto][mensaje]


# Permite extraer los headers y datos del paquete recibido,
# y lo pase a una estructura de datos conveniente
def parse_packet(IP_packet: bytes):
    # creamos el diccionario base
    parsed_ip_packet = {"ip": {}, "puerto": "", "mensaje": ""}
    # hay que dividir para obtener [Dirección IP],[Puerto] y [mensaje]
    ip_raw = IP_packet[0:4]
    puerto_raw = IP_packet[4:6]
    msg_raw = IP_packet[6:]
    # extraemos los valores de la direccion ip a.b.c.d -> primeros 4 bytes
    parsed_ip_packet["ip"]["a"] = ip_raw[0]
    parsed_ip_packet["ip"]["b"] = ip_raw[1]
    parsed_ip_packet["ip"]["c"] = ip_raw[2]
    parsed_ip_packet["ip"]["d"] = ip_raw[3]

    # extraemos el valor del puerto -> obtenemos de los 2 bytes extraidos
    parsed_ip_packet["puerto"] = int.from_bytes(puerto_raw, "big")

    # extraemos el mensaje que se envia
    parsed_ip_packet["mensaje"] = msg_raw.decode("utf-8")
    return parsed_ip_packet


# recibe la estructura de datos conveniente parsed_IP_packet que
# retorna la función parse_packet y crea un paquete IP de acuerdo
# a la estructura que usted definió
def create_packet(parsed_IP_packet):
    # extremos toda la informacion de la estructura
    a = parsed_IP_packet["ip"]["a"].to_bytes(1, "big")
    b = parsed_IP_packet["ip"]["b"].to_bytes(1, "big")
    c = parsed_IP_packet["ip"]["c"].to_bytes(1, "big")
    d = parsed_IP_packet["ip"]["d"].to_bytes(1, "big")
    puerto = parsed_IP_packet["puerto"].to_bytes(2, "big")
    mensaje = parsed_IP_packet["mensaje"].encode()
    # armamos la ip concatenando los numeros a, b, c y d
    # la idea es que el paquete quede de la forma: [Dirección IP][Puerto][mensaje]
    return a + b + c + d + puerto + mensaje


# =============== EXTRAS ===============
def get_ip_from_parsed(parsed_IP_packet):
    ip_raw = parsed_IP_packet["ip"]
    a, b, c, d = ip_raw["a"], ip_raw["b"], ip_raw["c"], ip_raw["d"]
    return f"{a}.{b}.{c}.{d}"


# ==============================================================================


# Revisa en orden la tabla de rutas para indicar la dirección del siguiente salto
# Recibe como parámetros el nombre del archivo que contiene las rutas routes_file_name y
# la dirección de destino destination_address
# debe retornar el par (next_hop_IP, next_hop_puerto) que indica por dónde se debe enviar
# un paquete que se dirige a la dirección de destino destination_address
# Si al recorrer la tabla de rutas no encuentra una ruta apropiada, la función deberá retornar None
def check_routes(routes_file_name: str, destination_address: tuple[str, int]):
    routes = []
    with open(routes_file_name, "r") as file:
        # revisamos cada linea del archivo
        for line in file:
            # line = [Red (CIDR)] [Puerto_Inicial] [Puerto_final] [IP_Para_llegar] [Puerto_para_llegar]
            route = line.split(" ")
            puerto_inicial, puerto_final = int(route[1]), int(route[2])
            # si el puerto que buscamos esta en el rango de puertos, agregamos el par (ip, puerto) a rutas
            if destination_address[1] in range(puerto_inicial, puerto_final + 1):
                # ahora vemos si (puerto_inicial, puerto_final) esta en el diccionario
                next_step = (route[3], int(route[4]))
                routes.append(next_step)
    if len(routes) == 0:
        return None
    else:
        return routes


def get_puertos_inicial_final(routes_file_name, destination_address):
    with open(routes_file_name, "r") as file:
        for line in file:
            route = line.split(" ")
            puerto_inicial, puerto_final = int(route[1]), int(route[2])
            if destination_address[1] in range(puerto_inicial, puerto_final + 1):
                return (puerto_inicial, puerto_final)
    return None


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
    state_routes = {}
    while True:
        name_socket = f"Router {tabla_rutas[6:8]}"
        print(f"... {name_socket} esperando mensaje ...")
        paquete_ip, _ = s.recvfrom(MAX_SIZE)  # esperamos que llegue el mensaje
        parsed_packet = parse_packet(paquete_ip)  # parseamos el mensaje recibido
        # obtenemos la direccion ip y el puerto del mensaje recibido
        destination_address = (
            get_ip_from_parsed(parsed_packet),
            parsed_packet["puerto"],
        )
        puerto = parsed_packet["puerto"]

        # si el mensaje recibido es para el router actual, imprimir mensaje
        if router_puerto == puerto:
            mensaje = parsed_packet["mensaje"]
            print("El mensaje es para este router!")
            print(f"Mensaje recibido: {mensaje}\n")
            break

        # si no es para el socket acutal, revisamos si el socket tiene la ruta en el archivo
        rutas = check_routes(tabla_rutas, destination_address)
        if rutas is None:
            print(
                f"No hay rutas hacia '{destination_address}' para paquete {paquete_ip}"
            )
        else:
            puertos = get_puertos_inicial_final(tabla_rutas, destination_address)
            if puertos not in state_routes.keys():
                state_routes[puertos] = 0
            else:
                state_routes[puertos] = (state_routes[puertos] + 1) % len(rutas)
            next_route = state_routes[puertos]
            print(f"VAMOS POR LA RUTA {next_route + 1}")
            print(
                f"redirigiendo paquete {paquete_ip} con destino final {destination_address} desde {(router_IP, router_puerto)} hacia {rutas[next_route]}\n"
            )
            s.sendto(paquete_ip, rutas[next_route])
