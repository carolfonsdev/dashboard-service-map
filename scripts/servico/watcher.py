"""Monitoramento dos repositórios e atualização dos dados."""

import csv
import hashlib
import json
import os
import signal
import sys
import threading
import tempfile
import time
from datetime import datetime
from pathlib import Path

from .analyzer import COLUNAS, analisar_repo, descobrir_repos, gerar_dados_js
from .common import erro, log_ts
from .config import DEBOUNCE, IGNORAR, PASTA, STATUS
from .server import criar_servidor


# ════════════════════════════════════════════════════════════════
#  WATCHER  (ex-watcher_servidor.py)
# ════════════════════════════════════════════════════════════════

estado = {
    "status": "iniciando",
    "total_repos": 0,
    "runs": 0,
    "ultima_atualizacao": None,
}
INTERVALO = 30
_STATUS_LOCK = threading.Lock()


def escrever_status(watcher="online"):
    """Escrita atômica: nunca deixa um status.json pela metade."""
    dados = {
        **estado,
        "watcher": watcher,
        "heartbeat": int(time.time()),  # o dashboard detecta watcher morto por aqui
        "intervalo": INTERVALO,
    }
    try:
        # O heartbeat e a análise podem chamar escrever_status() ao mesmo tempo.
        # Um único status.tmp compartilhado causava corrida: uma thread podia
        # substituir/remover o temporário enquanto a outra ainda tentava usá-lo.
        # Cada escrita usa um temporário exclusivo e o lock mantém a troca atômica.
        conteudo = json.dumps(dados, ensure_ascii=False)
        with _STATUS_LOCK:
            STATUS.parent.mkdir(parents=True, exist_ok=True)
            fd, nome_tmp = tempfile.mkstemp(
                prefix=f".{STATUS.name}.", suffix=".tmp", dir=STATUS.parent
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
                    arquivo.write(conteudo)
                    arquivo.flush()
                    os.fsync(arquivo.fileno())
                os.replace(nome_tmp, STATUS)
            finally:
                try:
                    os.unlink(nome_tmp)
                except FileNotFoundError:
                    pass
    except OSError as e:
        log_ts(f"Aviso: não consegui escrever status.json: {e}")


def fingerprint(base: Path) -> str:
    partes = []
    for raiz, dirs, arquivos in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in IGNORAR)
        # Inclui diretórios para detectar criação/remoção mesmo quando a
        # pasta ainda está vazia ou contém somente arquivos ignorados.
        for nome in dirs:
            p = Path(raiz) / nome
            try:
                partes.append(f"d:{p.relative_to(base)}:{p.stat().st_mtime_ns}")
            except OSError:
                pass
        for nome in sorted(arquivos):
            p = Path(raiz) / nome
            try:
                st = p.stat()
                # O analisador lê README, Dockerfile e outros arquivos sem
                # extensão de código; qualquer inclusão/remoção também deve
                # atualizar o snapshot.
                partes.append(f"f:{p.relative_to(base)}:{st.st_size}:{st.st_mtime_ns}")
            except OSError:
                pass
    return hashlib.md5("\n".join(partes).encode()).hexdigest()


def analisar_repos_embutido(base: Path, args) -> tuple:
    """Analisa os repositórios usando a lógica embutida neste arquivo."""
    excludes = set(args.exclude)
    includes = args.include
    repos = descobrir_repos(base, args.depth, includes, excludes)

    if not repos:
        log_ts("Nenhum repositório encontrado.")
        return 0, True

    log_ts(f"Encontrei {len(repos)} repositório(s). Analisando...")
    resultados = []
    for i, repo in enumerate(repos, 1):
        print(f"[{i:>3}/{len(repos)}]  {repo.name}", flush=True)
        resultados.append(analisar_repo(repo))

    saida = Path(args.output).expanduser()
    if not saida.is_absolute():
        saida = PASTA / saida
    saida.parent.mkdir(parents=True, exist_ok=True)

    fd, nome_tmp = tempfile.mkstemp(
        prefix=f".{saida.name}.", suffix=".tmp", dir=saida.parent
    )
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUNAS)
            writer.writeheader()
            writer.writerows(resultados)
            f.flush()
            os.fsync(f.fileno())
        os.replace(nome_tmp, saida)
    finally:
        try:
            os.unlink(nome_tmp)
        except FileNotFoundError:
            pass

    gerar_dados_js(resultados, PASTA / "dashboard" / "js")
    return len(resultados), True


def analisar(base: Path, args) -> bool:
    estado["status"] = "analisando"
    escrever_status()
    log_ts("Analisando...")
    inicio = time.time()

    try:
        total, sucesso = analisar_repos_embutido(base, args)
    except Exception as e:
        estado["status"] = "erro"
        escrever_status()
        log_ts(f"Erro na análise: {type(e).__name__}: {e}")
        return False

    if not sucesso:
        estado["status"] = "erro"
        escrever_status()
        return False

    estado["total_repos"] = total
    estado["runs"] += 1
    estado["status"] = "ok"
    estado["ultima_atualizacao"] = datetime.now().strftime("%d/%m/%Y às %H:%M")
    escrever_status()
    log_ts(f"OK em {time.time() - inicio:.1f}s — {total} repos")
    return True


def encerrar_watcher(*_):
    escrever_status("offline")
    log_ts("Watcher encerrado. Último snapshot mantido.")
    sys.exit(0)


def _heartbeat_loop():
    """Mantém o heartbeat vivo mesmo durante fingerprint/análises demoradas."""
    while True:
        time.sleep(min(max(INTERVALO // 2, 5), 15))
        if estado.get("status") != "encerrando":
            escrever_status()


def rodar_watcher(base: Path, intervalo: int, args):
    """Modo --watcher: loop infinito (precisa rodar na thread principal)."""
    global INTERVALO
    INTERVALO = intervalo

    signal.signal(signal.SIGTERM, encerrar_watcher)
    signal.signal(signal.SIGINT, encerrar_watcher)

    # O fingerprint pode percorrer milhares de arquivos. O heartbeat não pode
    # depender dele, senão o dashboard interpreta uma varredura longa como
    # queda do watcher.
    threading.Thread(target=_heartbeat_loop, daemon=True, name="heartbeat").start()

    log_ts(f"Monitorando {base} a cada {intervalo}s")
    atual = fingerprint(base)
    analisar(base, args)
    ultimo = time.time()

    while True:
        time.sleep(intervalo)
        novo = fingerprint(base)
        if novo == atual or time.time() - ultimo < DEBOUNCE:
            continue
        atual = novo
        ultimo = time.time()
        log_ts("Mudança detectada")
        analisar(base, args)


def resolver_pasta(args) -> Path:
    pasta = args.pasta
    if not pasta:
        print("  Qual é a pasta dos seus repositórios?")
        print("  Exemplo: ~/Documents/Repos/back\n")
        pasta = input("  📁  Pasta: ").strip()
        if not pasta:
            erro("Pasta não informada.")
    p = Path(pasta).expanduser().resolve()
    if not p.is_dir():
        erro(f"Pasta de repos não encontrada:\n       {p}")
    return p


# ════════════════════════════════════════════════════════════════
#  MODO ÚNICO: servidor + watcher no mesmo processo (--rodar)
# ════════════════════════════════════════════════════════════════

def rodar_tudo(args):
    base = resolver_pasta(args)
    httpd = criar_servidor(args.port)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    rodar_watcher(base, args.interval, args)


# ════════════════════════════════════════════════════════════════
#  INSTALADOR launchd  (Mac)
