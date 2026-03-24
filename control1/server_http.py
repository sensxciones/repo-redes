import socket

def parse_http_message(msg_bytes): 
    # esta función recibe un mensaje HTTP en bytes, lo parsea y devuelve una estructura de datos con la información relevante del mensaje HTTP (método, ruta, headers, body, etc.)
    pass

def create_http_message(esructura_datos): 
    # esta función recibe una estructura de datos con la información necesaria para crear un mensaje HTTP, y devuelve el mensaje HTTP en bytes listo para enviar al cliente
    pass

estructura = 0 # aca va la estructura de datos que se le pasará a create_http_message para crear el mensaje HTTP a enviar al cliente


if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 1024
    end_of_message = "\n"
    new_socket_address = ('localhost', 8000)

