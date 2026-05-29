import socket
from random import randint

MAX_SIZE = 16  # 16 bytes
SERVER_ADDRESS = ("localhost", 8000)
CLIENT_ADDRESS = ("localhost", 8001)


# TCP: realiza handshake -> Envia datos -> termino de comunicacion
# Cliente envia SYN, y numero aleatoro seq=x:
# Si acepta, el Servidor envia SYN+ACK, seq=x+1
class SocketTCP:
    def __init__(self):
        # El constructor de esta clase deberá ser capaz de almacenar todos los recursos que va a necesitar para la comunicación
        # Su constructor no debe recibir parámetros
        # socket UDP: socket no orientado a conexión
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # dirección de destino: (IP_destino, puerto_destino)
        self.direccion_destino = None
        # dirección de origen: (IP_origen, puerto_origen)
        self.direccion_origen = None
        # número de secuencia: num aleatorio entre 0 y 100
        self.num_seq = randint(0, 100)
        # guardamos el buffer y los bytes pendientes
        self.buffer_interno = b""
        self.bytes_pendientes = 0

    def set_direccion_origen(self, origen):
        self.direccion_origen = origen

    def set_direccion_destino(self, destino):
        self.direccion_destino = destino

    def get_num_seq(self):
        return self.num_seq

    def set_num_seq(self, n):
        self.num_seq = n

    def set_socket(self, s):
        self.socket_udp = s

    @staticmethod
    def parse_segment(tcp_segment):
        # pasar segmentos TCP a alguna estructura de datos más cómoda
        # asumiendo el formato: 00000 + SYN + ACK + FIN + seq + data
        # definimos la estructura que almacenara los headers
        parsed_tcp = {}
        # extraemos el primer byte: 00000 + SYN + ACK + FIN
        headers_tcp = tcp_segment[0]
        # extraemos el num_seq, que corresponde a los siguientes 4 bytes
        num_seq = tcp_segment[1:5]
        seq = int.from_bytes(num_seq, "big")

        if headers_tcp == 5 or headers_tcp == 7:
            print("ERROR: header no valido")
            return parsed_tcp

        # ahora, extraemos los valores de SYN, ACK y FIN considerando
        # 00000100 -> SYN
        # 00000010 -> ACK
        # 00000001 -> FIN
        # 00000000 -> data

        parsed_tcp["SYN"] = (headers_tcp & 4) >> 2
        parsed_tcp["ACK"] = (headers_tcp & 2) >> 1
        parsed_tcp["FIN"] = headers_tcp & 1
        parsed_tcp["SEQ"] = seq
        parsed_tcp["data"] = tcp_segment[5:]

        return parsed_tcp

    @staticmethod
    def create_segment(parsed_tcp):
        # se crea los segmentos a partir de la estructura de datos parseada
        syn = parsed_tcp["SYN"]
        ack = parsed_tcp["ACK"]
        fin = parsed_tcp["FIN"]
        seq = parsed_tcp["SEQ"]
        data = parsed_tcp["data"]

        # formamos el primer byte: 00000 + SYN + ACK + FIN
        primer_byte = (syn << 2) | (ack << 1) | fin
        headers = primer_byte.to_bytes(1, "big")
        seq = seq.to_bytes(4, "big")

        # armamos los segmentos concatenando los bytes
        tcp_segment = headers + seq + data
        return tcp_segment

    # metodo para crear mensaje syn
    def create_syn_message(self):
        syn_msg = {}
        syn_msg["SYN"] = 1
        syn_msg["ACK"] = 0
        syn_msg["FIN"] = 0
        syn_msg["SEQ"] = self.get_num_seq()
        syn_msg["data"] = b""
        msg = self.create_segment(syn_msg)
        return msg

    # metodo para crear mensaje ack
    def create_ack_message(self, seq):
        syn_msg = {}
        syn_msg["SYN"] = 0
        syn_msg["ACK"] = 1
        syn_msg["FIN"] = 0
        syn_msg["SEQ"] = seq
        syn_msg["data"] = b""
        msg = self.create_segment(syn_msg)
        return msg

    # metodo para crear mensaje syn+ack
    def create_syn_ack_message(self, seq):
        syn_msg = {}
        syn_msg["SYN"] = 1
        syn_msg["ACK"] = 1
        syn_msg["FIN"] = 0
        syn_msg["SEQ"] = seq
        syn_msg["data"] = b""
        msg = self.create_segment(syn_msg)
        return msg

    def get_s_udp(self):
        # retorna el socket no orientado a conexion que se utilza en esta conexión
        return self.socket_udp

    def is_syn_msg(self, parsed_msg):
        # recibe un mensaje parseado y verifica si es tipo syn
        return (
            parsed_msg["SYN"] == 1 and parsed_msg["ACK"] == 0 and parsed_msg["FIN"] == 0
        )

    def is_syn_ack_msg(self, parsed_msg):
        # recibe un mensaje parseado y verifica si es tipo syn
        return (
            parsed_msg["SYN"] == 1 and parsed_msg["ACK"] == 1 and parsed_msg["FIN"] == 0
        )

    def is_ack_msg(self, parsed_msg):
        # recibe un mensaje parseado y verifica si es tipo syn
        return (
            parsed_msg["SYN"] == 0 and parsed_msg["ACK"] == 1 and parsed_msg["FIN"] == 0
        )

    def is_data_msg(self, parsed_msg):
        return (
            parsed_msg["SYN"] == 0 and parsed_msg["ACK"] == 0 and parsed_msg["FIN"] == 0
        )

    def create_data_segment(self, seq, data):
        data_msg = {}
        data_msg["SYN"] = 0
        data_msg["ACK"] = 0
        data_msg["FIN"] = 0
        data_msg["SEQ"] = seq
        data_msg["data"] = data
        msg = self.create_segment(data_msg)
        return msg

    # ===================== funciones de 3-way Handshake =====================
    def bind(self, address):
        # el socket realiza bind a hacia la direccion 'address'
        s = self.get_s_udp()
        self.set_direccion_origen(address)
        s.bind(address)
        print(f"... SocketTCP conectado a la direccion {address}...")

    def accept(self):
        # funcion del lado del servidor
        # el servidor debe:
        # esperar que le envien un mensaje SYN
        print("... Esperando mensaje SYN ...")
        s = self.get_s_udp()
        while True:
            # recibimos un mensaje
            raw_msg, client_addr = s.recvfrom(MAX_SIZE)
            # parseamos el mensaje recibido
            parsed_msg = self.parse_segment(raw_msg)
            # verificamos que sea un mensaje SYN
            if self.is_syn_msg(parsed_msg):
                print("... Mensaje tipo SYN ha sido recibido! ...")
                # extraemos el numero de seq = x
                syn_seq = parsed_msg["SEQ"]
                print(f"... SEQ = {syn_seq}")
                syn_ack_seq = syn_seq + 1
                # actualizamos el num_seq a x + 1
                self.set_num_seq(syn_ack_seq)
                # creamos y enviamos el mensaje SYN+ACK, con seq = x + 1
                print("... Creando mensaje SYN+ACK ...")
                syn_ack_msg = self.create_syn_ack_message(syn_ack_seq)

                print("... Enviando mensaje SYN+ACK ...")
                s.sendto(syn_ack_msg, client_addr)

                # esperamos el mensaje ACK
                print("... Esperamos el mensaje ACK ...")
                msg_raw, server_addr = s.recvfrom(MAX_SIZE)
                new_parsed_msg = self.parse_segment(msg_raw)

                if self.is_ack_msg(new_parsed_msg):
                    print("... Mensaje ACK recibido! ...")
                    # actualizamos el seq del SocketTCP
                    ack_seq = new_parsed_msg["SEQ"]
                    print(f"... SEQ = {ack_seq}")
                    # debemos retornar el socket que realiza la coneccion y la direccion
                    # creamos el socket para el cliente
                    new_s = SocketTCP()
                    new_s.set_socket(s)
                    new_s.set_direccion_origen(server_addr)
                    new_s.set_direccion_destino(client_addr)
                    new_s.set_num_seq(ack_seq)

                    print("... 3-way Handshake completado! ...")
                    return new_s, client_addr

    def connect(self, address):
        s = self.get_s_udp()
        s.bind(CLIENT_ADDRESS)
        # funcion del lado del cliente
        # el cliente debe enviar un mensaje SYN
        print("... Creamos un mensaje SYN ...")
        print(f"... Numero inicial de SEQ = {self.get_num_seq()}")
        syn_msg = self.create_syn_message()
        print("... Enviando mensaje SYN ...")
        s.sendto(syn_msg, address)

        while True:
            # esperar un mensaje SYN+ACK
            print("... Esperando mensaje SYN+ACK ...")
            raw_msg, _ = s.recvfrom(MAX_SIZE)
            parsed_msg = self.parse_segment(raw_msg)

            if self.is_syn_ack_msg(parsed_msg):
                syn_ack_seq = parsed_msg["SEQ"]
                print("... Recibido mensaje SYN+ACK ...")
                print(f"... SEQ = {syn_ack_seq}")
                # enviar un mensaje ACK
                ack_seq = syn_ack_seq + 1
                print("... Enviando mensaje ACK ...")
                ack_msg = self.create_ack_message(ack_seq)
                s.sendto(ack_msg, SERVER_ADDRESS)

                self.set_num_seq(ack_seq)
                self.set_direccion_destino(address)

                print("... 3-way Handshake completo! ...")
                return address

    # =================================== funciones de Stop & Wait ===================================

    def send(self, message):
        s = self.get_s_udp()
        # Esta función será la encargada de manejar Stop & Wait desde el lado del emisor
        # primero dividir el mensaje message en trozos de tamaño máximo 16 bytes
        # haga que el primer segmento enviado por la función send le informe al receptor el largo en bytes del
        # mensaje message que le va a enviar (message_length = len(message))
        # y luego, a partir del segundo segmento, comience a enviar el mensaje.
        # Note que send usa como número de secuencia inicial el último número de secuencia almacenado.

        split_msg = []  # arreglo donde guardar los trozos de 16 bytes
        i = 0
        while i < len(message):
            # dividir el mensaje en trozos de 16 bytes
            last = min(len(message), i + MAX_SIZE)
            split_msg.append(message[i:last])  # agregamos un trozo de 16 bytes o menos
            i = i + MAX_SIZE

        # primero informamos de message_length
        message_length = len(message)
        print(f"... Enviando mensaje de largo: {message_length}")
        largo_bytes = message_length.to_bytes(4, "big")  # enviamos un entero
        primer_seg = self.create_data_segment(self.get_num_seq(), largo_bytes)

        # enviamos al primer segmento
        while True:
            print("... enviamos primer segmento ...")
            s.sendto(primer_seg, self.direccion_destino)
            s.settimeout(5)
            try:
                msg, _ = s.recvfrom(MAX_SIZE + 5)
                parsed_msg = self.parse_segment(msg)
                if self.is_ack_msg(parsed_msg):
                    ack_seq = parsed_msg["SEQ"]
                    self.set_num_seq(ack_seq)
                    print(f"... ACK recibido, SEQ = {ack_seq}")
                    break
            except socket.timeout:
                print("...TIMEOUT, reenviando ...")

        # ahora enviamos cada segmento
        for segment in split_msg:
            num_seq = self.get_num_seq()
            split_seg = self.create_data_segment(num_seq, segment)
            while True:
                s.sendto(split_seg, self.direccion_destino)
                s.settimeout(5)
                try:
                    msg, _ = s.recvfrom(MAX_SIZE)
                    parsed_msg = self.parse_segment(msg)
                    if self.is_data_msg(parsed_msg):
                        seq_esperado = self.get_num_seq() + len(segment)
                        seq_obtenido = parsed_msg["SEQ"]
                        if seq_esperado == seq_obtenido:
                            self.set_num_seq(seq_obtenido)
                            print(f"... ACK, SEQ = {seq_obtenido}")
                        else:
                            print(
                                f"ACK no coincide: obtenido = {seq_obtenido} vs. esperado = {seq_esperado}"
                            )

                except socket.timeout:
                    print("... TIMEOUT, enviamos de nuevo ...")
        s.settimeout(None)
        print("READY")

    def recv(self, buff_size):
        s = self.get_s_udp()
        data_recibida = b""
        if self.bytes_pendientes == 0:
            # si no hay pendientes, es porque llega un mensaje
            print("... Esperando largo del mensaje ...")
            while True:
                msg, _ = s.recvfrom(buff_size)
                parsed_msg = self.parse_segment(msg)
                if self.is_data_msg(parsed_msg):
                    message_length = int.from_bytes(parsed_msg["data"], "big")
                    self.bytes_pendientes = message_length
                    print(f" ... Largo: {message_length} bytes")

        # si bytes_pendientes no es 0, entonces se esta enviando el mensaje
        # recibimos una cantidad fija de elementos: buff_size o bytes_pendientes(si quedan menos que buff_size)
        limit = min(self.bytes_pendientes, buff_size)
        # mientras queden datos, hay que acumularlos
        while len(data_recibida) < limit:
            # obtenemos mensaje
            msg, _ = s.recvfrom(buff_size)
            parsed_msg = self.parse_segment(msg)
            if self.is_data_msg(parsed_msg):
                # sacamos el numero seq
                seq_recibido = parsed_msg["SEQ"]
                # si el segmento es duplicado, el seq recibido sera menor que el seq del socket
                s_seq = self.get_num_seq()
                if seq_recibido < s_seq:
                    print(" ... SEG duplicado, reenviando")
                    ack_msg = self.create_ack_message(s_seq)
                    s.sendto(ack_msg, self.direccion_destino)
                    continue

                # si el segmento esta bien se agrega a data_recibida
                data_recibida = data_recibida + parsed_msg["data"]
                nuevo_seq = seq_recibido + len(parsed_msg["data"])
                new_ack_msg = self.create_ack_message(nuevo_seq)
                s.sendto(new_ack_msg, self.direccion_destino)
                self.set_num_seq(nuevo_seq)
                print(f"... data recibida, SEQ = {nuevo_seq}")

        self.bytes_pendientes = self.bytes_pendientes - len(data_recibida)

        print(
            f"... {len(data_recibida)} bytes recibidos, pendientes = {self.bytes_pendientes}"
        )
        return data_recibida
