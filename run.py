import socket, subprocess, sys
from pathlib import Path
def free_port(start=8501,end=8599):
    for port in range(start,end+1):
        with socket.socket() as s:
            try: s.bind(("127.0.0.1",port)); return port
            except OSError: pass
    raise RuntimeError("No free local port found.")
root=Path(__file__).resolve().parent
port=free_port()
print(f"RentRelief running at http://localhost:{port}")
subprocess.run([sys.executable,"-m","streamlit","run",str(root/"app.py"),"--server.port",str(port)],check=False)
