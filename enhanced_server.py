import socket
import threading
import time

SERVER_IP = socket.gethostbyname(socket.gethostname())
PORT = 5050
ADDR = (SERVER_IP, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)
server.listen(5)

conexoes = []
lock = threading.Lock()

print(f"""
╔══════════════════════════════════════════╗
║         LAB SERVER - TCP DEBUG           ║
╠══════════════════════════════════════════╣
║  IP   : {SERVER_IP:<32}║
║  PORT : {PORT:<32}║
╠══════════════════════════════════════════╣
║  Backlog (fila do kernel) : 5            ║
║  Modo  : threading por conexão           ║
╠══════════════════════════════════════════╣
║  COMANDOS NO OUTRO TERMINAL:             ║
║  watch -n 0.5 'ss -tn | grep {PORT}'      ║
║  ss -tn | grep {PORT} | wc -l             ║
╚══════════════════════════════════════════╝
""")

def handle(conn, addr):
    with lock:
        conexoes.append(conn)
        total = len(conexoes)

    print(f"[+] NOVA CONEXÃO  | {addr[0]}:{addr[1]} | total ativo: {total}")

    try:
        # Lê os dados mas não responde nada — conexão fica ESTABLISHED
        # Descomente a linha abaixo para responder HTTP e fechar limpo:
        # conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")

        while True:
            data = conn.recv(1024)
            if not data:
                break  # cliente fechou

    except Exception as e:
        print(f"[!] ERRO          | {addr[0]}:{addr[1]} → {e}")

    finally:
        conn.close()
        with lock:
            conexoes.remove(conn)
            total = len(conexoes)
        print(f"[-] CONEXÃO FECHADA | {addr[0]}:{addr[1]} | total ativo: {total}")


# MODOS DE LAB — descomente para experimentar comportamentos diferentes

# MODO 1 (padrão): threading normal, trata todas as conexões
def start_threading():
    print("[MODO] Threading — cada conexão em sua própria thread\n")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle, args=(conn, addr), daemon=True)
        thread.start()

# MODO 2: sem threading — só aceita 1 conexão, resto fica na fila do kernel
def start_single():
    print("[MODO] Single — sem threading, veja a fila com ss -tn\n")
    while True:
        conn, addr = server.accept()
        handle(conn, addr)  # trava aqui até essa conexão fechar

# MODO 3: aceita mas não lê e não fecha — provoca CLOSE-WAIT
def start_leak():
    print("[MODO] Leak — aceita conexões mas nunca fecha, veja CLOSE-WAIT\n")
    while True:
        conn, addr = server.accept()
        with lock:
            conexoes.append(conn)
            total = len(conexoes)
        print(f"[+] ACEITA (sem fechar) | {addr[0]}:{addr[1]} | total: {total}")
        # não fecha, não lê — conexão fica presa em CLOSE-WAIT quando browser fechar


# ← ESCOLHA O MODO AQUI
# start_threading()
# start_single()
start_leak()