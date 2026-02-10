import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class SingleFileHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            with open("./client.html", 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(404)

if __name__ == '__main__':
    print("🌐 Client server running")
    HTTPServer(('', 8080), SingleFileHandler).serve_forever()