"""
Este script gera um arquivo `docker-compose.yml` configurado com uma topologia de rede simulada,
incluindo roteadores, hosts e conexões ponto-a-ponto entre roteadores. Além disso, ele cria uma
visualização gráfica da topologia de rede utilizando o NetworkX e Matplotlib.
"""
import networkx as nx
import random
import yaml
import matplotlib.pyplot as plt

# CONFIGURAÇÕES
num_roteadores = 20
hosts_por_roteador = 2

grafo = nx.connected_watts_strogatz_graph(num_roteadores, k=2, p=0.7)

for (u, v) in grafo.edges():
    grafo.edges[u, v]['weight'] = random.randint(1, 10)

compose = {
    'version': '3.8',
    'services': {},
    'networks': {}
}

subrede_base = 1  # para hosts: começa em 192.168.X.0/24
pontoaponto_base = 1  # para links: começa em 10.X.0.0/30

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
                net_name: {
                    'ipv4_address': ip_host
                }
            }
        }

        # Network bridge
        compose['networks'][net_name] = {
            'driver': 'bridge',
            'ipam': {
                'config': [{'subnet': subnet}]
            }
        }

        # Adiciona a mesma rede ao roteador
        router_networks.append({
            net_name: {'ipv4_address': ip_router}
        })

        subrede_base += 1

    compose['services'][router_name] = {
        'build': './router',
        'networks': {}
    }
    # insere depois para evitar sobrescrever
    for net in router_networks:
        compose['services'][router_name]['networks'].update(net)

# Conectar roteadores entre si com redes ponto-a-ponto
for (u, v, d) in grafo.edges(data=True):
    net_name = f"net_r{u}_r{v}"
    subnet = f"10.{pontoaponto_base}.0.0/30"
    ip_u = f"10.{pontoaponto_base}.0.1"
    ip_v = f"10.{pontoaponto_base}.0.2"

    compose['networks'][net_name] = {
        'driver': 'bridge',
        'ipam': {
            'config': [{'subnet': subnet}]
        }
    }

    # Adiciona rede aos roteadores com IP fixo
    compose['services'][f'router{u}']['networks'][net_name] = {
        'ipv4_address': ip_u
    }
    compose['services'][f'router{v}']['networks'][net_name] = {
        'ipv4_address': ip_v
    }

    pontoaponto_base += 1

# Salvar o docker-compose.yml
with open('docker-compose.yml', 'w') as f:
    yaml.dump(compose, f, sort_keys=False)

print("✅ docker-compose.yml gerado com IPs e subredes configuradas!")

# Criar o grafo visual
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
plt.show()
