# Runs a simple HTTP website
import http.server
import socketserver
import sys

print("Web Server")

if len(sys.argv) > 1:
    IP = sys.argv[1]
else:
    IP = input("Enter server IP: ")

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer((IP, PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server...")
        httpd.shutdown()