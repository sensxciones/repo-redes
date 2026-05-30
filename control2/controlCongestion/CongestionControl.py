
# Nicole Charun y Natalia Valencia

class CongestionControl:
    '''Clase para manejar el control de congestión de forma ordenada
    
    Mecanismos de control de congestión de TCP Tahoe:
    - Slow Start: El tamaño de la ventana de congestión (cwnd) comienza en 1 MSS (Maximum Segment Size) y se duplica cada vez que se recibe un ACK, hasta alcanzar el umbral de congestión (ssthresh).
    - Congestion Avoidance: Una vez que cwnd alcanza ssthresh, el crecimiento de cwnd se vuelve lineal, aumentando en 1 MSS por cada ronda de ACKs recibidos.
    - Timeout: Si se detecta una pérdida de paquete (por ejemplo, por un timeout), ssthresh se establece a la mitad de cwnd, y cwnd se reinicia a 1 MSS, volviendo al estado de Slow Start.

    Codigo sigue siendo una versión simplificada de TCP
    
    '''

    def __init__(self, initial_window_size=1):
        '''Constructor de la clase CongestionControl.
        Parámetros:
        - initial_window_size: int, tamaño inicial de la ventana de congestión en MSS. Por defecto es 1 MSS.
        - current_state: str, estado actual dentro de control de congestión. Puede ser "slow_start" o "congestion_avoidance". Se inicializa en "slow_start".
        - MSS: int, tamaño máximo en bytes del área de datos de un segmento congestion. Se inicializa con el valor de initial_window_size.
        - cwnd: int, tamaño actual de la ventana de congestión en bytes. Se inicializa con 1 MSS, y siempre es un múltiplo de MSS.
        - ssthresh: int, Slow start threshold. Se define luego del primer timeout durante slow start, antes de ser definida debe ser igual a None.        
        '''

        self.current_state = "slow_start" # estado actual dentro de control de congestion: slow_start o congestion_avoidance
        self.MSS = initial_window_size # indica tamaño maximo en bytes del area de datos de un segmento congestion
        self.cwnd = self.MSS # tamaño actual de la ventana de congestión en bytes. Se inicializa con 1 MSS, y siempre es un múltiplo de MSS
        self.ssthresh = None  # Slow start threshold. Se define luego del primer timeout durante slow start, antes de ser definida debe ser igual a None.
        # Cuando current_state es slow_start:
        # - Si cwnd >= ssthresh, cambia a congestion_avoidance
        # - Si cwnd < ssthresh, se mantiene en slow_start
        # Cuando current_state es congestion_avoidance:
        # - Si cwnd >= ssthresh, se mantiene current_state en congestion_avoidance
        # - Si cwnd < ssthresh, cambia a slow_start


    def get_cwnd(self):
        '''Retorna el valor cwnd almacenado, que representa el tamaño actual de la ventana de congestión en bytes'''
        return self.cwnd # en bytes

    def get_MSS_in_cwnd(self):
        '''Retorna el número de MSS que caben en la ventana de congestión actual'''
        return self.cwnd // self.MSS # cantidad de MSS que caben en la ventana de congestión actual
    

    def event_ack_received(self):
        '''Función que se encarga de manejar los cambios asociados a la recepción de ACKs.
        
            Si current_state es slow_start: 
            - Recibir un ACK hace que cwnd aumente en 1 MSS (cwnd *= 2) por cada ronda de ACKs recibidos, hasta alcanzar ssthresh.

            Si current_state es congestion_avoidance:
            - Cada aumento corresponde a una fracción 1/self.get_MSS_in_cwnd() de un MSS por cada ACK recibido
            - Si después de recibir un ACK, cwnd >= ssthresh, se cambia current_state a congestion_avoidance

            Al aumentar el cwnd chequea si el aumento genera un cambio en current_state, y lo actualiza en caso de ser necesario:
            - Si current_state es slow_start y cwnd >= ssthresh, cambia current_state a congestion_avoidance
            - Si current_state es congestion_avoidance y cwnd < ssthresh, cambia current_state a slow_start
        '''

        # SLOW START
        if self.current_state == "slow_start":
            self.cwnd += self.MSS

            # cambio de estado
            if self.ssthresh is not None and self.cwnd >= self.ssthresh:
                self.current_state = "congestion_avoidance"

        # CONGESTION AVOIDANCE
        elif self.current_state == "congestion_avoidance":
            self.cwnd += self.MSS / self.get_MSS_in_cwnd()

            # cambio de estado
            if self.ssthresh is not None and self.cwnd < self.ssthresh:
                self.current_state = "slow_start"


    def event_timeout(self):
        '''Función que se encarga de manejar los cambios asociados a que ocurra un timeout.

        Por ejemplo, si es la primera vez que ocurre timeout dentro de slow start entonces deberá inicializar el valor de ssthresh. 
        Esta función también deberá manejar los cambios de estado, de tamaño de ventana de congestión y de Slow Start threshold.

        '''

        # ssthresh = cwnd/2
        self.ssthresh = int(self.cwnd / 2)

        # volver a 1 MSS
        self.cwnd = self.MSS

        # volver a slow start
        self.current_state = "slow_start"

        
    def is_state_slow_start(self):
        '''Retorna True si el estado actual es slow_start, y False en caso contrario'''
        return self.current_state == "slow_start"
    
    def is_state_congestion_avoidance(self):
        '''Retorna True si el estado actual es congestion_avoidance, y False en caso contrario'''
        return self.current_state == "congestion_avoidance"

    def get_ssthresh(self):
        '''Retorna el valor de ssthresh, que representa el umbral de congestión.'''
        return self.ssthresh
    
    def get_MSS(self):
        '''Retorna el valor de MSS, que representa el tamaño máximo en bytes del área de datos de un segmento congestion.'''
        return self.MSS
    