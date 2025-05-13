#!/bin/bash 

# Descobre o IP do container (baseado no padrão da interface eth0)
IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

# Verifica se encontrou o IP corretamente
if [ -z "$IP" ]; then
    echo "Erro: não foi possível obter o IP da interface eth0."
    exit 1
fi

# Define o gateway padrão como .2 
gateway=$(echo $IP | cut -d. -f1-3).2

# Remove rota default antiga, se existir, e define a nova rota default via $gateway
ip route del default 2>/dev/null
ip route add default via $gateway

echo "Novo gateway: $gateway"

# Mantém o container ativo
while true; do
    sleep 1000
done
