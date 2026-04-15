# Cree un archivo llamado resolver.py.
# En él construya un código que le permita obtener mensajes DNS.
#  Para esto cree un socket apropiado que se encuentre asociado a la dirección (IP_VM, 8000)
# (¿Qué tipo de socket debe usar? Anótelo en su informe).
# Luego haga que su socket pueda recibir mensajes en un loop, aquí puede utilizar un tamaño de
# buffer "grande" pues en esta actividad no nos preocuparemos de manejar mensajes más grandes
#  que el tamaño del buffer.
# Finalmente haga que su código imprima en pantalla el mensaje recibido tal como se recibió, es decir, no utilice decode().

# Natalia:
# IP VM: 192.168.64.3
# IP HOST: 192.168.64.1

IP_HOST = "192.168.64.1"
IP_VM = "192.168.64.3"
