import random
import socket

import SocketTCP


def recv_con_perdidas(sockt, buff_size, loss_probability):
    while True:
        # recibimos el mensaje
        msg, addr = sockt.recvfrom(buff_size)
        # sacamos un número entre 0 y 100 de forma aleatoria
        random_number = random.randint(0, 100)
        # si el random_number es menor o igual a la probabilidad de perdida omitimos el mensaje
        if random_number <= loss_probability:
            continue
        # de lo contrario salimos del loop y retornamos
        else:
            break
    return msg, addr


def send_con_perdidas(sockt, message_in_bytes, loss_probability):
    # sacamos un número entre 0 y 100 de forma aleatoria
    random_number = random.randint(0, 100)
    # si el random_number es mayor o igual a la probabilidad de perdida enviamos el mensaje
    if random_number >= loss_probability:
        sockt.sendto(message_in_bytes)


if __name__ == "__main__":
    BYTES_SIZE = 16  # 16 bytes
    CLIENT_ADDRESS = ("localhost", 8001)
    SERVER_ADDRESS = ("localhost", 8000)

    # TEST - CLIENT
    client_socketTCP = SocketTCP.SocketTCP()
    client_socketTCP.connect(SERVER_ADDRESS)
    # test 1
    message = "Mensje de len=16".encode()
    client_socketTCP.send(message, mode="go_back_n")
    # test 2
    message = "Mensaje de largo 19".encode()
    client_socketTCP.send(message, mode="go_back_n")
    # test 3
    #message = "Mensaje de largo 19".encode()
    #client_socketTCP.send(message, mode="go_back_n")
