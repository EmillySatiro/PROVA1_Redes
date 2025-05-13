#!/bin/bash

# Script para testar conectividade total da rede
# Este script verifica se cada host consegue pingar todos os outros hosts

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para obter o endereço IP correto de um container em suas redes
get_ip_addresses() {
    local container=$1
    local ips=()
    
    # Obter todas as redes do container
    local networks=$(docker inspect -f '{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}' $container)
    
    # Para cada rede, obter o IP correspondente
    for network in $networks; do
        local ip=$(docker inspect -f "{{with index .NetworkSettings.Networks \"$network\"}}{{.IPAddress}}{{end}}" $container)
        if [ ! -z "$ip" ]; then
            ips+=("$ip")
        fi
    done
    
    # Retornar os IPs encontrados
    echo "${ips[@]}"
}

# Função para testar ping entre dois containers
test_ping() {
    local source=$1
    local target=$2
    local target_ip=$3
    
    echo -n "  Ping de $source para $target ($target_ip): "
    
    # Executar ping a partir do container de origem
    PING_RESULT=$(docker exec $source ping -c 2 -w 2 $target_ip 2>&1)
    PING_STATUS=$?
    
    # Verificar o resultado do ping
    if [ $PING_STATUS -eq 0 ]; then
        # Extrair informações relevantes do resultado
        echo -e "${GREEN}✓ Sucesso${NC}"
        return 0
    else
        echo -e "${RED}✗ Falha${NC}"
        return 1
    fi
}

# Obter lista de todos os hosts
HOSTS=$(docker ps --format '{{.Names}}' | grep "_host[0-9]\+$")

echo -e "${CYAN}===========================================================${NC}"
echo -e "${CYAN}TESTE DE CONECTIVIDADE ENTRE HOSTS${NC}"
echo -e "${CYAN}===========================================================${NC}"

# Inicializar estatísticas globais
TOTAL_TESTS=0
TOTAL_SUCCESS=0
TOTAL_FAILURE=0

# Para cada host como origem
for HOST in $HOSTS; do
    echo -e "\n${MAGENTA}===========================================================${NC}"
    echo -e "${MAGENTA}TESTANDO CONECTIVIDADE A PARTIR DE: ${HOST}${NC}"
    echo -e "${MAGENTA}===========================================================${NC}"
    
    # Inicializar estatísticas para este host
    HOST_TOTAL=0
    HOST_SUCCESS=0
    HOST_FAILURE=0
    
    # Testar conectividade com todos os outros hosts
    echo -e "\n${BLUE}TESTE DE CONECTIVIDADE COM OUTROS HOSTS:${NC}"
    for TARGET_HOST in $HOSTS; do
        if [ "$HOST" != "$TARGET_HOST" ]; then
            # Obter IPs do host alvo
            TARGET_IPS=($(get_ip_addresses $TARGET_HOST))
            
            # Tentar pingar cada IP do host alvo
            PING_SUCCESS=0
            for TARGET_IP in "${TARGET_IPS[@]}"; do
                HOST_TOTAL=$((HOST_TOTAL+1))
                TOTAL_TESTS=$((TOTAL_TESTS+1))
                
                if test_ping "$HOST" "$TARGET_HOST" "$TARGET_IP"; then
                    HOST_SUCCESS=$((HOST_SUCCESS+1))
                    TOTAL_SUCCESS=$((TOTAL_SUCCESS+1))
                    PING_SUCCESS=1
                    break  # Se conseguir pingar pelo menos um IP, considera sucesso
                else
                    HOST_FAILURE=$((HOST_FAILURE+1))
                    TOTAL_FAILURE=$((TOTAL_FAILURE+1))
                fi
            done
            
            # Se não conseguiu pingar nenhum IP, registra uma tentativa falha
            if [ $PING_SUCCESS -eq 0 ] && [ ${#TARGET_IPS[@]} -eq 0 ]; then
                echo -e "  Ping de $HOST para $TARGET_HOST: ${RED}✗ Falha (nenhum IP encontrado)${NC}"
                HOST_TOTAL=$((HOST_TOTAL+1))
                HOST_FAILURE=$((HOST_FAILURE+1))
                TOTAL_TESTS=$((TOTAL_TESTS+1))
                TOTAL_FAILURE=$((TOTAL_FAILURE+1))
            fi
        fi
    done
    
    # Exibir resumo para este host
    echo -e "\n${YELLOW}RESUMO PARA $HOST:${NC}"
    echo "Total de hosts testados: $HOST_TOTAL"
    echo -e "Hosts alcançáveis: ${GREEN}$HOST_SUCCESS${NC}"
    echo -e "Hosts não alcançáveis: ${RED}$HOST_FAILURE${NC}"
    
    # Calcular taxa de sucesso para este host
    if [ $HOST_TOTAL -gt 0 ]; then
        SUCCESS_RATE=$(( (HOST_SUCCESS * 100) / HOST_TOTAL ))
        echo -e "Taxa de sucesso: $SUCCESS_RATE%"
    fi
done

# Exibir resumo global
echo -e "\n${CYAN}===========================================================${NC}"
echo -e "${CYAN}RESUMO GLOBAL DOS TESTES${NC}"
echo -e "${CYAN}===========================================================${NC}"
echo "Total de testes realizados: $TOTAL_TESTS"
echo -e "Testes bem-sucedidos: ${GREEN}$TOTAL_SUCCESS${NC}"
echo -e "Testes com falha: ${RED}$TOTAL_FAILURE${NC}"

# Calcular taxa de sucesso global
if [ $TOTAL_TESTS -gt 0 ]; then
    GLOBAL_SUCCESS_RATE=$(( (TOTAL_SUCCESS * 100) / TOTAL_TESTS ))
    echo -e "Taxa de sucesso global: $GLOBAL_SUCCESS_RATE%"
fi

# Gerar relatório de conectividade
echo -e "\n${CYAN}===========================================================${NC}"
echo -e "${CYAN}GERANDO RELATÓRIO DE CONECTIVIDADE${NC}"
echo -e "${CYAN}===========================================================${NC}"

# Contar número de hosts
NUM_HOSTS=$(echo "$HOSTS" | wc -w)
echo -e "Número total de hosts: $NUM_HOSTS"

# Verificar conectividade total
if [ $GLOBAL_SUCCESS_RATE -eq 100 ]; then
    echo -e "\n${GREEN}✓ CONECTIVIDADE TOTAL ENTRE HOSTS${NC}"
    echo "Todos os hosts conseguem alcançar todos os outros hosts da rede."
elif [ $GLOBAL_SUCCESS_RATE -ge 80 ]; then
    echo -e "\n${YELLOW}⚠ CONECTIVIDADE PARCIAL ENTRE HOSTS${NC}"
    echo "A maioria dos hosts consegue alcançar a maioria dos outros hosts da rede."
    echo "Verifique os logs acima para identificar problemas específicos."
else
    echo -e "\n${RED}✗ PROBLEMAS SIGNIFICATIVOS DE CONECTIVIDADE${NC}"
    echo "Há problemas graves de conectividade entre os hosts."
    echo "Revise as configurações de roteamento e as tabelas de rotas."
fi

exit 0