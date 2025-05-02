import time
import socket
import threading
import json
import subprocess
import psutil

class EstadoRoteador:
    __slots__ = ["_tabela_roteamento", "_id_rota", "_dados_vizinhos", "_roteamento"]

    def __init__(self, id_rota: str, dados_vizinhos: dict[str, str]):
        """
        🚀 Inicializa o roteador com ID e vizinhos.
        """
        self._id_rota = id_rota
        self._tabela_roteamento = {}
        self._dados_vizinhos = dados_vizinhos
        self._roteamento = {}

    def _criar_entrada_tabela(self, numero_seq, timestamp, enderecos, links):
        """
        🧩 Cria uma entrada na tabela de roteamento.
        """
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

        entrada = self._tabela_roteamento.get(id_rota)
        if entrada and numero_seq <= entrada["numero_sequencia"]:
            return False

        self._tabela_roteamento[id_rota] = self._criar_entrada_tabela(
            numero_seq, pacote["timestamp"], pacote["enderecos"], pacote["links"]
        )

        for vizinho in pacote["links"]:
            if vizinho not in self._tabela_roteamento:
                print(f"🆕 Novo roteador descoberto: {vizinho}")
                self._tabela_roteamento[vizinho] = self._criar_entrada_tabela(-1, 0, [], {})

        rotas = self._calcular_rotas_minimas()
        self._atualizar_roteamento(rotas)
        self._aplicar_rotas()
        return True

    def _calcular_rotas_minimas(self):
        """
        🗺️ Usa Dijkstra para calcular rotas mínimas.
        """
        distancias = {r: float('inf') for r in self._tabela_roteamento}
        caminhos = {r: None for r in self._tabela_roteamento}
        visitados = {}

        distancias[self._id_rota] = 0

        while len(visitados) < len(self._tabela_roteamento):
            roteador = min((n for n in distancias if n not in visitados), key=distancias.get, default=None)
            if roteador is None:
                break

            visitados[roteador] = True
            vizinhos = self._tabela_roteamento[roteador]["links"]

            for vizinho, custo in vizinhos.items():
                if vizinho not in visitados:
                    nova_distancia = distancias[roteador] + custo
                    if nova_distancia < distancias[vizinho]:
                        distancias[vizinho] = nova_distancia
                        caminhos[vizinho] = roteador

        return caminhos

    def _atualizar_roteamento(self, caminhos: dict):
        """
        🔄 Atualiza as rotas com base no melhor caminho.
        """
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
        """
        📡 Aplica as rotas calculadas no sistema operacional.
        """
        for destino, gateway in self._roteamento.items():
            if destino != self._id_rota:
                if gateway not in self._dados_vizinhos:
                    print(f"⚠️ Rota ignorada para {destino} via {gateway}: gateway desconhecido.")
                    continue

                for ip_destino in self._tabela_roteamento[destino]["enderecos"]:
                    ip_gateway = self._dados_vizinhos[gateway]
                    comando = ["ip", "route", "replace", ip_destino, "via", ip_gateway]

                    try:
                        subprocess.run(comando, check=True)
                        print(f"✅ Rota aplicada: {ip_destino} -> {ip_gateway}")
                    except subprocess.CalledProcessError as e:
                        print(f"❌ Erro ao aplicar rota: {comando} -> {e}")
class EmissorPacoteHello:
    __slots__ = ["_id_rota", "_interfaces", "_vizinhos", "_intervalo_envio", "_porta_comunicacao"]

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
    

  

    def obter_interfaces_com_broadcast():
        """
        🧼 Retorna uma lista de dicionários contendo nome da interface, endereço IP e broadcast.
        Usa psutil para maior compatibilidade com sistemas diferentes.
        """
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
                thread = threading.Thread(target=self._enviar_broadcast, args=(ip, broadcast), daemon=True)
                thread.start()


class EmissorPacoteLSA:
    __slots__ = ["_id_rota", "_vizinhos_ip", "_vizinhos_custo", "_intervalo_envio", "_porta_comunicacao", "_numero_sequencia", "_iniciado", "_lsdb", "_interfaces"]

    def __init__(self, id_rota: str, vizinhos_ip: dict[str, str], vizinhos_custo: dict[str, int], interfaces: list[dict[str, str]], lsdb: EstadoRoteador, intervalo_envio: int = 30, porta_comunicacao: int = 5000):
        """
        Inicializa o emissor de pacotes LSA, configurando os vizinhos e os parâmetros de envio.
        
        Parâmetros:
        id_rota (str): Identificador do roteador.
        vizinhos_ip (dict[str, str]): Dicionário contendo os IPs dos vizinhos.
        vizinhos_custo (dict[str, int]): Dicionário contendo os custos para os vizinhos.
        interfaces (list[dict[str, str]]): Lista com informações das interfaces de rede.
        lsdb (EstadoRoteador): Instância da classe EstadoRoteador para atualizar a tabela de roteamento.
        intervalo_envio (int, opcional): Intervalo entre os envios de pacotes (em segundos). Padrão é 30.
        porta_comunicacao (int, opcional): Porta utilizada para comunicação dos pacotes. Padrão é 5000.
        """
        self._id_rota = id_rota
        self._vizinhos_ip = vizinhos_ip
        self._vizinhos_custo = vizinhos_custo
        self._intervalo_envio = intervalo_envio
        self._porta_comunicacao = porta_comunicacao
        self._numero_sequencia = 0
        self._iniciado = False
        self._lsdb = lsdb
        self._interfaces = interfaces

    def _gerar_pacote_lsa(self):
        """
        Gera um pacote LSA (Link State Advertisement) para ser enviado aos vizinhos.
        
        Retorna:
        dict: Pacote LSA com informações sobre o estado do roteador.
        """
        self._numero_sequencia += 1
        return {
            "tipo": "LSA",
            "id_rota": self._id_rota,
            "timestamp": time.time(),
            "enderecos": [item["address"] for item in self._interfaces],
            "numero_sequencia": self._numero_sequencia,
            "links": self._vizinhos_custo.copy()
        }

    def _enviar_para_vizinhos(self):
        """
        Envia pacotes LSA periodicamente para os vizinhos configurados.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            pacote = self._gerar_pacote_lsa()
            mensagem = json.dumps(pacote).encode("utf-8")
            
            # Envia pacotes para cada vizinho
            for ip_vizinho in self._vizinhos_ip.values():
                try:
                    sock.sendto(mensagem, (ip_vizinho, self._porta_comunicacao))
                    print(f"[{self._id_rota}] Pacote LSA enviado para {ip_vizinho}")
                except Exception as e:
                    print(f"[{self._id_rota}] Erro ao enviar LSA: {e}")

            time.sleep(self._intervalo_envio)

    def iniciar_emissao(self):
        """
        Inicia o envio de pacotes LSA para os vizinhos. O processo é feito em uma thread separada.
        """
        if not self._iniciado:
            thread = threading.Thread(target=self._enviar_para_vizinhos, daemon=True)
            thread.start()
            self._iniciado = True
