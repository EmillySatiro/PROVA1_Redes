#!/bin/bash

echo "Iniciando testes de conectividade..."

# Lista de testes de host para host (ponta a ponta)
declare -a testes_host_para_host=(
  "router1_host1 -> router1_host2:router1_host1 ping 192.168.2.2"
  "router2_host1 -> router2_host2:router2_host1 ping 192.168.4.2"
  "router3_host1 -> router3_host2:router3_host1 ping 192.168.6.2"
  "router4_host1 -> router4_host2:router4_host1 ping 192.168.8.2"
  "router5_host1 -> router5_host2:router5_host1 ping 192.168.10.2"
)

# Testes entre hosts de roteadores diferentes (conectividade entre regiões)
declare -a testes_inter_hosts=(
  "router1_host1 -> router2_host1:router1_host1 ping 192.168.3.2"
  "router1_host1 -> router3_host1:router1_host1 ping 192.168.5.2"
  "router1_host1 -> router4_host1:router1_host1 ping 192.168.7.2"
  "router1_host1 -> router5_host1:router1_host1 ping 192.168.9.2"
)

# Testes entre roteadores diretamente conectados
declare -a testes_roteador_para_roteador=(
  "router1 -> router3:router1 ping 10.10.1.2"
  "router2 -> router3:router2 ping 10.10.2.2"
  "router2 -> router5:router2 ping 10.10.3.2"
  "router3 -> router4:router3 ping 10.10.5.2"
  "router3 -> router5:router3 ping 10.10.4.2"
)

echo ""
echo "====== Testes Host para Host ======"
for teste in "${testes_host_para_host[@]}"; do
    IFS=":" read -r descricao comando <<< "$teste"
    echo "Teste $descricao"
    docker exec -it ${comando% *} ${comando#* } -c 2
    echo ""
done

echo ""
echo "====== Testes Inter Hosts (Redes Diferentes) ======"
for teste in "${testes_inter_hosts[@]}"; do
    IFS=":" read -r descricao comando <<< "$teste"
    echo "Teste $descricao"
    docker exec -it ${comando% *} ${comando#* } -c 2
    echo ""
done

echo ""
echo "====== Testes entre Roteadores Conectados ======"
for teste in "${testes_roteador_para_roteador[@]}"; do
    IFS=":" read -r descricao comando <<< "$teste"
    echo "Teste $descricao"
    docker exec -it ${comando% *} ${comando#* } -c 2
    echo ""
done

echo "Todos os testes executados!"
