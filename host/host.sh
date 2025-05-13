#!/bin/bash 

# descobre o ip do container (baseao no padrão da interface) 
IP =$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

#define o gateway padrão como .2 
gateway=$(echo $IP | cut -d. -f1-3).2

#define o novo gateway

ip route del default 2>/dev/null
ip route add default via $gateway

echo "Novo gateway: $gateway"

#matem o container ativo 

while true; do
    sleep 1000
done