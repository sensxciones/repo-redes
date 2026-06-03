import sys

if __name__ == "__main__":
    # chequeo si efectivamente tengo las tres cosas
    if len(sys.argv) < 3:
        raise Exception(
            "El formato de uso corresponde: python3 router.py router_IP router_puerto router_rutas.txt"
        )
    # extraemos los elementos
    router_ip = sys.argv[1]
    router_puerto = sys.argv[2]
    tabla_rutas = sys.argv[3]

    print(
        f"Router IP: {router_ip}\nPuerto Router: {router_puerto}\nArchivo: {tabla_rutas}"
    )
    with open(tabla_rutas) as f:
        print(f.read())
