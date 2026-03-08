import socketserver

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple HTML</title>
</head>
<body>
    <h1>A HTML sent by socket server</h1>
</body>
</html>
        """
        response = f"HTTP/1.1 200 OK\r\n{html}"
        self.request.sendall(response.encode())
        # após retornarmos, o soquete será fechado.

if __name__ == "__main__":
    HOST, PORT = "localhost", 3000

    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        server.serve_forever()