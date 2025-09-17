import socket
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

HOST = "0.0.0.0"
DEFAULT_PORT = 9009
ENC = "utf-8"
BUFFER_SIZE = 4096

class ClientHandler:
    def __init__(self, sock, addr, nick=None):
        self.sock = sock
        self.addr = addr
        self.nick = nick or f"{addr[0]}:{addr[1]}"
        self.buffer = ""

    def fileno(self):
        return self.sock.fileno()

    def send(self, msg: str):
        try:
            self.sock.sendall((msg + "\n").encode(ENC))
            return True
        except Exception as e:
            return False

    def close(self):
        try:
            self.sock.close()
        except:
            pass

class ServerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Servidor Sockets - Multi-client (TCP)")
        self.geometry("700x450")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.server_socket = None
        self.accept_thread = None
        self.running = False
        self.clients = {} 

        self.queue = queue.Queue()

        self._build_ui()

        self.after(100, self._process_queue)

    def _build_ui(self):
        frame_top = tk.Frame(self)
        frame_top.pack(fill="x", padx=5, pady=5)

        tk.Label(frame_top, text="Porta:").pack(side="left")
        self.port_var = tk.IntVar(value=DEFAULT_PORT)
        self.port_entry = tk.Entry(frame_top, width=8, textvariable=self.port_var)
        self.port_entry.pack(side="left", padx=(0,10))

        self.btn_start = tk.Button(frame_top, text="Iniciar Servidor", command=self.start_server)
        self.btn_start.pack(side="left")

        self.btn_stop = tk.Button(frame_top, text="Parar Servidor", command=self.stop_server, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        self.btn_broadcast = tk.Button(frame_top, text="Broadcast (teste)", command=self.broadcast_test)
        self.btn_broadcast.pack(side="right")

        center = tk.Frame(self)
        center.pack(fill="both", expand=True, padx=5, pady=5)

        left = tk.Frame(center)
        left.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="Logs:").pack(anchor="w")
        self.log_area = scrolledtext.ScrolledText(left, state="disabled", height=20)
        self.log_area.pack(fill="both", expand=True)

        right = tk.Frame(center, width=200)
        right.pack(side="right", fill="y")
        tk.Label(right, text="Clientes conectados:").pack(anchor="w")
        self.clients_listbox = tk.Listbox(right, height=20)
        self.clients_listbox.pack(fill="y", expand=False)

        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=5, pady=5)
        tk.Label(bottom, text="Mensagem para broadcast:").pack(anchor="w")
        self.broadcast_entry = tk.Entry(bottom)
        self.broadcast_entry.pack(fill="x", expand=True, side="left")
        tk.Button(bottom, text="Enviar", command=self.broadcast_from_gui).pack(side="right")

    def log(self, text):
        self.queue.put(("log", text))

    def add_client_gui(self, key, label):
        self.queue.put(("add_client", (key, label)))

    def remove_client_gui(self, key):
        self.queue.put(("remove_client", key))

    def start_server(self):
        if self.running:
            return
        port = int(self.port_var.get())
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((HOST, port))
            self.server_socket.listen(5)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar servidor: {e}")
            return

        self.running = True
        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.log(f"Servidor iniciado em {HOST}:{port}")

    def stop_server(self):
        if not self.running:
            return
        self.running = False
        try:
            self.server_socket.close()
        except:
            pass
        for ch in list(self.clients.values()):
            try:
                ch.send("[SERVER] Servidor encerrando.")
            except:
                pass
            ch.close()
        self.clients.clear()
        self._refresh_clients_listbox()
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.log("Servidor parado.")

    def _accept_loop(self):
        while self.running:
            try:
                client_sock, client_addr = self.server_socket.accept()
                handler = ClientHandler(client_sock, client_addr)
                key = client_sock.fileno()
                self.clients[key] = handler
                self.log(f"Conexão aceita de {client_addr}")
                t = threading.Thread(target=self._client_thread, args=(handler,), daemon=True)
                t.start()
                self.add_client_gui(key, handler.nick)
            except OSError:
                break
            except Exception as e:
                self.log(f"Erro accept: {e}")
                break

    def _client_thread(self, handler: ClientHandler):
        sock = handler.sock
        key = sock.fileno()
        addr = handler.addr
        try:
            while self.running:
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    break
                text = data.decode(ENC, errors="replace")
                handler.buffer += text
                while "\n" in handler.buffer:
                    line, handler.buffer = handler.buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("/nick "):
                        newnick = line[len("/nick "):].strip()
                        old = handler.nick
                        handler.nick = newnick or handler.nick
                        self.log(f"{old} agora é {handler.nick}")
                        self.add_client_gui(key, handler.nick)
                    else:
                        msg = f"{handler.nick}: {line}"
                        self.log(f"Recebido de {handler.nick}: {line}")
                        self._broadcast(msg, exclude_fd=None)
        except ConnectionResetError:
            pass
        except Exception as e:
            self.log(f"Erro no cliente {addr}: {e}")
        finally:
            self.log(f"Cliente {handler.nick} desconectado ({addr})")
            try:
                handler.close()
            except:
                pass
            if key in self.clients:
                del self.clients[key]
            self.remove_client_gui(key)

    def _broadcast(self, message, exclude_fd=None):
        bad = []
        for key, ch in list(self.clients.items()):
            if key == exclude_fd:
                continue
            ok = ch.send(message)
            if not ok:
                bad.append(key)
        for b in bad:
            try:
                self.clients[b].close()
            except:
                pass
            if b in self.clients:
                del self.clients[b]
            self.remove_client_gui(b)

    def broadcast_from_gui(self):
        txt = self.broadcast_entry.get().strip()
        if not txt:
            return
        self._broadcast(f"[SERVER-BROADCAST] {txt}")
        self.log(f"Broadcast enviado: {txt}")
        self.broadcast_entry.delete(0, "end")

    def broadcast_test(self):
        self.broadcast_from_gui()

    def _process_queue(self):
        while not self.queue.empty():
            typ, data = self.queue.get_nowait()
            if typ == "log":
                self.log_area.config(state="normal")
                self.log_area.insert("end", data + "\n")
                self.log_area.see("end")
                self.log_area.config(state="disabled")
            elif typ == "add_client":
                key, label = data
                self._add_client_list(key, label)
            elif typ == "remove_client":
                key = data
                self._remove_client_list(key)
        self.after(100, self._process_queue)

    def _add_client_list(self, key, label):
        for i in range(self.clients_listbox.size()):
            item = self.clients_listbox.get(i)
            if item.startswith(f"{key}:"):
                self.clients_listbox.delete(i)
                break
        self.clients_listbox.insert("end", f"{key}: {label}")

    def _remove_client_list(self, key):
        for i in range(self.clients_listbox.size()):
            item = self.clients_listbox.get(i)
            if item.startswith(f"{key}:"):
                self.clients_listbox.delete(i)
                break

    def _refresh_clients_listbox(self):
        self.clients_listbox.delete(0, "end")
        for key, ch in self.clients.items():
            self.clients_listbox.insert("end", f"{key}: {ch.nick}")

    def on_close(self):
        if self.running:
            if not messagebox.askyesno("Sair", "Servidor está rodando. Parar e sair?"):
                return
        self.stop_server()
        self.destroy()

if __name__ == "__main__":
    app = ServerApp()
    app.mainloop()
