"""Servidor HTTP do dashboard."""

import functools
import http.server
import json
import signal
import socket
from datetime import datetime

from .config import DASHBOARD, PASTA

def porta_disponivel(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", porta)) != 0


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serve os arquivos da pasta. Dados dinâmicos nunca ficam em cache."""

    def end_headers(self):
        caminho = self.path.split("?", 1)[0]
        if caminho in ("/status.json", "/dashboard/js/repos_analise.csv", "/dashboard/js/dados.js"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()
    def do_GET(self):
        if self.path.startswith("/ping"):
            self._ping()
        else:
            super().do_GET()

    def _ping(self):
        body = json.dumps({
            "servidor": "online",
            "hora": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # silencioso — logs ficam nos arquivos do launchd


def criar_servidor(porta: int):
    porta_original = porta
    while not porta_disponivel(porta):
        print(f"  ⚠️   Porta {porta} em uso — tentando {porta + 1}...", flush=True)
        porta += 1
    handler = functools.partial(Handler, directory=str(PASTA))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", porta), handler)
    httpd.porta_real = porta
    if porta != porta_original:
        print(f"  ℹ️   Usando a porta {porta}.", flush=True)
    print("  🌐  GloboAds Servidor HTTP", flush=True)
    print(f"  📁  Servindo: {PASTA}", flush=True)
    print(f"  🔗  URL: http://localhost:{porta}/{DASHBOARD}", flush=True)
    return httpd


def rodar_servidor(porta: int):
    """Modo --servidor: bloqueia até Ctrl+C / SIGTERM."""
    httpd = criar_servidor(porta)
    def _sigterm(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _sigterm)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  👋  Servidor encerrado.", flush=True)


# ════════════════════════════════════════════════════════════════
#  ANALISADOR DE REPOSITÓRIOS (embutido — ex-analisar_repos.py)
# ════════════════════════════════════════════════════════════════

# ============================================================
# CONFIGURAÇÃO — ajuste se quiser mudar o comportamento padrão
# ============================================================

# Diretórios que nunca são analisados (build, cache, etc.)
