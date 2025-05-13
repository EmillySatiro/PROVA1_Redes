#!/bin/bash

#criar um vetor associativo com a estrutura ip_.container 
declare -A roteadores

#criar um lista ordenada de roteadores 
route=()

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
        roteadores["$ip"]="$container"
        #adiciona o ip na lista de roteadores 
        route+=("$ip")
    fi
done < docker-compose.yml

#coleta todos os ips 
ips=("${!roteadores[@]}")

#imprime 

echo "Teste de conectividade com os roteadores:"
echo "-------------------------------------"

#loop para testar a conectividade com os roteadores

for origem in "${ips[@]}"; do
    for destino in "${ips[@]}"; do
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

if ((total > 0)); then
    sucesso_percent=$((sucersso * 100 / total))
    falha_percent=$((falha * 100 / total))
else
    sucesso_percent=0
    falha_percent=0
fi