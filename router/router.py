import time
import csv
import networkx as nx

# Função para construir o grafo a partir do CSV
def construir_grafo_do_csv(caminho_csv):
    grafo = nx.Graph()
    with open(caminho_csv, newline='') as csvfile:
        leitor = csv.reader(csvfile)
        next(leitor)  # Pula o cabeçalho
        for origem, destino, custo in leitor:
            # Verifica se o custo é um número inteiro válido
            try:
                custo_int = int(custo)
                grafo.add_edge(origem.strip(), destino.strip(), weight=custo_int)
            except ValueError:
                print(f"Valor inválido para o custo entre {origem.strip()} e {destino.strip()}: {custo}. Ignorando essa linha.")
    return grafo

# Função para construir o pacote HELLO
def construir_pacote_hello(router_id, interface="eth0"):
    return {
        "type": "HELLO",
        "router_id": router_id,
        "timestamp": int(time.time()),
        "interface": interface
    }

# Função para construir o pacote LSA
def construir_pacote_lsa(router_id, vizinhos, numero_sequencia):
    return {
        "type": "LSA",
        "router_id": router_id,
        "timestamp": round(time.time(), 2),
        "sequence_number": numero_sequencia,
        "links": [{"neighbor_id": vizinho, "cost": custo} for vizinho, custo in vizinhos]
    }

# Função principal para simular o protocolo LSD
def simular_protocolo_lsd(caminho_csv):
    grafo = construir_grafo_do_csv(caminho_csv)
    numero_sequencia = 1
    for roteador in grafo.nodes:
        print(f"\n[ROTEADOR {roteador}] Enviando pacotes HELLO para vizinhos...")
        for vizinho in grafo.neighbors(roteador):
            pacote_hello = construir_pacote_hello(roteador)
            print(f"-> HELLO para {vizinho}: {pacote_hello}")

        vizinhos_info = [(vizinho, grafo[roteador][vizinho]["weight"]) for vizinho in grafo.neighbors(roteador)]
        pacote_lsa = construir_pacote_lsa(roteador, vizinhos_info, numero_sequencia)
        print(f"\n[ROTEADOR {roteador}] Pacote LSA gerado:")
        print(pacote_lsa)
        numero_sequencia += 1

if __name__ == "__main__":
    simular_protocolo_lsd("conexoes_rede.csv")
