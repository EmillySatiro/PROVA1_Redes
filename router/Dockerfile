FROM python:3.10-slim

WORKDIR /app

# Copia o script router.py e o CSV a partir do diretório raiz (contexto de build)
COPY router.py .
COPY conexoes_rede.csv .

# Instala a biblioteca necessária
RUN pip install --no-cache-dir networkx

# Comando padrão ao iniciar o container
CMD ["python","-u", "router.py"]
