import time
import csv
import networkx as nx

import socket
import time
import json

class PacoteHello:
    def __init__(self, router_id, ip_address, neighbors):
        self.type = "HELLO"
        self.router_id = router_id
        self.timestamp = time.time()
        self.ip_address = ip_address
        self.known_neighbors = list(neighbors.keys())  

    def criar_pacote(self):
        """
        Cria a mensagem do pacote Hello no formato JSON.
        Retorna uma string com a mensagem.
        """
        pacote = {
            "type": self.type,
            "router_id": self.router_id,
            "timestamp": self.timestamp,
            "ip_address": self.ip_address,
            "known_neighbors": self.known_neighbors
        }
        return json.dumps(pacote)

class EmissorHello:
    def __init__(self, router_id, ip_address, neighbors, ip_broadcast='255.255.255.255', porta=5000, intervalo_hello=5):
        self.ip_broadcast = ip_broadcast
        self.porta = porta
        self.intervalo_hello = intervalo_hello
        self.soquete = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.soquete.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.router_id = router_id
        self.ip_address = ip_address
        self.neighbors = neighbors  # Dicionário de vizinhos
        self.pacote_hello = PacoteHello(self.router_id, self.ip_address, self.neighbors)  # Instancia da classe PacoteHello

    def enviar_hello(self):
        """
        Envia pacotes Hello a cada intervalo de tempo configurado.
        """
        while True:
            pacote = self.pacote_hello.criar_pacote()  # Cria o pacote
            self.soquete.sendto(pacote.encode(), (self.ip_broadcast, self.porta))  # Envia o pacote
            print(f"[ENVIADO] {pacote}")
            time.sleep(self.intervalo_hello)

if __name__ == "__main__":
    # Exemplo de uso com alguns dados fictícios
    router_id = 1
    ip_address = '192.168.1.1'
    neighbors = {'192.168.1.2': 'vizinho1', '192.168.1.3': 'vizinho2'}  # Exemplo de dicionário de vizinhos
    emissor = EmissorHello(router_id, ip_address, neighbors)  # Cria o emissor de pacotes Hello
    emissor.enviar_hello()  # Inicia o envio dos pacotes
