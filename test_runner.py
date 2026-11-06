import subprocess
import socket
import time
import sys
import os

# 1. Structure a completely raw, framework-free native HTTP responder script
mock_code = """
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class MockOllamaHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Drain the request body first so closing the socket can't cause a connection reset
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        
        mock_response = {
            "choices": [{
                "message": {
                    "content": "{\\"summary\\": \\"Mocked summary matching the JD\\", \\"experience\\": [], \\"skills\\": []}"
                }
            }]
        }
        self.wfile.write(json.dumps(mock_response).encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress logging to keep the runner logs pristine
        return

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 11434), MockOllamaHandler)
    server.serve_forever()
"""

with open("mock_server.py", "w") as f:
    f.write(mock_code.strip())

# 2. Spawn the mock server as a strict managed child process
print("Spawning native Mock Ollama API server process...", flush=True)
server_proc = subprocess.Popen([sys.executable, "mock_server.py"])

# 3. Block and poll until the port is definitively open and listening
print("Polling 127.0.0.1:11434 for socket initialization...", flush=True)
connected = False
for i in range(15):
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=1):
            print("Socket interface confirmed active and reachable on port 11434!", flush=True)
            connected = True
            break
    except OSError:
        print(f"Port 11434 not listening yet... ({i+1}/15)", flush=True)
        time.sleep(1)

if not connected:
    print("Error: Mock server socket failed to bind.", flush=True)
    server_proc.terminate()
    sys.exit(1)

# 4. Now that the server is 100% active, run the worker script sequentially
print("Executing worker logic synchronously...", flush=True)
worker_res = subprocess.run([sys.executable, "-m", "app.worker"])

# 5. Clean up and shut down the server process safely
print("Cleaning up mock infrastructure layers...", flush=True)
server_proc.terminate()
server_proc.wait()

# 6. Clean up the temporary file
if os.path.exists("mock_server.py"):
    os.remove("mock_server.py")

# 7. Pass the exit code straight back to GitHub Actions
sys.exit(worker_res.returncode)
