import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12000))
server.listen(5)

while True:
    client_socket, client_addr = server.accept()

    bytes_req = client_socket.recv(1024)
    string_req = bytes_req.decode()
    print(string_req)

    if string_req.startswith("GET"):
        html = """
            <!DOCTYPE html>
            <html>
                <body>
                    <h1>My First Raw Server</h1>
                </body>
            </html>
        """
        response = f"HTTP/1.1 200 OK\r\n{html}"
        client_socket.sendall(response.encode())
