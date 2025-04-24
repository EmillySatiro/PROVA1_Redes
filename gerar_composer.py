import networkx as nx
import random
import yaml
import networkx as nx
import matplotlib.pyplot as plt



# CONFIGURAÇÕES
num_roteadores = 5
hosts_por_roteador = 2

# Gerar grafo aleatório conectado
grafo = nx.connected_watts_strogatz_graph(num_roteadores, k=2, p=0.7)

# Gerar custos dos enlaces
for (u, v) in grafo.edges():
    grafo.edges[u, v]['weight'] = random.randint(1, 10)

# Começar a estrutura do docker-compose
compose = {
    'version': '3.8',
    'services': {},
    'networks': {}
}

# Criar roteadores e hosts
for r in grafo.nodes():
    router_name = f"router{r}"
    compose['services'][router_name] = {
        'build': './router',
        'networks': []
    }

    for h in range(hosts_por_roteador):
        host_name = f"host{r}_{h}"
        net_name = f"net_r{r}_h{h}"
        compose['services'][host_name] = {
            'build': './host',
            'networks': [net_name]
        }

        compose['networks'][net_name] = {'driver': 'bridge'}
        compose['services'][router_name]['networks'].append(net_name)

# Conectar os roteadores entre si
for (u, v, d) in grafo.edges(data=True):
    net_name = f"net_r{u}_r{v}"
    compose['networks'][net_name] = {'driver': 'bridge'}
    compose['services'][f'router{u}']['networks'].append(net_name)
    compose['services'][f'router{v}']['networks'].append(net_name)

# Salvar o docker-compose.yml
with open('docker-compose.yml', 'w') as f:
    yaml.dump(compose, f, sort_keys=False)

print("✅ docker-compose.yml gerado com sucesso!")

# Criar grafo visual da topologia
visual_grafo = nx.Graph()

# Adicionar routers como nós
for r in grafo.nodes():
    router_name = f"router{r}"
    visual_grafo.add_node(router_name, type='router')
    
    # Adicionar hosts conectados a esse router
    for h in range(hosts_por_roteador):
        host_name = f"host{r}_{h}"
        visual_grafo.add_node(host_name, type='host')
        visual_grafo.add_edge(router_name, host_name)

# Conectar os routers com base no grafo original
for (u, v) in grafo.edges():
    visual_grafo.add_edge(f"router{u}", f"router{v}")

# Definir cores: azul para hosts, verde para roteadores
node_colors = [
    'lightgreen' if data['type'] == 'router' else 'lightblue'
    for _, data in visual_grafo.nodes(data=True)
]


# Desenhar o grafo
plt.figure(figsize=(10, 8))
pos = nx.spring_layout(visual_grafo, seed=42)  # Layout bonito e fixo
nx.draw(
    visual_grafo,
    pos,
    with_labels=True,
    node_color=node_colors,
    node_size=1500,
    font_size=10,
    edge_color='gray'
)
plt.title("Topologia de Rede Gerada")
plt.show()
