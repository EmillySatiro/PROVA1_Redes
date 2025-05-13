FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
  iproute2 \
  iputils-ping \
  net-tools \
  nano \
  curl \
  traceroute \
  && rm -rf /var/lib/apt/lists/*

COPY host.sh /host.sh 

RUN chmod +x /host.sh

CMD ["/host.sh"]
