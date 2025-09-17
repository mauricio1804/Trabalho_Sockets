# Trabalho Sockets - Multi-client (TCP) com GUI

Arquivos:
- server.py
- client.py

Requisitos:
- Python 3.8+

Execução:
1. No servidor:
   python server.py
   (escolha a porta, clique em "Iniciar Servidor")

2. No(s) cliente(s):
   python client.py
   - Informe IP do servidor (ex.: 192.168.1.20)
   - Informe porta (ex.: 9009)
   - Informe nick e clique em Conectar

Observações:
- O servidor aceita múltiplos clientes simultâneos.
- Protocol: mensagens separadas por `\n`. Primeiro envio do cliente pode ser `/nick <nome>`.
- Para rodar em máquinas diferentes, abra a porta no firewall do servidor e, se necessário, configure port forwarding no roteador.

Explicação técnica e mapa para apresentação estão no arquivo do trabalho.

Referências:
- Aula Sockets (Profa. Gisane A. Michelon). :contentReference[oaicite:6]{index=6}
