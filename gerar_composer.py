import networkx as nx
import random
import yaml
import matplotlib.pyplot as plt
import csv

# CONFIGURAÇÕES
num_roteadores = 15
hosts_por_roteador = 2

# Gerar grafo conectado com pesos'
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
with open("router/conexoes_rede.csv", mode='w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Origem', 'Destino', 'Custo'])

    # Criar roteadores e hosts
    for r in grafo.nodes():
        router_name = f"router{r+1}"  
        router_networks = []

        for h in range(hosts_por_roteador):
            host_name = f"{router_name}_host{h+1}"  # Nomenclatura ajustada para router01_host01, router01_host02, etc.
            net_name = f"{router_name}_host{h+1}_net"
            subnet = f"192.168.{subrede_base}.0/24"
            ip_host = f"192.168.{subrede_base}.2"
            ip_router = f"192.168.{subrede_base}.10"

            # Host
            compose['services'][host_name] = {
                'build': './host',
                'container_name': host_name,
                'cap_add': ['NET_ADMIN'],
                'networks': {
                    net_name: {'ipv4_address': ip_host}
                }
            }

            # Rede
            compose['networks'][net_name] = {
                'driver': 'bridge',
                'ipam': {'config': [{'subnet': subnet}]}
            }

            router_networks.append({net_name: {'ipv4_address': ip_router}})
            writer.writerow([host_name, router_name, '-'])
            subrede_base += 1

        # Roteador
        compose['services'][router_name] = {
            'build': './router',
            'container_name': router_name,
            'environment': {
                'CONTAINER_NAME': f"router{r+1}",
            },
            'volumes': ['./router/router.py:/app/router.py'],
            'cap_add': ['NET_ADMIN'],
            'networks': {}
        }
        for net in router_networks:
            compose['services'][router_name]['networks'].update(net)

    # Conexões ponto-a-ponto entre roteadores
    for (u, v, d) in grafo.edges(data=True):
        router_u = f"router{u+1}"  # Ajuste para router01, router02, etc.
        router_v = f"router{v+1}"  # Ajuste para router01, router02, etc.
        net_name = f"{router_u}_{router_v}_net"
        subnet = f"10.10.{pontoaponto_base}.0/24"
        ip_u = f"10.10.{pontoaponto_base}.10"
        ip_v = f"10.10.{pontoaponto_base}.2"

        compose['networks'][net_name] = {
            'driver': 'bridge',
            'ipam': {'config': [{'subnet': subnet}]}
        }

        compose['services'][router_u]['networks'][net_name] = {'ipv4_address': ip_u}
        compose['services'][router_v]['networks'][net_name] = {'ipv4_address': ip_v}

        writer.writerow([router_u, router_v, d['weight']])
        pontoaponto_base += 1

# Salvar docker-compose.yml
with open('docker-compose.yml', 'w') as f:
    yaml.dump(compose, f, sort_keys=False)
print("✅ docker-compose.yml gerado!")

# Criar imagem da topologia
visual_grafo = nx.Graph()
for r in grafo.nodes():
    router_name = f"router{r+1:02d}"
    visual_grafo.add_node(router_name, type='router')
    for h in range(hosts_por_roteador):
        host_name = f"{router_name}_host{h+1:02d}"
        visual_grafo.add_node(host_name, type='host')
        visual_grafo.add_edge(router_name, host_name)

for (u, v) in grafo.edges():
    visual_grafo.add_edge(f"router{u+1:02d}", f"router{v+1:02d}")

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

