#!/bin/bash

#lista de host
hosts=()

#criar um vetor associativo com a estrutura ip -> container 
declare -A ip_roteadores

#contadores de sucersso e falha

sucersso=0
falha=0

#leitura do docker compose

while IFS= read -r line; do
    #verifica se a linha começa com "container" 
    if [[ $line == *"container"* ]]; then
        #extrai o nome do container 
        container=$(echo "$line" | awk -F' ' '{print $2}')
        #extrai o ip do container 
        ip=$(echo "$line" | awk -F' ' '{print $3}')
        #adiciona o ip e o nome do container no vetor associativo 
        hosts["$ip"]="$container"
    fi
done < docker-compose.yml

#adiciona os host 
ips=()
for ip in "${!ip_roteadores[@]}"; do
    container="${ip_roteadores[$ip]}"
    if [[ $container == *"container"* ]]; then
        ips+=("$ip")
    fi
done

#Teste de ping 

for oringem in "${hosts[@]}"; do
    for destino in "${hosts[@]}"; do
        #não testa a conectividade com o mesmo container 
        if [[ "$origem" != "$destino" ]]; then
            #testa a conectividade com o container 
            ping -c 1 "$destino" > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo "Conectividade de $origem para $destino: OK"
                ((sucersso++))
            else
                echo "Conectividade de $origem para $destino: Falha"
                ((falha++))
            fi
        fi
    done
done
#calculando a pocentagem de sucesso e falha
total=$((sucersso + falha))
echo -e "\n Resultados do teste de conectividade:"
echo "Total de testes: $total"
echo "Total de sucesso: $sucersso"
echo "Total de falha: $falha"

if((total > 0)); then 
perda=$(100 *falha / total)
echo "Perda de pacotes: $perda%"
else
echo "Total de testes: $total"
fi