import time
import socket
import threading
import json
import subprocess
import psutil
import os
import networkx as nx
import csv
import traceback


def carregar_grafo_com_pesos(csv_path):
    G = nx.Graph()
    with open(csv_path, newline='') as csvfile:
        leitor = csv.DictReader(csvfile)
        for linha in leitor:
            origem = linha['Origem']
            destino = linha['Destino']
            custo = linha['Custo']
            if custo != '-':
                G.add_edge(origem, destino, weight=int(custo))
            else:
                # Para conexões host-roteador
                G.add_edge(origem, destino, weight=1)
    return G


class EstadoRoteador:
    __slots__ = ["_tabela_roteamento", "_id_rota",
                 "_dados_vizinhos", "_roteamento"]

    def __init__(self, id_rota: str, dados_vizinhos: dict[str, str]):

        self._id_rota = id_rota
        self._tabela_roteamento = {}
        self._dados_vizinhos = dados_vizinhos
        self._roteamento = {}

    def _criar_entrada_tabela(self, numero_seq, timestamp, enderecos, links):

        return {
            "numero_sequencia": numero_seq,
            "timestamp": timestamp,
            "enderecos": enderecos,
            "links": links,
        }

    def atualizar_tabela(self, pacote):
        """
        🛠️ Atualiza a tabela com o pacote recebido.
        """
        id_rota = pacote["id_rota"]
        numero_seq = pacote["numero_sequencia"]

        print(f"Pacote recebido: {pacote}")

        entrada = self._tabela_roteamento.get(id_rota)
        if entrada and numero_seq <= entrada["numero_sequencia"]:
            print(f"Pacote ignorado (sequência antiga): {pacote}")
            return False

        print(f"Atualizando tabela de roteamento com id_rota {id_rota} e seq {numero_seq}")
        self._tabela_roteamento[id_rota] = self._criar_entrada_tabela(
            numero_seq, pacote["timestamp"], pacote["enderecos"], pacote["links"]
        )

        for vizinho in pacote["links"].keys():
            if vizinho not in self._tabela_roteamento:
                print(f"Novo roteador descoberto: {vizinho}")
                self._tabela_roteamento[vizinho] = self._criar_entrada_tabela(-1, 0, [], {})

        # CHAMADA DO ALGORITMO DE DIJKSTRA MANUAL
        rotas = self._calcular_rotas_minimas()
        
        self._atualizar_roteamento(rotas)
        self._aplicar_rotas()
        return True

    def _calcular_rotas_minimas(self):
        """
        Implementa o algoritmo de Dijkstra usando os dados em self._tabela_roteamento.
        """
        distancias = {n: float('inf') for n in self._tabela_roteamento}
        anteriores = {n: None for n in self._tabela_roteamento}
        visitados = set()

        distancias[self._id_rota] = 0

        while len(visitados) < len(self._tabela_roteamento):
            # Seleciona o nó com menor distância ainda não visitado
            no_atual = min((n for n in distancias if n not in visitados),
                        key=lambda n: distancias[n], default=None)

            if no_atual is None:
                break

            visitados.add(no_atual)
            vizinhos = self._tabela_roteamento[no_atual]["links"]

            for vizinho, custo in vizinhos.items():
                if vizinho in visitados:
                    continue
                nova_dist = distancias[no_atual] + custo
                if nova_dist < distancias[vizinho]:
                    distancias[vizinho] = nova_dist
                    anteriores[vizinho] = no_atual

        return anteriores


    def _atualizar_roteamento(self, caminhos: dict):
        self._roteamento.clear()
        for destino, gateway in caminhos.items():
            if destino != self._id_rota:
                pulo = destino
                while pulo and caminhos[pulo] != self._id_rota:
                    pulo = caminhos[pulo]
                if pulo:
                    self._roteamento[destino] = pulo
        self._roteamento = dict(sorted(self._roteamento.items()))

    def _aplicar_rotas(self):
        print("Tabela de roteamento atual:")
        for destino, dados in self._tabela_roteamento.items():
            print(f"  {destino}: {dados}")
        
        print("\nRotas calculadas:")
        for destino, gateway in self._roteamento.items():
            print(f"  {destino} -> {gateway}")
            
            if gateway in self._dados_vizinhos:
                ip_gateway = self._dados_vizinhos[gateway]
                for ip_destino in self._tabela_roteamento[destino]["enderecos"]:
                    print(f"  Aplicando rota: {ip_destino} via {ip_gateway}")
                    comando = ["ip", "route", "replace", ip_destino, "via", ip_gateway]
                    try:
                        subprocess.run(comando, check=True)
                        print("    ✅ Sucesso")
                    except subprocess.CalledProcessError as e:
                        print(f"    ❌ Falha: {e}")

def obter_interfaces_com_broadcast():

    interfaces = []
    for nome, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == socket.AF_INET:
                ip = snic.address
                broadcast = snic.broadcast
                if ip and broadcast:
                    interfaces.append({
                        "interface": nome,
                        "address": ip,
                        "broadcast": broadcast
                    })
    return interfaces


class EmissorPacoteHello:
    __slots__ = ["_id_rota", "_interfaces", "_vizinhos",
                 "_intervalo_envio", "_porta_comunicacao"]

    def __init__(self, id_rota: str, interfaces: list[dict[str, str]], vizinhos: dict[str, str], intervalo_envio: int = 10, porta_comunicacao: int = 5000):
        """
        Inicializa o emissor de pacotes HELLO, configurando o roteador, as interfaces e os vizinhos.

        Parâmetros:
        id_rota (str): Identificador do roteador.
        interfaces (list[dict]): Lista com informações das interfaces de rede.
        vizinhos (dict): Dicionário contendo os vizinhos com seus endereços IP.
        intervalo_envio (int, opcional): Intervalo entre os envios de pacotes (em segundos). Padrão é 10.
        porta_comunicacao (int, opcional): Porta utilizada para comunicação dos pacotes. Padrão é 5000.
        """
        self._id_rota = id_rota
        self._interfaces = interfaces
        self._vizinhos = vizinhos
        self._intervalo_envio = intervalo_envio
        self._porta_comunicacao = porta_comunicacao

    def _gerar_pacote_hello(self, ip_address: str):
        """
        Gera um pacote do tipo HELLO contendo as informações do roteador e seus vizinhos.

        Parâmetros:
        ip_address (str): Endereço IP da interface de envio do pacote.

        Retorna:
        dict: Pacote do tipo HELLO.
        """
        return {
            "tipo": "HELLO",
            "id_rota": self._id_rota,
            "timestamp": time.time(),
            "ip_address": ip_address,
            "vizinhos_conhecidos": list(self._vizinhos.keys()),
        }

    def _enviar_broadcast(self, ip_address: str, broadcast_ip: str):
        """
        Envia pacotes HELLO periodicamente para os vizinhos via broadcast.

        Parâmetros:
        ip_address (str): Endereço IP da interface.
        broadcast_ip (str): Endereço de broadcast para o envio dos pacotes.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while True:
            pacote = self._gerar_pacote_hello(ip_address)
            mensagem = json.dumps(pacote).encode("utf-8")

            try:
                sock.sendto(mensagem, (broadcast_ip, self._porta_comunicacao))
                print(f"[{self._id_rota}] Pacote HELLO enviado para {broadcast_ip}")
            except Exception as e:
                
                print(f"[{self._id_rota}] Erro ao enviar HELLO: {e}")

            time.sleep(self._intervalo_envio)

    def iniciar_emissao(self):
        """
        Inicia o envio de pacotes HELLO para os vizinhos através das interfaces configuradas.
        """
        for interface in self._interfaces:
            if "broadcast" in interface:
                ip = interface["address"]
                broadcast = interface["broadcast"]
                thread = threading.Thread(
                    target=self._enviar_broadcast, args=(ip, broadcast), daemon=True)
                thread.start()


class EmissorPacoteLSA:
    __slots__ = ["_id_rota", "_vizinhos_ip", "_vizinhos_custo", "_intervalo_envio",
                 "_porta_comunicacao", "_numero_sequencia", "_iniciado", "_lsdb", "_interfaces"]

    def __init__(self, id_rota: str, vizinhos_ip: dict[str, str], vizinhos_custo: dict[str, int],interfaces: list[dict[str, str]], lsdb: EstadoRoteador, intervalo_envio: int = 30, porta_comunicacao: int = 5000):
        self._id_rota = id_rota
        self._vizinhos_ip = vizinhos_ip
        self._vizinhos_custo = vizinhos_custo
        self._intervalo_envio = intervalo_envio
        self._porta_comunicacao = porta_comunicacao
        self._numero_sequencia = 0
        self._iniciado = False
        self._lsdb = lsdb
        self._interfaces = interfaces

    def _enviar_para_vizinhos(self):
            """
            Envia pacotes LSA periodicamente para TODOS os vizinhos.
            Diferente do encaminhar_vizinhos() que evita o remetente original.
            """
            while True:
                try:
                    # 1. Gera novo pacote LSA
                    pacote = self._gerar_pacote_lsa()
                    mensagem = json.dumps(pacote).encode("utf-8")
                    
                    # 2. Atualiza a própria tabela primeiro
                    self._lsdb.atualizar_tabela(pacote)
                    
                    # 3. Envia para todos os vizinhos
                    for vizinho_id, ip_vizinho in self._vizinhos_ip.items():
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                                sock.sendto(mensagem, (ip_vizinho, self._porta_comunicacao))
                                print(f"[LSA] Enviado para {vizinho_id} ({ip_vizinho})")
                        except Exception as e:
                            print(f"Erro ao enviar LSA para {vizinho_id}: {e}")
                    
                    # 4. Aguarda o intervalo
                    time.sleep(self._intervalo_envio)
                    
                except Exception as e:
                    print(f"Erro grave no envio periódico de LSA: {e}")
                    time.sleep(5)  # Espera antes de tentar novamente

    def encaminhar_vizinhos(self, pacote, ip_remetente):
        """Encaminha o LSA para todos os vizinhos exceto o remetente original."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        mensagem = json.dumps(pacote).encode("utf-8")
        
        for vizinho_id, ip_vizinho in self._vizinhos_ip.items():
            if ip_vizinho != ip_remetente:
                try:
                    sock.sendto(mensagem, (ip_vizinho, self._porta_comunicacao))
                    print(f"[{self._id_rota}] LSA encaminhado para {vizinho_id} ({ip_vizinho})")
                except Exception as e:
                    print(f"[{self._id_rota}] Erro ao encaminhar para {vizinho_id}: {e}")

    def _gerar_pacote_lsa(self):
        """Gera um novo LSA com informações atualizadas."""
        self._numero_sequencia += 1
        
        pacote = {
            "tipo": "LSA",
            "id_rota": self._id_rota,
            "ip_address": self._interfaces[0]["address"] if self._interfaces else "0.0.0.0",
            "timestamp": time.time(),
            "numero_sequencia": self._numero_sequencia,
            "enderecos": [item["address"] for item in self._interfaces],
            "links": self._vizinhos_custo.copy()
        }
    
        print(f"[{self._id_rota}] Gerado LSA (seq {self._numero_sequencia}): {pacote}")
        return pacote

    def iniciar_emissao(self):
        """Inicia o envio periódico de LSAs em thread separada."""
        if not self._iniciado:
            threading.Thread(target=self._enviar_para_vizinhos, daemon=True).start()
            self._iniciado = True
            print("Emissor LSA iniciado!")


class Roteador:
    """
    Classe que gerencia a operação do roteador, incluindo a comunicação com os vizinhos,
    manutenção da tabela de roteamento e envio de pacotes HELLO e LSA.
    """

    def __init__(self, router_id: str, porta_comunicacao: int = 5000, intervalo_envio: int = 10):
        self._router_id = router_id
        self._porta_comunicacao = porta_comunicacao
        self._intervalo_envio = intervalo_envio
        self._interfaces = self.obter_interfaces_com_broadcast()
        self._vizinhos = {} 
        self._vizinhos_reconhecidos = {}
        self._estado_roteador = EstadoRoteador(router_id, self._vizinhos_reconhecidos)
        self._grafo = carregar_grafo_com_pesos("conexoes_rede.csv")
        # Criando os emissores
        self._emissor_hello = EmissorPacoteHello(
            router_id, self._interfaces, self._vizinhos, intervalo_envio, porta_comunicacao)
        self._emissor_lsa = EmissorPacoteLSA(router_id, self._vizinhos_reconhecidos, self._vizinhos, self._interfaces, self._estado_roteador, intervalo_envio, porta_comunicacao)

    def obter_interfaces_com_broadcast(self):
        interfaces = []
        for nome, snics in psutil.net_if_addrs().items():
            for snic in snics:
                if snic.family == socket.AF_INET:
                    ip = snic.address
                    broadcast = snic.broadcast
                    if ip and broadcast:
                        interfaces.append({
                            "interface": nome,
                            "address": ip,
                            "broadcast": broadcast
                        })
        return interfaces

    def iniciar_comunicacao(self):
        # Inicializa o envio de pacotes HELLO e LSA em threads separadas
        threading.Thread(
            target=self._emissor_hello.iniciar_emissao, daemon=True).start()
        threading.Thread(
            target=self._emissor_lsa.iniciar_emissao, daemon=True).start()

    def processar_pacote(self, pacote):
        tipo_pacote = pacote.get("tipo")
        
        if tipo_pacote == "HELLO":
            self._processar_hello(pacote)
        elif tipo_pacote == "LSA":
            self._processar_lsa(pacote)
    def _processar_hello(self, pacote):
        """Processa pacotes HELLO recebidos."""
        try:
            id_emissor = pacote["id_rota"]
            if id_emissor != self._router_id:  # Ignora pacotes do próprio roteador
                print(f"[{self._router_id}] Recebido HELLO de {id_emissor}")
                
                # Verifica se é um vizinho conhecido no grafo
                if self._grafo.has_edge(id_emissor, self._router_id):
                    custo = self._grafo[id_emissor][self._router_id]["weight"]
                    self._vizinhos[id_emissor] = custo
                    
                    # Registra o IP do vizinho se estiver no pacote
                    if "ip_address" in pacote:
                        self._vizinhos_reconhecidos[id_emissor] = pacote["ip_address"]
                        print(f"[{self._router_id}] Registrado vizinho {id_emissor} - IP: {pacote['ip_address']}, Custo: {custo}")
        except Exception as e:
            print(f"[{self._router_id}] Erro ao processar HELLO: {e}")
            traceback.print_exc()
            
    def _processar_lsa(self, pacote):
        id_emissor = pacote["id_rota"]
        
        # Ignora pacotes do próprio roteador
        if id_emissor == self._router_id:
            return
        
        print(f"[{self._router_id}] Recebido LSA de {id_emissor} (seq: {pacote['numero_sequencia']})")
        
        # Verifica se o pacote é novo
        entrada_atual = self._estado_roteador._tabela_roteamento.get(id_emissor, {})
        seq_atual = entrada_atual.get("numero_sequencia", -1)
        seq_recebido = pacote["numero_sequencia"]
        
        if seq_recebido > seq_atual:
            print(f"[{self._router_id}] Atualizando tabela com LSA de {id_emissor}")
            self._estado_roteador.atualizar_tabela(pacote)
            
            # Encaminha para todos os vizinhos EXCETO quem enviou
            ip_remetente = pacote.get("ip_address")
            if ip_remetente:
                print(f"[{self._router_id}] Encaminhando LSA para outros vizinhos")
                self._emissor_lsa.encaminhar_vizinhos(pacote, ip_remetente)
            else:
                print(f"[{self._router_id}] LSA sem IP remetente, não encaminhado")
        else:
            print(f"[{self._router_id}] LSA antigo ignorado (seq {seq_recebido} <= {seq_atual})")

    def receber_pacotes(self):
        """
        Método responsável por ouvir pacotes na rede e processá-los.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self._porta_comunicacao))

        while True:
            try:
                data, address = sock.recvfrom(4096)
                pacote = json.loads(data.decode("utf-8"))
                if pacote is not None:
                    self.processar_pacote(pacote)
            except Exception as e:
                
                print(f"[{self._router_id}] Erro ao processar pacote: {e}")
                traceback.print_exc()

    def iniciar(self):
        # Inicia a comunicação com os vizinhos e começa a ouvir pacotes
        threading.Thread(target=self.receber_pacotes, daemon=True).start()
        self.iniciar_comunicacao()

        while True:
            time.sleep(1)


# Exemplo de uso
if __name__ == "__main__":
    router_id = os.getenv("CONTAINER_NAME")
    if (not router_id):
        raise ValueError(
            "NÃO ACHOU O NOME DO CONTAINER AHAHHAHAHAHAHA"
        )
    roteador = Roteador(router_id)
    roteador.iniciar()
