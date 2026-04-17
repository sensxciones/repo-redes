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


def get_rdata(parsed_msg):
    for ans in parsed_msg["answers"]:
        if ans["type"] == "A":
            return ans["rdata"]
    return None


def is_there_answer_type_a(parsed_msg, section):
    is_there_answer = False
    for ans in parsed_msg[section]:
        if ans["type"] == "A":
            is_there_answer = True
    return is_there_answer


def resolver_ns_recursivo(ns, msg_consulta):
    ns_query = DNSRecord.question(ns)
    ns_bytes = ns_query.pack()
    ns_response_bytes = resolver(ns_bytes)
    if ns_response_bytes:
        ns_parsed = parser_dns_message(ns_response_bytes)
        ns_ip = None
        for a in ns_parsed["answers"]:
            if a["type"] == "A":
                ns_ip = a["rdata"]
                break
        return ns_ip


# recibe el mensaje de query en bytes obtenido desde el cliente. Dentro de esta función, siga el siguiente
# procedimiento para obtener la respuesta:
def resolver(mensaje_consulta):
    # Envíe el mensaje query al servidor raíz de DNS y espere su respuesta. Se recomienda dejar la IP del
    # servidor raíz en una variable global de su programa.
    print(" .. Consultando servidor raiz ...\n")
    respuesta_bytes = send_dns_query(mensaje_consulta, SERVER_ADDRESS)

    if not respuesta_bytes:
        print("No se recibió respuesta")
        return None

    # Parseamos la respuesta a la estructura de diccionario
    respuesta_parsed = parser_dns_message(respuesta_bytes)

    # Si el mensaje answer recibido tiene la respuesta a la consulta, es decir, viene alguna respuesta
    # de tipo A en la sección Answer del mensaje, entonces simplemente haga que su función retorne el
    # mensaje recibido.

    # vemos si hay respuesta tipo A en la seccion Answer

    if respuesta_parsed["ancount"] > 0 and is_there_answer_type_a(
        respuesta_parsed, "answers"
    ):
        ip = get_rdata(respuesta_parsed)
        print(f"Encontrado {ip}\n")
        return response_bytes

    # Si la respuesta recibida corresponde a una delegación a otro Name Server, es decir, vienen
    # respuestas de tipo NS en la sección Authority, revise si viene alguna respuesta de tipo A en
    # la sección Additional.
    if respuesta_parsed["nscount"] > 0:
        print("... Delegación a otro Name Server... \n")
        is_there_answer = is_there_answer_type_a(respuesta_parsed, "additional")
        # Si encuentra una respuesta tipo A, entonces envíe la query del paso a) a la primera
        # dirección IP contenida en la sección Additional.
        if is_there_answer:
            # buscamos direccion IP en Additional
            ip_additional = []
            for add in respuesta_parsed["additional"]:
                if add["type"] == "A":
                    ip_additional.append(add["rdata"])

            if ip_additional:
                # Si encuentra una respuesta tipo A, entonces envíe la query del paso a) a la primera
                # dirección IP contenida en la sección Additional
                first_ip = ip_additional[0]
                print(f"... Consulta con IP de sección Additional: {first_ip} ...\n")
                respuesta_bytes = send_dns_query(mensaje_consulta, first_ip)
                if respuesta_bytes:
                    respuesta_parsed = parser_dns_message(respuesta_bytes)
                    if respuesta_parsed["ancount"] > 0 and is_there_answer_type_a(
                        respuesta_parsed, "answers"
                    ):
                        return respuesta_bytes
                    else:
                        resolver(respuesta_bytes)
            else:
                # Si no, tomamos el nombre de un Name Server desde la sección Authority y use recursivamente su función
                # para resolver la IP asociada al nombre de dominio del Name Server
                print("... No hay IP en Additional ...\n")
                ns_list = []
                for auth in respuesta_parsed["authority"]:
                    if auth["type"] == "NS":
                        ns_list.append(auth["rdata"])

                for ns in ns_list:
                    # hay que resolver la IP asociada recursivamente
                    ns_ip = resolver_ns_recursivo(ns, mensaje_consulta)
                    if ns_ip:
                        # enviar consulta
                        respuesta_bytes = send_dns_query(mensaje_consulta, ns_ip)
                        if respuesta_bytes:
                            respuesta_parsed = parser_dns_message(respuesta_bytes)
                            if is_there_answer_type_a(respuesta_parsed, "answer"):
                                return respuesta_bytes
                            else:
                                resolver(respuesta_bytes)
                        else:
                            print("No hay respuesta\n")
                    break
    # Si recibe algún otro tipo de respuesta simplemente ignórela
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
