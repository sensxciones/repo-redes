import socket
from CongestionControl import CongestionControl
from socketUDP import SocketUDP
from slidingWindowCC import *
from random import randint

MAX_SIZE = 16  # 16 bytes
SERVER_ADDRESS = ("localhost", 8000)
CLIENT_ADDRESS = ("localhost", 8001)


# TCP: realiza handshake -> Envia datos -> termino de comunicacion
# Cliente envia SYN, y numero aleatoro seq=x:
# Si acepta, el Servidor envia SYN+ACK, seq=x+1
class SocketTCP:
    def __init__(self):
        '''El constructor de esta clase deberá ser capaz de almacenar todos los recursos que va a necesitar para la comunicación
        Parámetros:
        - socket_udp: socket no orientado a conexión que se va a usar para la comunicación
        - direccion_destino: tupla (IP_destino, puerto_destino) que se va a usar para enviar los mensajes
        - direccion_origen: tupla (IP_origen, puerto_origen) que se va a usar para recibir los mensajes
        - num_seq: número de secuencia que se va a usar para enviar los mensajes. Se inicializa con un número aleatorio entre 0 y 100.
        - buffer_interno: buffer donde se van a ir acumulando los datos recibidos, para luego ser retornados por la función recv. Se inicializa como un string vacío.
        - bytes_pendientes: cantidad de bytes que quedan por recibir. Se inicializa en 0 y se actualiza cuando se recibe el largo del mensaje a recibir. 
                            Se va actualizando a medida que se reciben los segmentos del mensaje.
        '''
        self.socket_udp = SocketUDP()
        self.direccion_destino = None # (IP_destino, puerto_destino)
        self.direccion_origen = None # (IP_origen, puerto_origen)
        self.num_seq = randint(0, 100)
        # guardamos el buffer y los bytes pendientes
        self.buffer_interno = b""
        self.bytes_pendientes = 0
        self.congestion_controler = CongestionControl(8)

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
    
    def send(self, message, mode="stop_and_wait"):
        '''Envía un mensaje utilizando el protocolo Stop & Wait como default, o Go-Back-N si se especifica'''

        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        if mode == "go_back_n":
            self.send_using_go_back_n(message)
    

    def recv(self, buff_size, mode="stop_and_wait"):
        '''Recibe un mensaje utilizando el protocolo Stop & Wait como default, o Go-Back-N si se especifica'''

        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        if mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

    # =================================== ACT CONTROL CONGESTION ===================================

    def send_using_stop_and_wait(self, message):
        '''Esta función será la encargada de manejar Stop & Wait desde el lado del emisor. 
        1. Divide el mensaje message en trozos de tamaño máximo 16 bytes
        2. Hace que el primer segmento enviado por la función send le informe al receptor el largo en bytes del mensaje message que le va a enviar (message_length = len(message))
        3. A partir del segundo segmento, comienza a enviar el mensaje.
        Note que send usa como número de secuencia inicial el último número de secuencia almacenado.'''

        s = self.get_s_udp()

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

    def recv_using_stop_and_wait(self, buff_size):
        '''Recibe un mensaje usando Stop & Wait. 
        1. Revisa si hay bytes pendientes por recibir. 
            - Si no hay: espera a recibir un mensaje que le informe el largo del mensaje que se va a enviar (message_length = len(message)). Luego, actualiza bytes_pendientes = message_length.
            - Si hay: espera a recibir el mensaje, y va acumulando los datos recibidos en data_recibida. 
        2. Cuando se recibe un segmento, se chequea si el número de secuencia del segmento es el esperado. 
            - Si no es el esperado, se reenvía un ACK con el número de secuencia que se esperaba recibir. 
            - Si el número de secuencia es el esperado, se actualiza el número de secuencia esperado, se envía un ACK con el nuevo número de secuencia esperado, y se agrega la data recibida a data_recibida.
        3. Cuando se reciben todos los bytes pendientes, se retorna data_recibida
        '''
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

        print(f"... {len(data_recibida)} bytes recibidos, pendientes = {self.bytes_pendientes}")
        return data_recibida
    

    def send_using_go_back_n(self, message):
        '''Esta función será la encargada de manejar Go-Back-N desde el lado del emisor.'''

        message_length = str(len(message)).encode()
        # dividimos el mensaje en trozos 
        data_list = self.divide_message(message, self.congestion_controler.get_MSS())
        window_size = self.congestion_controler.get_cwnd() // self.congestion_controler.get_MSS()
        print("\nEnviando mensaje de largo: ", len(message))

        # Inicializando ventana
        initial_seq = self.num_seq
        ventana = SlidingWindowCC(window_size, [message_length]+data_list, initial_seq)
        print("Ventana inicial:")
        print(ventana, "\n")

        # Inicio timer
        self.socket_udp.settimeout(5)
        self.socket_udp.set_timer_list_length(1)

        # enviar ventana inicial
        print("Enviando ventana inicial:")
        for i in range(window_size):
            data = ventana.get_data(i)

            if data is None:
                break
            
            seq = ventana.get_sequence_number(i)
            segment = self.create_data_segment(seq, data)

            print(f"- Enviado segmento con SEQ = {seq} y data = {data}")
            self.socket_udp.sendto(segment, self.direccion_destino, timer_index=0)

        print("Ventana inicial enviada.\n Esperando ACKs ...\n")


        while ventana.get_data(0) is not None: # mientras haya datos por enviar

            try:
                # Queda esperando un ACK
                answer, address = self.socket_udp.recvfrom(MAX_SIZE)

                print(f"ACK recibido")

                # Si el ACK es correcto
                parsed_ack = self.parse_segment(answer)
                
                if self.is_ack_msg(parsed_ack):
                    
                    ack_seq = parsed_ack["SEQ"]

                    # CONTROL DE CONGESTION: se informa al controlador que se recibió un ACK
                    self.congestion_controler.event_ack_received()
                    window_size = self.congestion_controler.get_MSS_in_cwnd()
                    ventana.update_window_size(window_size)


                    if self.socket_udp.timer_list[0] is not None:
                        self.socket_udp.stop_timer(timer_index=0) 

                    # Mover ventana
                    #ack_seq = parsed_ack["SEQ"]
                    print(f"ACK con SEQ = {ack_seq} recibido, moviendo ventana ...")

                    while ventana.get_data(0) is not None and ventana.get_sequence_number(0) < ack_seq:
                        ventana.move_window(1)

                    # Enviar nuevo segmento que entró en la ventana
                    new_data = ventana.get_data(window_size - 1) 
                    
                    print("\n Ventana actualizada:")
                    print(ventana, "\n")

                    if new_data is not None:
                        print(f"Enviamos segmento con SEQ = {ventana.get_sequence_number(window_size - 1)} y data = {new_data}")
                        self.num_seq = ventana.get_sequence_number(window_size - 1)
                        new_segment = self.create_data_segment(self.num_seq, new_data)
                        self.socket_udp.sendto(new_segment, self.direccion_destino, timer_index=0)
                        print("Nuevo segmento enviado, esperando ACKs ...")
                

            except TimeoutError:
                
                #CONTROL DE CONGESTIÓN: se informa al controlador que hubo un timeout
                self.congestion_controler.event_timeout() 
                window_size = self.congestion_controler.get_MSS_in_cwnd()
                ventana.update_window_size(window_size)

                # reenviar toda la ventana
                for i in range(window_size):
                    data = ventana.get_data(i)

                    if data is None:
                        break

                    seq = ventana.get_sequence_number(i)
                    segment = self.create_data_segment(seq, data)
                    self.socket_udp.sendto(segment, self.direccion_destino, timer_index=0)

        print("\nMensaje enviado exitosamente!\n============================\n")


    def recv_using_go_back_n(self, buff_size):
        '''Recibe un mensaje usando Go-Back-N.
        1. Revisa si hay bytes pendientes por recibir.
            - Si no hay: espera a recibir un mensaje que le informe el largo del mensaje que se va a enviar (message_length = len(message)). Luego, actualiza bytes_pendientes = message_length.
            - Si hay: espera a recibir el mensaje, y va acumulando los datos recibidos en data_recibida.'''
        print("Recibiendo mensaje usando Go-Back-N ...")
        
        data_recibida = b""

        # Recibir largo del mensaje
        if self.bytes_pendientes == 0:
            while True:
                print(f"Recibiendo largo del mensaje\n- Largo del mensaje a recibir: {buff_size}")
                msg, _ = self.socket_udp.recvfrom(buff_size)
                parsed_msg = self.parse_segment(msg)
                print(f"- Mensaje recibido: {parsed_msg}")

                if self.is_data_msg(parsed_msg): 
                    
                    self.bytes_pendientes = int(parsed_msg["data"].decode())

                    # enviar ACK
                    ack_seq = parsed_msg["SEQ"] + len(parsed_msg["data"])
                    ack_msg = self.create_ack_message(ack_seq)
                    self.socket_udp.sendto(ack_msg, self.direccion_destino)
                    self.set_num_seq(ack_seq)
                    print(f"- ACK enviado, SEQ = {ack_seq}")
                    break
            
            esperado = self.get_num_seq()
            print(f"SEQ esperado: {esperado}\n")

            # Recibir mensaje
            print(f"Recibiendo mensaje:")
            while len(data_recibida) < self.bytes_pendientes:
                msg, _ = self.socket_udp.recvfrom(buff_size)
                parsed_msg = self.parse_segment(msg)
                print(f"\nSegmento recibido: {parsed_msg}")

                if self.is_data_msg(parsed_msg):
                    seq_recibido = parsed_msg["SEQ"] 

                    # Segmento correcto
                    if seq_recibido == esperado:
                        print(f"- SEQ = {parsed_msg['SEQ']} y data = {parsed_msg['data']}")
                        data_recibida += parsed_msg["data"]
                        esperado += len(parsed_msg["data"])
                        print(f"- SEQ aumentado en {len(parsed_msg['data'])}, nuevo SEQ: {esperado}")
                        
                        print(f"- Enviando ACK: SEQ = {esperado}")
                        ack_msg = self.create_ack_message(esperado)
                        self.socket_udp.sendto(ack_msg, self.direccion_destino)

                        self.set_num_seq(esperado)


                    # Segmento fuera de orden
                    else:
                        print(f"SEQ no es el esperado, se recibió {seq_recibido}")

                        print("... Reenviando ACK ...")
                        ack_msg = self.create_ack_message(esperado)
                        self.socket_udp.sendto(ack_msg, self.direccion_destino)
                        print(f"Fuera de  orden. Esperaba SEQ = {esperado}. Recibido SEQ = {seq_recibido}. ")
                        print(f"Reenviado ACK con SEQ = {esperado}\n")
                
            self.bytes_pendientes = 0
            print(f"\nData final recibida: {data_recibida}")
            return data_recibida
        


    # ===================== funciones auxiliares =====================
    def divide_message(self, message, size):
        '''Divide el mensaje message en trozos de tamaño size. Retorna una lista con los trozos.'''
        return [message[i:i+size] for i in range(0, len(message), size)]