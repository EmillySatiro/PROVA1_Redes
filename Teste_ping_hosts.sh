#!/bin/bash

# Caminho do docker-compose.yml
compose_file="docker-compose.yml"

# Arrays e Mapas
containers=()
declare -A ip_map

# Verifica se o arquivo docker-compose.yml existe
if [[ ! -f "$compose_file" ]]; then
  echo "Arquivo $compose_file não encontrado!"
  exit 1
fi

# Extrai containers e IPs do docker-compose.yml
container=""
while IFS= read -r line; do
  # Encontrar o nome do container
  if [[ $line =~ container_name:\ (.+) ]]; then
    container="${BASH_REMATCH[1]}"
  fi

  # Encontrar o IP dentro das redes
  if [[ $line =~ ipv4_address:\ (.+) ]]; then
    ip="${BASH_REMATCH[1]}"
    containers+=("$container")
    ip_map["$container"]="$ip"
  fi
done < "$compose_file"

# Cabeçalho
echo "🔁 Teste de conectividade entre TODOS os containers"
echo "==================================================="

# Loop de ping entre todos os containers (exceto a si mesmos)
for origem in "${containers[@]}"; do
  echo -e "\n🌐 Testando a partir de: $origem"
  for destino in "${containers[@]}"; do
    if [[ "$origem" == "$destino" ]]; then
      continue
    fi

    destino_ip="${ip_map[$destino]}"
    # Verifica se o IP do destino está vazio
    if [[ -z "$destino_ip" ]]; then
      echo "❌ IP de $destino não encontrado!"
      continue
    fi
    
    printf "Pingando %-12s (%-15s)... " "$destino" "$destino_ip"
    docker exec "$origem" ping -c 1 -W 1 "$destino_ip" &> /dev/null \
      && echo "✔️" || echo "❌"
  done
  echo "----------------------------------------------"
done
