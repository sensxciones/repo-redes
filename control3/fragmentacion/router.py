import socket
import sys
from pathlib import Path

# === variables globales
MAX_SIZE = 1024
HEADER_SIZE = 18

# Nuestro TTL corresponderá a un número entero entre 1 y 255. Se sugiere añadir el TTL como un elemento de 1 byte al final
# de su header original.
# Con esto su header utilizaría 7 bytes donde: los primeros 4 bytes representan la IP, los siguientes 2 bytes representan
# el puerto, el siguiente byte representa el TTL y los bytes restantes representan el mensaje.


# Permite extraer los headers y datos del paquete recibido,
# y lo pase a una estructura de datos conveniente
def parse_packet(IP_packet: bytes):
    # creamos el diccionario base
    parsed_ip_packet = {"ip": {}, "puerto": "", "mensaje": ""}
    # hay que dividir para obtener [Dirección IP],[Puerto] y [mensaje]
    ip_raw = IP_packet[0:4]
    puerto_raw = IP_packet[4:6]
    ttl_raw = IP_packet[6]
    id_raw = IP_packet[7:9]
    offset_raw = IP_packet[9:13]
    tamano_raw = IP_packet[13:17]
    flag_raw = IP_packet[17]
    msg_raw = IP_packet[HEADER_SIZE:]
    # extraemos los valores de la direccion ip a.b.c.d -> primeros 4 bytes
    parsed_ip_packet["ip"]["a"] = ip_raw[0]
    parsed_ip_packet["ip"]["b"] = ip_raw[1]
    parsed_ip_packet["ip"]["c"] = ip_raw[2]
    parsed_ip_packet["ip"]["d"] = ip_raw[3]

    # extraemos el valor del puerto -> obtenemos de los 2 bytes extraidos
    parsed_ip_packet["puerto"] = int.from_bytes(puerto_raw, "big")

    # guardamos el valor de ttl -> 1 byte
    parsed_ip_packet["ttl"] = int(ttl_raw)

    # campos usados para fragmentar y reensamblar
    parsed_ip_packet["id"] = int.from_bytes(id_raw, "big")
    parsed_ip_packet["offset"] = int.from_bytes(offset_raw, "big")
    parsed_ip_packet["tamano"] = int.from_bytes(tamano_raw, "big")
    parsed_ip_packet["flag"] = int(flag_raw)

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
    ttl = parsed_IP_packet["ttl"].to_bytes(1, "big")
    id_paquete = parsed_IP_packet["id"].to_bytes(2, "big")
    offset = parsed_IP_packet["offset"].to_bytes(4, "big")
    tamano = parsed_IP_packet["tamano"].to_bytes(4, "big")
    flag = parsed_IP_packet["flag"].to_bytes(1, "big")
    mensaje = get_message_bytes(parsed_IP_packet)
    # armamos la ip concatenando los numeros a, b, c y d
    # la idea es que el paquete quede de la forma: [Dirección IP][Puerto][ttl][mensaje]
    return a + b + c + d + puerto + ttl + id_paquete + offset + tamano + flag + mensaje


# obtiene msj en bytes del paquete parseado
def get_message_bytes(parsed_IP_packet):
    mensaje = parsed_IP_packet["mensaje"]
    if isinstance(mensaje, bytes):
        return mensaje
    return mensaje.encode("utf-8")


# Divide datagramas IP en fragmentos de tamaño MTU
# - Si cabe: retorna el paquete original en una lista de un solo elemento
# - Si no cabe: retorna una lista con los fragmentos del paquete original
def fragment_IP_packet(IP_packet, MTU):
    # Caso 1: el paquete completo, incluyendo header, cabe en el enlace
    if len(IP_packet) <= MTU:
        return [IP_packet]

    # Caso 2: el paquete no cabe, por lo que hay que partir solo el mensaje
    max_message_size = MTU - HEADER_SIZE
    if max_message_size <= 0:
        raise ValueError("El MTU debe ser mayor que el tamano del header")

    parsed_packet = parse_packet(IP_packet)
    mensaje = get_message_bytes(parsed_packet)
    fragments = []

    for i in range(0, len(mensaje), max_message_size):
        # Cada fragmento lleva como mensaje un trozo de largo maximo MTU-HEADER_SIZE
        fragment_message = mensaje[i : i + max_message_size]
        is_last_piece = i + max_message_size >= len(mensaje)

        parsed_fragment = {
            "ip": parsed_packet["ip"].copy(),
            "puerto": parsed_packet["puerto"],
            "ttl": parsed_packet["ttl"],
            "id": parsed_packet["id"],
            "offset": parsed_packet["offset"] + i, # posicion del trozo dentro del datagrama original
            "tamano": len(fragment_message), # bytes del mensaje que contiene este fragmento
            "flag": 0 if is_last_piece and parsed_packet["flag"] == 0 else 1, # =1 si aun quedan fragmentos despues; 0 si este cierra el datagrama
            "mensaje": fragment_message,
        }
        fragments.append(create_packet(parsed_fragment))

    return fragments


# Reensambla fragmentos de un datagrama IP en un solo paquete
# - Si paquete completo fue recibido lo retorna reensamblado
# - Si faltan fragmentos retorna None.
def reassemble_IP_packet(fragment_list):
    if len(fragment_list) == 0:
        return None

    parsed_fragments = [parse_packet(fragment) for fragment in fragment_list]

    # Si paquete completo: offset 0 y flag 0 => no falta nada mas
    if len(parsed_fragments) == 1:
        fragment = parsed_fragments[0]
        if fragment["offset"] == 0 and fragment["flag"] == 0:
            return fragment_list[0]
        return None

    parsed_fragments.sort(key=lambda fragment: fragment["offset"])

    # verificar que 1er fragmento tenga offset 0 y que no todos los fragmentos tengan flag 1
    if parsed_fragments[0]["offset"] != 0:
        return None
    if all(fragment["flag"] == 1 for fragment in parsed_fragments):
        return None

    expected_offset = 0
    full_message = b""

    for fragment in parsed_fragments:
        # si el offset del fragmento no es el esperado o el tamaño no es el correcto, retorna None
        if fragment["offset"] != expected_offset:
            return None

        fragment_message = get_message_bytes(fragment)
        if len(fragment_message) != fragment["tamano"]:
            return None

        full_message += fragment_message
        expected_offset += fragment["tamano"]

    # ultimo fragmento cierra el datagrama
    if parsed_fragments[-1]["flag"] != 0:
        return None

    first_fragment = parsed_fragments[0]
    reassembled_packet = {
        "ip": first_fragment["ip"].copy(),
        "puerto": first_fragment["puerto"],
        "ttl": first_fragment["ttl"],
        "id": first_fragment["id"],
        "offset": 0,
        "tamano": len(full_message),
        "flag": 0,
        "mensaje": full_message,
    }
    return create_packet(reassembled_packet)


# =============== EXTRAS ===============
# se extrae los numeros del ip y se arma
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
            # line = [Red (CIDR)] [Puerto_Inicial] [Puerto_final] [IP_Para_llegar] [Puerto_para_llegar] [MTU]
            route = line.split()
            puerto_inicial, puerto_final = int(route[1]), int(route[2])
            # si el puerto que buscamos esta en el rango de puertos, agregamos el par (ip, puerto) a rutas
            if destination_address[1] in range(puerto_inicial, puerto_final + 1):
                # ahora vemos si (puerto_inicial, puerto_final) esta en el diccionario
                next_hop_address = (route[3], int(route[4]))
                mtu = int(route[5])
                routes.append((next_hop_address, mtu))
    if len(routes) == 0:
        return None
    else:
        return routes


def get_puertos_inicial_final(routes_file_name, destination_address):
    with open(routes_file_name, "r") as file:
        for line in file:
            route = line.split()
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
    received_packets = {}
    while True:
        name_socket = Path(tabla_rutas).stem
        print(f"... {name_socket} esperando mensaje ...")
        paquete_ip, _ = s.recvfrom(MAX_SIZE)  # esperamos que llegue el mensaje
        parsed_packet = parse_packet(paquete_ip)  # parseamos el mensaje recibido
        # primero revisamos si el mensaje tiene TTL == 0
        if parsed_packet["ttl"] == 0:
            # si no cumple, se ignora el paquete y se imprime el mensaje
            print(f"Se recibió paquete [{paquete_ip}] con TTL 0")
            continue

        # obtenemos la direccion ip y el puerto del mensaje recibido
        destination_address = (
            get_ip_from_parsed(parsed_packet),
            parsed_packet["puerto"],
        )
        puerto = parsed_packet["puerto"]

        # si el mensaje recibido es para el router actual, imprimir mensaje
        if router_puerto == puerto:
            packet_id = parsed_packet["id"]
            if packet_id not in received_packets:
                received_packets[packet_id] = []
            received_packets[packet_id].append(paquete_ip)

            print("El mensaje es para este router!")
            print(
                f"Fragmentos/paquetes almacenados para ID {packet_id}: {len(received_packets[packet_id])}"
            )

            reassembled_packet = reassemble_IP_packet(received_packets[packet_id])
            if reassembled_packet is None:
                print("Aun no llegan todos los fragmentos.\n")
                continue

            reassembled_message = parse_packet(reassembled_packet)["mensaje"]
            print(f"Mensaje recibido: {reassembled_message}\n")
        else:
            # si no es para el socket acutal, revisamos si el socket tiene la ruta en el archivo
            rutas = check_routes(tabla_rutas, destination_address)
            if rutas is None:
                print(
                    f"No hay rutas hacia '{destination_address}' para paquete {paquete_ip}"
                )
            else:
                puertos = get_puertos_inicial_final(tabla_rutas, destination_address)
                if puertos not in state_routes.keys():
                    next_route = 0
                    state_routes[puertos] = (next_route + 1) % len(rutas)
                else:
                    next_route = state_routes[puertos]
                    state_routes[puertos] = (state_routes[puertos] + 1) % len(rutas)
                next_hop_address, mtu = rutas[next_route]
                # creamos una copia del paquete parseado
                new_parsed = parsed_packet
                # disminuimos en 1 su ttl
                parsed_packet["ttl"] = parsed_packet["ttl"] - 1
                # creamos un paquete nuevo en bytes y lo mandamos
                new_paquete_ip = create_packet(new_parsed)
                fragments = fragment_IP_packet(new_paquete_ip, mtu)
                print(
                    f"redirigiendo paquete {paquete_ip} con destino final {destination_address} desde {(router_IP, router_puerto)} hacia {next_hop_address} con MTU {mtu}. fragmentos: {len(fragments)}\n"
                )
                for fragment in fragments:
                    s.sendto(fragment, next_hop_address)
