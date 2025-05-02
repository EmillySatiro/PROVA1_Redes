FROM python:3.10-slim

WORKDIR /app

# Copia o script router.py e o CSV a partir do diretório raiz (contexto de build)
COPY router.py .
COPY conexoes_rede.csv .

# Instala a biblioteca necessária
RUN pip install --no-cache-dir networkx
RUN apt-get update && apt-get install -y \
  iproute2 \
  iputils-ping \
  net-tools \
  nano \
  tcpdump \
  traceroute \
  && rm -rf /var/lib/apt/lists/*

# Instala psutil normalmente
RUN pip install psutil

# Ativa roteamento IP
RUN echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
 
# Comando padrão ao iniciar o container
CMD ["python","-u", "router.py"]
