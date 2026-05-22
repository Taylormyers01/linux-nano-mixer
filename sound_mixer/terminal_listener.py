import socketserver

class LogTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            self.data = self.request.recv(1024).strip()
            if not self.data:
                break
            print(self.data.decode('utf-8'))

def start_listener():
    HOST, PORT = "localhost", 9999
    with socketserver.TCPServer((HOST, PORT), LogTCPHandler) as server:
        print("--- Log Terminal Active ---")
        server.serve_forever()

if __name__ == "__main__":
    start_listener()