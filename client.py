import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import queue

ENC = "utf-8"
BUFFER_SIZE = 4096

class ClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cliente Sockets (TCP)")
        self.geometry("600x450")
        self.sock = None
        self.recv_thread = None
        self.running = False
        self.queue = queue.Queue()
        self.buffer = ""

        self._build_ui()
        self.after(100, self._process_queue)

    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=5, pady=5)
        tk.Label(top, text="Servidor IP:").pack(side="left")
        self.ip_var = tk.StringVar(value="172.31.99.172")
        tk.Entry(top, width=14, textvariable=self.ip_var).pack(side="left")
        tk.Label(top, text="Porta:").pack(side="left", padx=(10,0))
        self.port_var = tk.IntVar(value=9009)
        tk.Entry(top, width=6, textvariable=self.port_var).pack(side="left")
        tk.Label(top, text="Nick:").pack(side="left", padx=(10,0))
        self.nick_var = tk.StringVar(value="Aluno")
        tk.Entry(top, width=10, textvariable=self.nick_var).pack(side="left")

        tk.Button(top, text="Conectar", command=self.connect).pack(side="left", padx=5)
        tk.Button(top, text="Desconectar", command=self.disconnect).pack(side="left")

        tk.Label(self, text="Chat:").pack(anchor="w", padx=5)
        self.chat_area = scrolledtext.ScrolledText(self, state="disabled", height=18)
        self.chat_area.pack(fill="both", expand=True, padx=5, pady=5)

        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=5, pady=5)
        self.msg_entry = tk.Entry(bottom)
        self.msg_entry.pack(fill="x", side="left", expand=True)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        tk.Button(bottom, text="Enviar", command=self.send_message).pack(side="right")

    def log(self, text):
        self.queue.put(("log", text))

    def connect(self):
        if self.running:
            return
        ip = self.ip_var.get().strip()
        port = int(self.port_var.get())
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao conectar: {e}")
            return
        self.running = True
        # Send nickname as first message
        nick = self.nick_var.get().strip()
        if nick:
            try:
                self.sock.sendall(f"/nick {nick}\n".encode(ENC))
            except:
                pass
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()
        self.log(f"Conectado a {ip}:{port} como {nick}")

    def disconnect(self):
        if not self.running:
            return
        self.running = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            self.sock.close()
        except:
            pass
        self.log("Desconectado.")
        self.sock = None

    def _recv_loop(self):
        try:
            while self.running:
                data = self.sock.recv(BUFFER_SIZE)
                if not data:
                    break
                text = data.decode(ENC, errors="replace")
                self.buffer += text
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    self.log(line.strip())
        except Exception as e:
            self.log(f"Erro recv: {e}")
        finally:
            if self.running:
                self.log("Conexão perdida.")
            self.running = False

    def send_message(self):
        if not self.running or not self.sock:
            messagebox.showwarning("Aviso", "Não conectado.")
            return
        msg = self.msg_entry.get().strip()
        if not msg:
            return
        try:
            self.sock.sendall((msg + "\n").encode(ENC))
            # Optionally show own message immediately
            self.log(f"Você: {msg}")
            self.msg_entry.delete(0, "end")
        except Exception as e:
            self.log(f"Erro ao enviar: {e}")

    def _process_queue(self):
        while not self.queue.empty():
            typ, data = self.queue.get_nowait()
            if typ == "log":
                self.chat_area.config(state="normal")
                self.chat_area.insert("end", data + "\n")
                self.chat_area.see("end")
                self.chat_area.config(state="disabled")
        self.after(100, self._process_queue)

    def on_close(self):
        self.disconnect()
        self.destroy()

if __name__ == "__main__":
    app = ClientApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
