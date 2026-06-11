import socket
import sys

import routerv2 as router

if __name__ == "__main__":
    # formato de entrega:
    # python sendMessage.py [IP_router_final] [puerto_router_final] [ttl] [mensaje] [IP_envío] [puerto_envío]:
    if len(sys.argv) < 7:
        raise Exception(
            "Formato: python send-v2.py [IP_router_final] [puerto_router_final] [ttl] [mensaje] [IP_envío] [puerto_envío]"
        )
    # primero construimos el paquete_ip con [IP_router_final] [puerto_router_final] [mensaje]
    ip_router_final = sys.argv[1]
    num_ip = ip_router_final.split(".")
    a, b, c, d = int(num_ip[0]), int(num_ip[1]), int(num_ip[2]), int(num_ip[3])
    puerto_router_final = int(sys.argv[2])
    ttl = int(sys.argv[3])
    mensaje = sys.argv[4]

    # creamos la estructura diccionario
    parsed_packet_ip = {
        "ip": {"a": a, "b": b, "c": c, "d": d},
        "puerto": puerto_router_final,
        "mensaje": mensaje,
        "ttl": ttl,
    }
    # creamos el ip_packet con la estructura en bytes
    packet_ip = router.create_packet(parsed_packet_ip)
    parsed_v2 = router.parse_packet(packet_ip)
    # creamos un socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # extraemos [IP_envío] y [puerto_envío]
    ip_envio = sys.argv[5]
    puerto_envio = int(sys.argv[6])
    # enviamos el ip_packet a (IP_envío, puerto_envío)
    s.sendto(packet_ip, (ip_envio, puerto_envio))
