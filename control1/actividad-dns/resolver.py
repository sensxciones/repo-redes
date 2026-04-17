import socket

import dnslib
import eol
from dnslib import DNSRecord
from dnslib.dns import QTYPE

# Natalia:
# IP VM: 192.168.64.3
# IP HOST: 192.168.64.1

IP_HOST = "192.168.64.1"
IP_VM = "192.168.64.3"


# ========================================== funcion extra ==========================================
# Programe una función para parsear mensajes DNS, que sea capaz de tomar un mensaje DNS y transformarlo
# a alguna estructura de datos manejable.
# Programando DNS con sockets.
# Nota: Se recomienda guardar la siguiente información en su estructura:
# Qname, ANCOUNT, NSCOUNT, ARCOUNT, la sección Answer, la sección Authority y la sección Additional.
def parser_dns_message(message_bytes):
    # guardar la siguiente información en su estructura:
    # Qname ANCOUNT, NSCOUNT, ARCOUNT
    dns_record = DNSRecord.parse(message_bytes)
    header = dns_record.header

    # extraemos QNAME
    if dns_record.q:
        qname = str(dns_record.q.qname)
    else:
        qname = ""

    # extraemos ANCOUNT, NSCOUNT, ARCOUNT
    ancount = header.a
    nscount = header.auth
    arcount = header.ar

    # extraemos la seccion Answer
    answers = []
    for rr in dns_record.rr:
        answers.append(
            {"name": str(rr.rname), "type": QTYPE.get(rr.rtype), "rdata": str(rr.rdata)}
        )

    # extraemos sección Authority
    authority = []
    if hasattr(dns_record, "auth") and dns_record.auth:
        for rr in dns_record.auth:
            authority.append(
                {
                    "name": str(rr.rname),
                    "type": QTYPE.get(rr.rtype),
                    "rdata": str(rr.rdata),
                }
            )
    # extraemos sección Additional
    additional = []
    if hasattr(dns_record, "ar") and dns_record.ar:
        for rr in dns_record.ar:
            additional.append(
                {
                    "name": str(rr.rname),
                    "type": QTYPE.get(rr.rtype),
                    "rdata": str(rr.rdata),
                }
            )
    return {
        "qname": qname,
        "ancount": ancount,
        "nscount": nscount,
        "arcount": arcount,
        "answers": answers,
        "authority": authority,
        "additional": additional,
    }


SERVER_ADDRESS = "192.33.4.12"
SERVER_PORT = 53
BUFFER_SIZE = 4096


def send_dns_query(query, ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(query, (ip, SERVER_PORT))
    response_bytes, _ = sock.recvfrom(BUFFER_SIZE)
    sock.close()
    return response_bytes


# recibe el mensaje de query en bytes obtenido desde el cliente. Dentro de esta función, siga el siguiente
# procedimiento para obtener la respuesta:
def resolver(mensaje_consulta):
    # Envíe el mensaje query al servidor raíz de DNS y espere su respuesta. Se recomienda dejar la IP del
    # servidor raíz en una variable global de su programa.
    print(" .. Consultando servidor raiz ... ")
    respuesta_bytes = send_dns_query(mensaje_consulta, SERVER_ADDRESS)
    respuesta = DNSRecord.parse(respuesta_bytes)

    ancount = respuesta.header.a
    nscount = respuesta.header.auth
    arcount = respuesta.header.ar

    # Si el mensaje answer recibido tiene la respuesta a la consulta, es decir, viene alguna respuesta de tipo A en
    # la sección Answer del mensaje, entonces simplemente haga que su función retorne el mensaje recibido.
    if ancount > 0:
        for rr in respuesta.rr:
            if rr.rtype == QTYPE.A:
                print(f"Respuesta encontrada: \n{rr.rdata}\n")
                return respuesta_bytes

    # Si la respuesta recibida corresponde a una delegación a otro Name Server, es decir, vienen respuestas de tipo
    # NS en la sección Authority, revise si viene alguna respuesta de tipo A en la sección Additional.
    if nscount > 0:
        print("... delegación a otro Name Server ...\n")
        ips_additional = []
        if arcount > 0 and hasattr(respuesta, "ar"):
            for rr in respuesta.ar:
                if rr.rtype == QTYPE.A:
                    ip = str(rr.rdata)
                    ips_additional.append(ip)
                    print(f"Encontramos IP en Additional: {ip}\n")
        #  i.- Si encuentra una respuesta tipo A, entonces envíe la query del paso a) a la primera dirección IP
        #      contenida en la sección Additional.
        if ips_additional:
            print(" ... Enviando consulta a Name Server ...\n")
            first_ip_address = ips_additional[0]
            respuesta_bytes = send_dns_query(mensaje_consulta, first_ip_address)
            print(f"{respuesta_bytes}\n")
            return None

        #  ii.- En caso de no encontrar alguna IP en la sección Additional, tome el nombre de un Name Server desde la
        #       sección Authority y use recursivamente su función para resolver la IP asociada al nombre de dominio del
        #       Name Server. Una vez obtenga la IP del Name Server, envíe la query obtenida en el paso a) a dicha IP.
        #       Una vez recibida la respuesta, vuelva al paso b).
        else:
            print("... No hay IP en sección Additional ...\n")

    # Si recibe algún otro tipo de respuesta simplemente ignórela
    print("Respuesta sin delegacion ni respuesta ")
    return None


# =====================================================================================================
# creamos un socket no orientado a conexión
print(" ... Creando Socket ...\n")
socket_resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_address = (IP_HOST, 8000)

# recordar descargar dnslib con pip install dnslib

# Al igual que los servidores HTTP, los servidores DNS ocupan un puerto reservado,
# en este caso este corresponde al puerto 53.

if __name__ == "__main__":
    # la idea es conectar el socket a (IP_VM, 8000)
    socket_resolver.bind(socket_address)
    print(f"Socket de DNS escuchando en {socket_address}\n")

    while True:
        message_bytes, client_addres = socket_resolver.recvfrom(BUFFER_SIZE)
        print(f"Longitud del mensaje: {len(message_bytes)}\n")
        print(f"Mensaje(en bytes) recibido: \n{message_bytes}\n")
        decoded_message_dns = parser_dns_message(message_bytes)
        print(f"Mensaje DNS parseado en json: \n {decoded_message_dns}\n")

        response_bytes = resolver(message_bytes)
        if response_bytes:
            socket_resolver.sendto(response_bytes, client_addres)
            print(f"Respuesta enviada: {client_addres}\n")
        else:
            print(f"No es posible resolver la consulta de {client_addres}")
        break

    print(" ... Cerrando socket DNS ... ")
    socket_resolver.close()
