import subprocess
import socket
import time
import sys
import os

# 1. Write the isolated mock API server code cleanly to a local file
mock_code = """
from fastapi import FastAPI
import uvicorn
app = FastAPI()
@app.post("/v1/chat/completions")
def mock_completions(payload: dict = None):
    return {
        "choices": [{
            "message": {
                "content": "{\\"summary\\": \\"Mocked summary matching the JD\\", \\"experience\\": [], \\"skills\\": []}"
            }
        }]
    }
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=11434)
"""

with open("mock_server.py", "w") as f:
    f.write(mock_code.strip())

# 2. Spawn the mock server as a strict managed child process
print("Spawning managed Mock Ollama API process...", flush=True)
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
