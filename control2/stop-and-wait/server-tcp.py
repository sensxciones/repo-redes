import random

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
    # el servidor debe recibir los mensajes desde el cliente e imprimir el
    # contenido del archivo en salida estándar
    BYTES_SIZE = 16
    SERVER_ADDRESS = ("localhost", 8000)
    PROBABILITY = 5
    # creamos un socket UDP
    print("... Creando socket ...")
    # server_socketTCP = SocketTCP.SocketTCP()
    # server_socketTCP.bind(SERVER_ADDRESS)
    # connection_socketTCP, new_address = server_socketTCP.accept()

    # msg = ""
    # while True:
    #    print("... Esperando mensaje de cliente ...")
    # msg_bytes, address = socket_server.recvfrom(BYTES_SIZE)
    #    msg_buffer, addr = recv_con_perdidas(server_socketTCP, BYTES_SIZE, PROBABILITY)
    #    if msg_buffer is None or not msg_buffer:
    #        print("Perdida")
    #    else:
    #        msg += msg_buffer.decode()
    #        print(msg)
    #    if msg_buffer.decode() == "Done!":
    #        print(msg)
    #        break
    #    socket_server.sendto(b"Message recieved", addr)
    # socket_server.close()

    # TEST - SERVER
    server_socketTCP = SocketTCP.SocketTCP()
    server_socketTCP.bind(SERVER_ADDRESS)
    connection_socketTCP, new_address = server_socketTCP.accept()

    # test 1
    buff_size = 16
    full_message = connection_socketTCP.recv(buff_size)
    print("Test 1 received:", full_message)
    if full_message == "Mensje de len=16".encode():
        print("Test 1: Passed")
    else:
        print("Test 1: Failed")

    # test 2
    # buff_size = 19
    # full_message = connection_socketTCP.recv(buff_size)
    # print("Test 2 received:", full_message)
    # if full_message == "Mensaje de largo 19".encode():
    #    print("Test 2: Passed")
    # else:
    #    print("Test 2: Failed")

    # test 3
    # buff_size = 14
    # message_part_1 = connection_socketTCP.recv(buff_size)
    # message_part_2 = connection_socketTCP.recv(buff_size)
    # print("Test 3 received:", message_part_1 + message_part_2)
    # if (message_part_1 + message_part_2) == "Mensaje de largo 19".encode():
    #    print("Test 3: Passed")
    # else:
    #    print("Test 3: Failed")
