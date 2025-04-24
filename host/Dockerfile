# Este Dockerfile configura um ambiente Python leve usando a imagem oficial Python 3.10 slim.

FROM python:3.10-slim 
#    - Especifica a imagem base como Python 3.10 slim, que é uma imagem mínima com Python instalado.

WORKDIR /app
#    - Define o diretório de trabalho dentro do contêiner como "/app".
COPY host.py .
#- Copia o arquivo "host.py" do diretório local para o diretório de trabalho no contêiner.
CMD ["python", "host.py"]
#    - Define o comando padrão para executar o script "host.py" usando o interpretador Python.
