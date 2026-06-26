import socket
import sys

import router


if __name__ == "__main__":
    if len(sys.argv) < 10:
        raise Exception(
            "Formato: python send.py [IP_router_final] [puerto_router_final] "
            "[ttl] [id] [offset] [flag] [mensaje] [IP_envio] [puerto_envio]"
        )

    ip_router_final = sys.argv[1]
    num_ip = ip_router_final.split(".")
    a, b, c, d = int(num_ip[0]), int(num_ip[1]), int(num_ip[2]), int(num_ip[3])

    puerto_router_final = int(sys.argv[2])
    ttl = int(sys.argv[3])
    id_paquete = int(sys.argv[4])
    offset = int(sys.argv[5])
    flag = int(sys.argv[6])
    mensaje = sys.argv[7]
    tamano = len(mensaje.encode("utf-8"))

    parsed_packet_ip = {
        "ip": {"a": a, "b": b, "c": c, "d": d},
        "puerto": puerto_router_final,
        "ttl": ttl,
        "id": id_paquete,
        "offset": offset,
        "tamano": tamano,
        "flag": flag,
        "mensaje": mensaje,
    }

    packet_ip = router.create_packet(parsed_packet_ip)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip_envio = sys.argv[8]
    puerto_envio = int(sys.argv[9])
    s.sendto(packet_ip, (ip_envio, puerto_envio))
