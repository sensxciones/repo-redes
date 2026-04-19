import socket


# Recibe un msj HTTP en bytes, lo parsea y devuelve una estructura de datos con la información relevante del mensaje HTTP (método, ruta, headers, body, etc.)
def parse_http_message(http_message):
    lines = http_message.split("\r\n")
    request_line = lines[0].split(" ")
    method = request_line[0]  # método HTTP (GET, POST, etc.)
    path = request_line[1]  # ruta solicitada ("/index.html")
    version = request_line[2]  # versión del protocolo HTTP (HTTP/1.1, HTTP/2,)
    headers = {} # parte vacío
    body = "" 
    is_body = False

    for line in lines[1:]:
        if line == "":
            is_body = True
        if is_body:
            body += line + "\n"
        else:
            header_parts = line.split(": ", 1)
            if len(header_parts) == 2:
                headers[header_parts[0]] = header_parts[1]

    # Estructura que representa un mensaje HTTP
    http_message_dict = {
        "method": method,
        "path": path,
        "version": version,
        "headers": headers,
    }

    if body:
        http_message_dict["body"] = (
            body.strip()
        )  # el método strip() se utiliza para eliminar los caracteres de nueva línea adicionales al final del cuerpo del mensaje HTTP

    return http_message_dict


# Recibe la estructura con la info del mensaje HTTP y devuelve el mensaje HTTP en bytes listo para enviar al cliente
def create_http_message(http_message_dict):
    http_message = ""
    http_message += f"{http_message_dict['method']} {http_message_dict['path']} {http_message_dict['version']}\r\n"
    for header, value in http_message_dict["headers"].items():
        http_message += f"{header}: {value}\r\n"
    http_message += "\r\n"
    if "body" in http_message_dict:
        http_message += http_message_dict["body"]
    return http_message


# esta función se encarga de recibir el mensaje completo desde el cliente.
# en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
# llegue el resto. Para saber si el mensaje ya llegó por completo, se busca el caracter de fin de mensaje (parte de nuestro protocolo inventado)
def receive_full_message(connection_socket, buff_size, end_sequence):

    # recibimos la primera parte del mensaje
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
    # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
    is_end_of_message = contains_end_of_message(
        full_message.decode("utf-8", errors="ignore"), end_sequence
    )

    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras el buffer no contenga secuencia de fin de mensaje
    while not is_end_of_message:
        # recibimos un nuevo trozo del mensaje
        recv_message = connection_socket.recv(buff_size)

        # lo añadimos al mensaje "completo"
        full_message += recv_message

        # verificamos si es la última parte del mensaje
        is_end_of_message = contains_end_of_message(
            full_message.decode("utf-8", errors="ignore"), end_sequence
        )

    # removemos la secuencia de fin de mensaje, esto entrega un mensaje en string
    full_message = remove_end_of_message(
        full_message.decode("utf-8", errors="ignore"), end_sequence
    )

    # finalmente retornamos el mensaje
    return full_message


# Verifica si el mensaje contiene la secuencia de fin de mensaje
def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)


# Elimina la secuencia de fin de mensaje del mensaje
def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

# verifica si el host está en la lista de páginas bloqueadas
def is_blocked(path, blocked_pages):
    if blocked_pages[-1] == '/':
        blocked_pages = blocked_pages[:-1]
    if path[-1] == '/':
        path = path[:-1]
    for page in blocked_pages:
        if path == page:
            return True
    return False

# lee todo el mensaje HTTP desde el socket 
def recv_http_message(socket, buff_size):
    data = b""
    # 1) leer hasta que lleguen los headers completos
    while b"\r\n\r\n" not in data:
        chunk = socket.recv(buff_size)
        if not chunk:
            break
        data += chunk
    # 2) headers completos, ahora sigo leyendo el resto (body)
    while True:
        chunk = socket.recv(buff_size)
        if not chunk:
            break
        data += chunk

    return data

# verifica si una palabra está en la lista de palabras prohibidas
def count_forbidden_words(forbidden_words, html):
    counts = []
    for w in forbidden_words:
        palabra = list(w.keys())[0]   # la "word" es la clave del dict
        counts.append(html.count(palabra))
    return counts

# reemplaza las palabras prohibidas en el HTML
def reemplazar_forbidden_words(forbidden_words, html):
    for w in forbidden_words:
        palabra = list(w.keys())[0]       # la palabra prohibida (clave del dict)
        reemplazo = w[palabra]            # el reemplazo (valor del dict)
        # reemplazo simple (con espacios alrededor para evitar falsos positivos)
        html = html.replace(palabra, reemplazo)
    return html


# Verifica si el HTML tiene palabras prohibidas y las reemplaza
def procesar_html(body_html, forbidden_words):
    # Ver cuántas veces aparecen
    counts = count_forbidden_words(forbidden_words, body_html)
    if sum(counts) == 0:
        # No hay palabras prohibidas
        print("No se encontraron palabras prohibidas")
        return body_html
    else:
        print("Se encontraron palabras prohibidas: ", counts)
        # Reemplazar todas 
        new_body_html = reemplazar_forbidden_words(forbidden_words, body_html)
        print(f"HTML modificado: {new_body_html}\n")
        return new_body_html


# Reemplaza el body del mensaje HTTP con un nuevo body
def replace_body_http(http_message_parsed, new_body):
    http_message_parsed['body'] = new_body # defino nuevo body
    http_message_parsed['headers']['Content-Length'] = str(len(new_body)) # actualizo Content-Length
    return http_message_parsed


