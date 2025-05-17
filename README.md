# 🚀 Simulação de Topologia de Redes Distribuídas Utilizando Docker e Automação

## 📖 Descrição Geral

Este projeto implementa uma plataforma avançada para simulação de topologias de redes de computadores utilizando **Docker**, **Python** e **Shell Script**. A solução permite criar e orquestrar múltiplos hosts e roteadores em containers isolados, possibilitando análises realistas de comunicação, roteamento e comportamento em redes distribuídas. O sistema automatiza a configuração e oferece ferramentas para validação da conectividade entre os dispositivos simulados, funcionando como um ambiente robusto para experimentação e estudos práticos em redes.

## 🛠 Tecnologias Utilizadas

- 🐳 **Docker** — Containerização e orquestração dos dispositivos de rede simulados.  
- 🐍 **Python** — Automação da geração das configurações de rede.  
- 💻 **Shell Script** — Scripts para testes e validação da conectividade.  
- 🐧 **Linux Networking Tools** — Ferramentas nativas para configuração e diagnóstico das redes simuladas.  

## 📂 Estrutura do Repositório

host/: Scripts e configurações relacionados aos hosts da rede.  
router/: Scripts e configurações para os roteadores( Envio e recebimentos dos pacotes HELLO E SLA, controle e atualização da tabela de roteamento dos roteadores da rede).  
Topologia_rede.png: Grafo ilustrativo da topologia da rede simulada.  
docker-compose.yml: Arquivo para orquestrar os containers Docker.  
gerar_composer.py: Script Python para gerar configurações automaticamente.  
ping.sh: Script para testar conectividade entre roteadores.  
ping_host.sh: Script para testar conectividade com host específico.  
Requerimentos.txt: Lista das dependências necessárias para o projeto.

## 🧩 Componentes Principais

- O sistema utiliza **pacotes Hello**, que permitem a descoberta e manutenção das vizinhanças entre dispositivos na rede simulada.  
- Utiliza **pacotes LSA (Link-State Advertisements)** para atualizar e propagar informações sobre o estado das ligações, garantindo que a topologia da rede esteja sempre atualizada.  
- Mantém uma **tabela de roteamento dinâmica** que reflete as melhores rotas calculadas usando o **(algoritmo de Dijkstra)** em tempo real para o encaminhamento eficiente dos pacotes entre os hosts.  
- O projeto considera aspectos de segurança e privacidade, alinhando-se às diretrizes da **LGPD** para proteção dos dados simulados durante as operações.

## ⚙️ Como Utilizar

1. Clone este repositório:

   ```bash
   git clone https://github.com/EmillySatiro/PROVA1_Redes.git
   cd PROVA1_Redes

2. Crie e ative um ambiente virtual Python (recomendado):
   ```
    python -m venv venv
    source venv/bin/activate       # Linux/macOS
    venv\Scripts\activate          # Windows

3. Instale as dependências:
   ```
   pip install -r Requerimentos.txt
   
4. Inicialize a rede simulada via Docker Compose:
   ```
   docker-compose up --build

5. Para testar a conectividade entre os dispositivos, execute(no terminal):
    ```
    ./ping.sh
    ./ping_host.sh

## Como Contribuir

Contribuições são sempre bem-vindas para aprimorar este projeto. Siga as diretrizes abaixo para colaborar de forma organizada e eficiente:

### 1. Fork do Repositório

- Faça um fork deste repositório para sua conta pessoal.

### 2. Crie uma Branch

- Crie uma branch com um nome descritivo para sua feature ou correção:

  ```bash
  git checkout -b minha-feature

