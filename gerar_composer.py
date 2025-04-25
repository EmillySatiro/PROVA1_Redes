"""
Este script gera:
- docker-compose.yml com a topologia simulada (roteadores + hosts)
- Topologia_rede.png com o grafo visual
- conexoes_rede.csv com as conexões: Origem, Destino, Custo
"""

import networkx as nx
import random
import yaml
import matplotlib.pyplot as plt
import csv

# CONFIGURAÇÕES
num_roteadores = 5
hosts_por_roteador = 2

# Gerar grafo conectado com pesos
grafo = nx.connected_watts_strogatz_graph(num_roteadores, k=2, p=0.7)
for (u, v) in grafo.edges():
    grafo.edges[u, v]['weight'] = random.randint(1, 10)

compose = {
    'version': '3.8',
    'services': {},
    'networks': {}
}

subrede_base = 1
pontoaponto_base = 1

# CSV simplificado: Origem, Destino, Custo
with open("conexoes_rede.csv", mode='w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Origem', 'Destino', 'Custo'])

    # Criar roteadores e hosts
    for r in grafo.nodes():
        router_name = f"router{r}"
        router_networks = []

        for h in range(hosts_por_roteador):
            host_name = f"host{r}_{h}"
            net_name = f"net_r{r}_h{h}"
            subnet = f"192.168.{subrede_base}.0/24"
            ip_host = f"192.168.{subrede_base}.10"
            ip_router = f"192.168.{subrede_base}.1"

            # Host
            compose['services'][host_name] = {
                'build': './host',
                'networks': {
                    net_name: {'ipv4_address': ip_host}
                }
            }

            # Rede
            compose['networks'][net_name] = {
                'driver': 'bridge',
                'ipam': {'config': [{'subnet': subnet}]}
            }

            # Roteador
            router_networks.append({net_name: {'ipv4_address': ip_router}})

            # CSV: host → roteador
            writer.writerow([host_name, router_name, '-'])

            subrede_base += 1

        # Roteador final
        compose['services'][router_name] = {
            'build': './router',
            'networks': {}
        }
        for net in router_networks:
            compose['services'][router_name]['networks'].update(net)

    # Conectar roteadores entre si
    for (u, v, d) in grafo.edges(data=True):
        net_name = f"net_r{u}_r{v}"
        subnet = f"10.{pontoaponto_base}.0.0/30"
        ip_u = f"10.{pontoaponto_base}.0.1"
        ip_v = f"10.{pontoaponto_base}.0.2"

        compose['networks'][net_name] = {
            'driver': 'bridge',
            'ipam': {'config': [{'subnet': subnet}]}
        }

        compose['services'][f'router{u}']['networks'][net_name] = {'ipv4_address': ip_u}
        compose['services'][f'router{v}']['networks'][net_name] = {'ipv4_address': ip_v}

        # CSV: roteador ↔ roteador com custo
        writer.writerow([f"router{u}", f"router{v}", d['weight']])

        pontoaponto_base += 1

# Salvar docker-compose.yml
with open('docker-compose.yml', 'w') as f:
    yaml.dump(compose, f, sort_keys=False)
print("✅ docker-compose.yml gerado!")

# Criar imagem da topologia
visual_grafo = nx.Graph()
for r in grafo.nodes():
    router_name = f"router{r}"
    visual_grafo.add_node(router_name, type='router')
    for h in range(hosts_por_roteador):
        host_name = f"host{r}_{h}"
        visual_grafo.add_node(host_name, type='host')
        visual_grafo.add_edge(router_name, host_name)

for (u, v) in grafo.edges():
    visual_grafo.add_edge(f"router{u}", f"router{v}")

node_colors = [
    'lightgreen' if data['type'] == 'router' else 'lightblue'
    for _, data in visual_grafo.nodes(data=True)
]

plt.figure(figsize=(10, 8))
pos = nx.spring_layout(visual_grafo, seed=42)
nx.draw(
    visual_grafo,
    pos,
    with_labels=True,
    node_color=node_colors,
    node_size=1500,
    font_size=10,
    edge_color='gray'
)
plt.title("Topologia de Rede com Subredes e IPs")
plt.savefig("Topologia_rede.png", dpi=300)
plt.show()
